"""Resumable bounded Ranked development collection. No model fitting or scoring."""
from collections import Counter
from datetime import timedelta

from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.db.models import Exists, OuterRef, F

from drafter.models import CollectorRun, Match, RawPayload
from drafter.models.discovery import DiscoveryPlayer, DiscoveryObservation
from drafter.services.discovery_frontier import DiscoveryFrontierCollector
from drafter.services.tagged_frontier import TaggedFrontierCollector, COOLDOWN, eligible, beobachteter_tag
from drafter.services.v2_future_window import OLD_END
from drafter.services.ingest.parser import parse_offizieller_battlelog, FORMAT_OFFIZIELLER_BATTLELOG
from drafter.services.ingest.importer import MatchImporter
from drafter.services.collector import _EineLieferung
from drafter.services.providers.records import Lieferung

SAMPLING = 'ranked_development_v1'
POLICY = {'version':SAMPLING, 'cycle_http_cap':50,'max_depth':1,'cooldown_hours':6,
    'exploration_every_queries':5,'priority':'direct_observed_soloRanked_activity',
    'current_age_days':30,'rankings':0,'quota':'UNKNOWN','future_final_test_eligible':False}


def development_eligible(match, now):
    players=list(match.players.all())
    return (eligible(match) and match.brawl_map_id is not None and match.game_mode_id is not None
        and len({p.brawler_id for p in players})==6 and OLD_END < match.played_at <= now)


