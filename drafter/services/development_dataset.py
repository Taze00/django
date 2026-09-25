"""Versioned Train + new development membership; no historical holdout query."""
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path

from django.db.models import Prefetch
from django.utils import timezone
from drafter.models import Match,RawPayload
from drafter.services.v2_future_window import OLD_END,digest
from drafter.services.development_collection import SAMPLING,development_eligible
from drafter.services.evaluation import examples_from_queryset
from drafter.services.v2_challenger_training import example_digest,TRAIN_DIGEST
from drafter.services.evaluation_lifecycle import aborted_protocols

V2_HASH='92e0b427bf9abce62e047419ea1008f740c9ee7b39b1458ae15692402b7cf52d'


def new_development_inventory(now=None):
    now=now or timezone.now()
    cutoff=max(OLD_END,now-timedelta(days=30))
    raw=RawPayload.objects.only('content_hash','source','sampling','format','fetched_at','collector_run_id').select_related('collector_run')
    qs=Match.objects.filter(source='api',battle_type='soloRanked',played_at__gt=cutoff,
        played_at__lte=now).prefetch_related('players',Prefetch('payloads',queryset=raw)).order_by('played_at','fingerprint')
    members=[];excluded=Counter();coverage={key:Counter() for key in ('map','mode','date','import_patch')}
    seen=set(); aborted=aborted_protocols()
    for match in qs.iterator(chunk_size=500):
        if not development_eligible(match,now):
            excluded['incomplete_conflicting_unknown_context_or_duplicate_brawlers']+=1;continue
        if any(p.collector_run_id and p.collector_run.parameters.get('purpose')=='prospective_test'
               and p.collector_run.parameters.get('protocol_sha256') not in aborted for p in match.payloads.all()):
            excluded['protected_final_test_origin']+=1;continue
        origins=[]
        for p in match.payloads.all():
            params=p.collector_run.parameters if p.collector_run_id else {}
            allowed=(p.sampling in ('observed_discovery_pilot_v1',SAMPLING)
                     or (p.sampling=='prospective_discovery_v1' and params.get('protocol_sha256') in aborted))
            if (allowed and p.source=='api' and p.format=='brawlstars.battlelog.raw'
                and p.collector_run_id and match.played_at<=p.fetched_at<=now):
                origins.append({'raw_sha256':p.content_hash,'run_id':p.collector_run_id,'sampling':p.sampling})
        if not origins:
            excluded['unverified_or_non_development_origin']+=1;continue
        key=match.reconstructed_fingerprint
        if not key or key in seen:
            raise ValueError('Missing/duplicate reconstructed development identity; fail closed')
        seen.add(key)
        players=list(match.players.all())
        content={'fingerprint':match.fingerprint,'played_at':match.played_at.isoformat(),
            'mode':match.mode_name,'map_name':match.map_name,
            'team_a':sorted(p.brawler_id for p in players if p.side=='a'),
            'team_b':sorted(p.brawler_id for p in players if p.side=='b'),
            'label':int(match.winner_side=='a')}
        members.append({'fingerprint':match.fingerprint,'played_at':content['played_at'],
            'content_sha256':digest(content),'origins':sorted(origins,key=lambda o:o['raw_sha256'])})
        for key,value in (('map',match.map_name),('mode',match.mode_name),
                          ('date',str(match.played_at.date())),('import_patch',str(match.patch_id))):
            coverage[key][value or 'UNKNOWN']+=1
    return members,{'eligible_new_current_soloRanked':len(members),'excluded':dict(excluded),
        'coverage':{key:dict(value) for key,value in coverage.items()},'actual_game_patch':'UNKNOWN',
        'new_membership_sha256':digest(members),'after_exclusive':cutoff.isoformat(),
        'selection_bias':'Ranked-activity-prioritized graph, repeated players; no independence or sampling weights',
        'final_test_eligible':False}


def versioned_development_dataset(now=None):
    now=now or timezone.now()
    artifact=Path('data/brawl_reports/v2_challenger.json').read_bytes()
    if hashlib.sha256(artifact).hexdigest()!=V2_HASH:
        raise ValueError('Pinned original Train artifact changed')
    original=json.loads(artifact)['provenance']['train']
    keys=original['fingerprints']
    if len(keys)!=6094 or len(set(keys))!=6094:
        raise ValueError('Original Train membership invalid')
    # Deliberately do NOT call development_partitions(), which scans the old freeze.
    train,skipped=examples_from_queryset(Match.objects.filter(fingerprint__in=keys))
    if skipped or len(train)!=6094 or example_digest(train)!=TRAIN_DIGEST:
        raise ValueError('Original Train content no longer matches pinned artifact')
    new,report=new_development_inventory(now)
    if set(keys)&{r['fingerprint'] for r in new}:
        raise ValueError('Original and new development memberships overlap')
    manifest={'schema':'ranked-development-dataset-1','created_at':now.isoformat(),
        'original_train':{'fingerprints':keys,'n':6094,'content_sha256':TRAIN_DIGEST},
        'new_development':new,'report':report,'old_validation':'not included in this dataset version',
        'historical_holdout':'permanently_closed_not_selected','future_final_test_eligible':False,
        'training_started':False}
    manifest['dataset_sha256']=digest({'original_train':manifest['original_train'],'new_development':new})
    return manifest


def chronological_plan(manifest):
    # Entire UTC days stay together; no random splitting or timestamp ties crossing.
    days=sorted({r['played_at'][:10] for r in manifest['new_development']})
    if len(days)<2:
        return {'status':'INSUFFICIENT_TEMPORAL_COVERAGE'}
    boundary=days[-1]
    older=[r['fingerprint'] for r in manifest['new_development'] if r['played_at'][:10]<boundary]
    newer=[r['fingerprint'] for r in manifest['new_development'] if r['played_at'][:10]==boundary]
    ready=len(manifest['new_development'])>=1000 and len(older)>=500 and len(newer)>=200
    return {'status':'READY_FOR_PREREGISTERED_DEVELOPMENT_VALIDATION' if ready else 'INSUFFICIENT_DATA',
        'validation_utc_day':boundary,'new_train_n':len(older),'new_validation_n':len(newer),
        'train_fingerprints':manifest['original_train']['fingerprints']+older,
        'validation_fingerprints':newer,'final_test':False}
