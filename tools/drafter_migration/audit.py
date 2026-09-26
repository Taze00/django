"""Run via manage.py shell. Read-only source/target handoff verification; no HTTP."""
import hashlib
import json
import os
from pathlib import Path
from datetime import timedelta
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drafter.models import CollectorRun, Match, TrackedPlayer
from drafter.models.discovery import DiscoveryPlayer
from drafter.services.development_dataset import new_development_inventory, V2_HASH
from drafter.services.evaluation import examples_from_queryset
from drafter.services.v2_challenger_training import example_digest, TRAIN_DIGEST
from drafter.services.anfrage import context_aus_daten
from drafter.services.v2_challenger import recommend
from drafter.services.v2_legacy_comparison import compare


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()


def normalized(value):
    if isinstance(value,dict):return {k:normalized(v) for k,v in value.items() if k!='elapsed_ms'}
    if isinstance(value,(tuple,list)):return [normalized(v) for v in value]
    if isinstance(value,float):return round(value,12)
    return value


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


checkpoint_path='data/brawl_reports/development-20260925-007-session-checkpoint.json'
checkpoint=json.loads(Path(checkpoint_path).read_text())
artifacts=json.loads(Path('docs/drafter-v2/DEVELOPMENT_EXPERIMENT_001_ARTIFACTS.json').read_text())
legacy=json.loads(Path('docs/drafter-v2/LEGACY_BUNDLE_ARTIFACTS.json').read_text())['artifacts'][1]
artifacts[legacy['path']]=legacy['file_sha256']
for path,expected in artifacts.items():
    if file_hash(path)!=expected:raise ValueError('Frozen artifact hash mismatch: '+path)
assert file_hash('data/brawl_reports/v2_challenger.json')==V2_HASH
with transaction.atomic():
    with connection.cursor() as c:
        c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        names=[r[0] for r in c.fetchall()]
        counts={}
        for name in names:
            c.execute('SELECT count(*) FROM '+connection.ops.quote_name(name));counts[name]=c.fetchone()[0]
        # Only framework metadata and Drafter data may cross to the new host.
        metadata={'auth_permission','django_content_type','django_migrations'}
        excluded=[n for n in names if not n.startswith('drafter_') and n not in metadata]
        allowed_seed={'fitness_exercise':3,'fitness_progression':21}
        for name in excluded:
            if counts[name] and counts[name]!=allowed_seed.get(name):
                raise ValueError('Non-Drafter data present; refuse package: '+name)
        if CollectorRun.objects.filter(status='running').exists():raise ValueError('Collector still running')
        table_hashes={}
        for name in names:
            if name.startswith(('drafter_discovery','drafter_tracked','drafter_tagged')) or name in (
                'drafter_collectorrun','drafter_brawler','drafter_brawlmap','drafter_gamemode','drafter_patch',
                'django_migrations','drafter_praxisfall','drafter_userbrawlerpreference'):
                h=hashlib.sha256()
                c.execute('SELECT row_to_json(t)::text FROM '+connection.ops.quote_name(name)+' t ORDER BY id')
                for row in c:
                    h.update(json.dumps(json.loads(row[0]),sort_keys=True,separators=(',',':')).encode()+b'\n')
                table_hashes[name]=h.hexdigest()
    # Verify ONLY explicitly pinned original Train and development members.
    # Never call historical split/holdout evaluation functions.
    train,skipped=examples_from_queryset(Match.objects.filter(fingerprint__in=checkpoint['original_train']['fingerprints']))
    assert not skipped and len(train)==6094 and example_digest(train)==TRAIN_DIGEST
    members,report=new_development_inventory(parse_datetime(checkpoint['created_at']))
    assert members==checkpoint['new_development'], 'Checkpoint membership/content/provenance differs'
    assert digest({'original_train':checkpoint['original_train'],'new_development':members})==checkpoint['dataset_sha256']
    contexts=[
        {'map':'hideout','own_picks':['mortis','gene'],'enemy_picks':['piper','amber','pearl'],'own_team_first_pick':False,'bans':[]},
        {'map':'hideout','own_picks':['mortis','gene'],'enemy_picks':['piper','amber'],'own_team_first_pick':True,'bans':[]},
        {'map':'hideout','own_picks':[],'enemy_picks':[],'own_team_first_pick':True,'bans':[]},
    ]
    smoke=[]
    for data in contexts:
        ctx=context_aus_daten(data)
        result=recommend(ctx)
        if len(data['enemy_picks'])==3:result['legacy']=compare(ctx)
        smoke.append({'context':data,'response':normalized(result)})
    now=timezone.now()
    due=TrackedPlayer.objects.filter(is_active=True,discovery_frontier__isnull=False).filter(
        Q(last_fetched_at__isnull=True)|Q(last_fetched_at__lte=now-timedelta(hours=6))).filter(
        Q(next_fetch_after__isnull=True)|Q(next_fetch_after__lte=now)).count()
    backoffs=list(CollectorRun.objects.filter(parameters__strategie='ranked_development_v1',
        report__api_backoff_required=True).values_list('report__api_backoff_until',flat=True))
    ready={'observed_at':now.isoformat(),'due_observed_targets':due,'discovery_frontier':DiscoveryPlayer.objects.count(),
        'active_backoffs':[v for v in backoffs if v and parse_datetime(v)>now],
        'credential':'NOT_LOADED_NOT_TESTED','http_attempts':0,'collection_started':False}
result={'schema':'drafter-migration-audit-1','source_table_counts':counts,
    'expected_restored_table_counts':{n:0 if n in excluded else v for n,v in counts.items()},
    'excluded_table_data':excluded,'critical_table_sha256':table_hashes,
    'checkpoint_sha256':checkpoint['dataset_sha256'],'checkpoint_n':len(members),'original_train_sha256':TRAIN_DIGEST,
    'artifact_sha256':artifacts,'smoke':smoke,'smoke_sha256':digest(smoke),'collector_readiness':ready,
    'old_holdout':'opaque backup only; no split membership or quality inspection','final_test_or_fitting':False}
expected=os.environ.get('DRAFTER_MIGRATION_EXPECTED')
if expected:
    baseline=json.loads(Path(expected).read_text())
    for key in ('expected_restored_table_counts','critical_table_sha256','checkpoint_sha256','checkpoint_n','original_train_sha256','artifact_sha256','smoke_sha256'):
        assert result[key]==baseline[key], 'Handoff mismatch: '+key
    comparison_counts='source_table_counts' if os.environ.get('DRAFTER_MIGRATION_SOURCE_RECHECK')=='1' else 'expected_restored_table_counts'
    assert counts==baseline[comparison_counts], 'Unexpected database rows'
    result['handoff_comparison']='PASS'
output=Path(os.environ['DRAFTER_MIGRATION_OUTPUT'])
with output.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True)
os.chmod(output,0o644)  # New audit inside private package directory, never source DB/artifacts.
print(json.dumps({'output':str(output),'checkpoint_n':len(members),'checkpoint_sha256':checkpoint['dataset_sha256'],
    'smoke_sha256':result['smoke_sha256'],'collector_readiness':ready,'handoff_comparison':result.get('handoff_comparison','SOURCE_CAPTURED')},indent=2))
