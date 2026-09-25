"""Synthetic data only: persistent bounded development cycles and dataset safety."""
from datetime import timedelta
from unittest.mock import patch
from django.db import connection
from django.test.utils import CaptureQueriesContext
from drafter.tests.basis import DrafterTest
from drafter.tests import test_tagged_frontier as fixtures
from drafter.models import Match,RawPayload,CollectorRun,TrackedPlayer
from drafter.models.discovery import DiscoveryPlayer
from drafter.services.discovery_frontier import DiscoveryFrontierCollector
from drafter.services.development_collection import DevelopmentCollector,SAMPLING
from drafter.services.development_dataset import new_development_inventory,chronological_plan
from drafter.services.brawl_api_client import BrawlApiClient,pfad_battlelog
from drafter.tests.test_api_client import _http_fehler,_Antwort


class DevelopmentCollectionTests(DrafterTest):
    battle=fixtures.TaggedFrontierTest.battle
    api=fixtures.TaggedFrontierTest.api
    collect=fixtures.TaggedFrontierTest.collect

    def seed(self,ranked=False):
        entries=[self.battle('ranked')]
        if ranked:
            entries.append(self.battle(tags=[fixtures.SEED,'#Z1','#Z2','#Z3','#Z4','#Z5'],time='20260923T110100.000Z'))
        self.collect(self.api(entries=entries))
        raw=RawPayload.objects.get(format='brawlstars.battlelog.raw')
        DiscoveryFrontierCollector(after=fixtures.CUTOFF,source_payloads=[{'id':raw.pk,'content_hash':raw.content_hash}],
            pilot_id='synthetic-dev-bootstrap',protocol_hash='a'*64,max_battlelogs=0,client=self.api(),now=lambda:fixtures.NOW).execute()

    def dev(self,client=None,**kwargs):
        kwargs.setdefault('max_battlelogs',1)
        return DevelopmentCollector(client=client or self.api(),now=lambda:fixtures.NOW,**kwargs).execute()

    def test_ranked_activity_priority_and_trophy_raw_only(self):
        self.seed(ranked=True)
        before=Match.objects.count()
        client=self.api()
        client.antworten[pfad_battlelog('#Z1')]={'items':[self.battle('ranked',time='20260923T120000.000Z')]}
        report=self.dev(client)
        self.assertEqual(client.aufrufe,[pfad_battlelog('#Z1')])
        self.assertEqual(Match.objects.count(),before)
        self.assertEqual(report['raw_battle_types'],{'ranked':1})
        self.assertFalse(report['future_test_eligible'])
        self.assertEqual(report['purpose'],'development')
        self.assertEqual(RawPayload.objects.filter(sampling=SAMPLING).count(),1)

    def test_cycles_resume_without_resetting_player_cooldown(self):
        self.seed()
        self.dev()
        p=TrackedPlayer.objects.get(tag='#P1');before=(p.last_fetched_at,p.next_fetch_after)
        client=self.api();self.dev(client)
        p.refresh_from_db()
        self.assertEqual((p.last_fetched_at,p.next_fetch_after),before)
        self.assertEqual(client.aufrufe,[pfad_battlelog('#P2')])
        self.assertEqual(CollectorRun.objects.filter(parameters__strategie=SAMPLING).count(),2)

    def test_new_ranked_dataset_restricts_sql_and_excludes_old_trophy_and_future(self):
        self.seed()
        client=self.api();client.antworten[pfad_battlelog('#P1')]={'items':[self.battle(time='20260923T120000.000Z')]}
        report=self.dev(client)
        self.assertEqual(report['new_eligible_solo_ranked_matches'],1)
        with CaptureQueriesContext(connection) as sql:
            members,coverage=new_development_inventory(fixtures.NOW)
        self.assertEqual(len(members),1)
        self.assertEqual(coverage['eligible_new_current_soloRanked'],1)
        self.assertIn('2026-09-18',sql[0]['sql'])
        self.assertIn('soloRanked',sql[0]['sql'])
        self.assertFalse(coverage['final_test_eligible'])
        self.assertTrue(all(o['sampling']==SAMPLING for o in members[0]['origins']))

    def test_429_even_followed_by_success_stops_and_persists_global_pause(self):
        self.seed();calls=[]
        def response(request,timeout=None):
            calls.append(request.full_url)
            if len(calls)==1:raise _http_fehler(429,{})
            return _Antwort({'items':[]})
        client=BrawlApiClient(api_key='synthetic',oeffner=response,schlafen=lambda _:None,mindestabstand=0)
        report=self.dev(client,max_battlelogs=50)
        self.assertEqual(report['battlelog_attempts'],2)
        self.assertFalse(report['next_cycle_allowed'])
        with self.assertRaisesRegex(ValueError,'API_BACKOFF'):self.dev()

    def test_crash_retains_raw_and_recovers_without_refetch_or_clock_change(self):
        self.seed()
        client=self.api();client.antworten[pfad_battlelog('#P1')]={'items':[self.battle(time='20260923T120000.000Z')]}
        with patch('drafter.services.tagged_frontier.parse_offizieller_battlelog',side_effect=RuntimeError('synthetic crash')):
            with self.assertRaises(RuntimeError):self.dev(client)
        raw=RawPayload.objects.get(sampling=SAMPLING)
        self.assertEqual(raw.parse_status,'unsupported')
        p=TrackedPlayer.objects.get(tag='#P1');before=(p.last_fetched_at,p.next_fetch_after,p.fetch_count)
        # Processing errors intentionally stop; this synthetic test advances the
        # injected clock beyond the error pause, never real collection clocks.
        later=fixtures.NOW+timedelta(hours=6)
        report=DevelopmentCollector(client=self.api(),now=lambda:later,max_battlelogs=0).execute()
        raw.refresh_from_db();p.refresh_from_db()
        self.assertEqual(raw.parse_status,'parsed')
        self.assertEqual((p.last_fetched_at,p.next_fetch_after,p.fetch_count),before)
        self.assertEqual(report['recovered_raw']['new_matches'],1)
        self.assertEqual(report['ranked_evidence_matches'],1)
        self.assertEqual(report['battlelog_attempts'],0)

    def test_chronological_day_groups_never_randomly_mix(self):
        manifest={'original_train':{'fingerprints':['original']},'new_development':[
            {'fingerprint':str(i),'played_at':'2026-09-24T23:00:00Z' if i<600 else '2026-09-25T01:00:00Z'} for i in range(1100)]}
        plan=chronological_plan(manifest)
        self.assertEqual(plan['new_train_n'],600)
        self.assertEqual(plan['new_validation_n'],500)
        self.assertFalse(set(plan['train_fingerprints'])&set(plan['validation_fingerprints']))
        self.assertFalse(plan['final_test'])

    def test_active_final_test_origin_cannot_be_laundered_into_development(self):
        self.seed()
        client=self.api();client.antworten[pfad_battlelog('#P1')]={'items':[self.battle(time='20260923T120000.000Z')]}
        self.dev(client)
        raw=RawPayload.objects.get(sampling=SAMPLING)
        run=raw.collector_run
        run.parameters['purpose']='prospective_test';run.parameters['protocol_sha256']='future-protected'
        run.save(update_fields=['parameters'])
        members,report=new_development_inventory(fixtures.NOW)
        self.assertEqual(members,[])
        self.assertEqual(report['excluded']['protected_final_test_origin'],1)

    def test_fifty_attempt_bound_cannot_be_exceeded(self):
        with self.assertRaises(ValueError):DevelopmentCollector(max_battlelogs=51)