class DevelopmentCollector(DiscoveryFrontierCollector):
    sampling = SAMPLING
    budget_limit = 50

    def __init__(self, *, max_battlelogs=50, client=None, now=None, code_revision='UNKNOWN'):
        from django.utils import timezone
        clock=now or timezone.now
        TaggedFrontierCollector.__init__(self, after=max(OLD_END,clock()-timedelta(days=30)),
            max_battlelogs=max_battlelogs,max_depth=1,client=client,now=clock,code_revision=code_revision)
        self.raw_types,self.bootstrap_types=Counter(),Counter()
        self.seen_response_tags,self.bootstrap_tags=set(),set()
        self.recovered=Counter()

    def _execute(self):
        # Shared advisory lock is already held. A quota/error pause is global,
        # so changing targets or starting another cycle cannot bypass it.
        recent=CollectorRun.objects.filter(parameters__strategie=SAMPLING,report__api_backoff_required=True)
        if self.max_battlelogs and any(parse_datetime(r.report['api_backoff_until'])>self.now() for r in recent):
            raise ValueError('API_BACKOFF: development collection is paused for six hours')
        for run in CollectorRun.objects.filter(parameters__strategie=SAMPLING,status='running'):
            run.status='aborted';run.abort_reason='INTERRUPTED: retained raw/checkpoints; next cycle recovers pending raw'
            run.finished_at=self.now();run.save(update_fields=['status','abort_reason','finished_at'])
        return TaggedFrontierCollector._execute(self)

    def _prepare_frontier(self):
        self.run.parameters.update(purpose='development',future_test_eligible=False,policy=POLICY)
        self.run.save(update_fields=['parameters'])
        self.metrics['query_eligible_tags_available']=DiscoveryPlayer.objects.count()
        self.metrics['query_eligible_tags_due']=self._due().filter(discovery_frontier__isnull=False).count()
        self.depths=dict.fromkeys(DiscoveryPlayer.objects.values_list('player_id',flat=True),0)
        # At most the previous cycle's 50 pending responses; original raw run,
        # fetch clocks and player cooldowns are never rewritten during recovery.
        for raw in RawPayload.objects.filter(sampling=SAMPLING,
                parse_status=RawPayload.ParseStatus.UNSUPPORTED).order_by('id')[:50]:
            self._recover(raw)

    def _importable_records(self, records):
        return [r for r in records if r.battle_type=='soloRanked' and r.ranked]

    def _claim(self, queried):
        if self.client.statistik.status.get(429,0):
            return None
        ranked=DiscoveryObservation.objects.filter(player__player_id=OuterRef('pk'),
            source__in=('solo_ranked','soloRanked_battlelog'))
        allowed=[pk for pk,depth in self.depths.items() if depth<=1]
        with transaction.atomic():
            due=self._due().filter(pk__in=allowed).exclude(pk__in=queried).annotate(
                ranked_activity=Exists(ranked))
            exploration=(len(queried)+1)%5==0
            pool=due.filter(ranked_activity=False) if exploration else due
            if exploration and not pool.exists():
                pool=due
            player=pool.order_by('-ranked_activity',F('last_fetched_at').asc(nulls_first=True),
                'discovery_frontier__first_seen','tag').select_for_update(of=('self',),skip_locked=True).first()
            if player:
                player.next_fetch_after=self.now()+COOLDOWN
                player.save(update_fields=['next_fetch_after','updated_at'])
            return player

    def _request(self,path,kind,remaining):
        try:
            return super()._request(path,kind,remaining)
        finally:
            stats=self.client.statistik
            pause=any(stats.status.get(s,0) for s in (401,403,429))
            self.run.report.update(api=stats.als_dict(),battlelog_attempts=self.metrics['battlelog_attempts'],
                api_backoff_required=pause,api_backoff_until=(self.now()+COOLDOWN).isoformat() if pause else None)
            self.run.save(update_fields=['report'])

    def _battlelog(self, player, answer):
        # Commit raw independently BEFORE parsing. The processing transaction
        # avoids thousands of per-tag fsyncs, while a crash leaves replayable raw.
        self._raw(answer,player.tag,FORMAT_OFFIZIELLER_BATTLELOG)
        with transaction.atomic():
            super()._battlelog(player,answer)
        self.metrics['new_eligible_solo_ranked_matches']=sum(development_eligible(m,self.now())
            for m in Match.objects.filter(pk__in=self.new_match_ids).prefetch_related('players'))
        self.run.report={**self.run.report,**self.summary.als_dict(),**self.metrics,'api':self.client.statistik.als_dict(),
                         'checkpoint':'response_processed','raw_payloads_persisted':RawPayload.objects.filter(collector_run=self.run).count()}
        self.run.save(update_fields=['report'])

    def _recover(self, raw):
        self._validate_payload(raw)
        parsed=parse_offizieller_battlelog(raw.payload)
        records=self._importable_records([r for r in parsed.matches if self.after<r.played_at<=raw.fetched_at])
        delivery=Lieferung(referenz=raw.reference,format=raw.format,rohdaten=raw.payload,
            source=raw.source,matches=records,sampling=raw.sampling,collector_run_id=raw.collector_run_id)
        importer=MatchImporter(_EineLieferung(delivery))
        delivery.matches=[r for r in records if (importer.finde_importierte_partie(r) is None
            or importer.finde_importierte_partie(r).played_at>self.after)]
        with transaction.atomic():
            imported=importer.ausfuehren()
            parent=DiscoveryPlayer.objects.select_related('player').get(player__tag=raw.reference)
            self._discover(raw,parent)
            for index,item in enumerate(raw.payload['antwort']['items']):
                single={**raw.payload,'antwort':{'items':[item]}}
                for record in parse_offizieller_battlelog(single).matches:
                    if record.battle_type!='soloRanked' or not self.after<record.played_at<=raw.fetched_at:
                        continue
                    match=importer.finde_importierte_partie(record)
                    if match is None or not development_eligible(match,self.now()) or not match.payloads.filter(pk=raw.pk).exists():
                        continue
                    for ti,team in enumerate(item['battle']['teams']):
                        for pi,observed in enumerate(team):
                            tag=beobachteter_tag(observed.get('tag'))
                            if tag:
                                self._observe(tag,'solo_ranked',raw,
                                    f'/antwort/items/{index}/battle/teams/{ti}/{pi}/tag',parent=parent,match=match)
            raw.parse_status=RawPayload.ParseStatus.ERROR if imported.fehlerhaft else RawPayload.ParseStatus.PARSED
            raw.parse_message='Recovered from retained official raw without a new HTTP request'
            raw.save(update_fields=['parse_status','parse_message'])
        self.recovered['payloads']+=1
        self.recovered['new_matches']+=imported.neu
        self.recovered['errors']+=imported.fehlerhaft
        if imported.fehlerhaft:
            raise ValueError('Retained payload recovery failed; inspect raw without refetching')

    def _extra_report(self):
        report=super()._extra_report()
        count=sum(development_eligible(m,self.now()) for m in Match.objects.filter(
            pk__in=self.new_match_ids).prefetch_related('players'))
        statuses=self.client.statistik.status
        backoff=bool(statuses.get(429,0) or self.summary.abbruch.startswith('API_'))
        report.update(purpose='development',future_test_eligible=False,
            new_eligible_solo_ranked_matches=count,
            soloRanked_yield_per_http_attempt=(count/self.metrics['battlelog_attempts'] if self.metrics['battlelog_attempts'] else None),
            api_backoff_required=backoff,api_backoff_until=(self.now()+COOLDOWN).isoformat() if backoff else None,recovered_raw=dict(self.recovered),quota='UNKNOWN',
            next_cycle_allowed=not backoff and not self.summary.konflikte,
            model_fitting_performed=False)
        return report
