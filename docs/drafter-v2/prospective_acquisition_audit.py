"""Operational-only read-only audit of the latest registered prospective run.

No model invocation, performance metric, seal or historical Match selection.
Run through manage.py shell with PGOPTIONS read-only; publish only aggregate output.
"""
import json
from collections import Counter
from datetime import timedelta
from pathlib import Path
from django.db import connection, transaction
from django.utils import timezone
from drafter.models import CollectorRun, RawPayload
from drafter.management.commands.drafter_v2_future_window import inventory
from drafter.services.ingest.importer import inhalts_hash
from drafter.services.prospective_acquisition import verify_files, verify_catalog
from drafter.services.v2_future_window import digest, timestamp, validate, POLICY

protocol = json.loads(Path('docs/drafter-v2/PROSPECTIVE_WINDOW.json').read_text())
validate(protocol)
protocol_hash = digest(protocol)
assert protocol_hash == '70e55f3dde205e15b232814f98b4e00c34fac8238f2fe5bc8b190608891adac8'
verify_files(protocol)
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    verify_catalog(protocol)
    runs = CollectorRun.objects.filter(parameters__protocol_sha256=protocol_hash)
    run = runs.latest('started_at')
    assert run.finished_at and run.status == 'finished', 'Audit incomplete/aborted run separately; never retry automatically'
    assert run.parameters['ranking_http_budget'] == 0
    assert run.report['battlelog_attempts'] <= 10
    raws = list(RawPayload.objects.filter(collector_run=run).order_by('pk'))
    raw_types = Counter()
    for raw in raws:
        assert inhalts_hash(raw.payload) == raw.content_hash
        assert raw.source == 'api' and raw.sampling == POLICY['sampling']
        assert raw.payload['http_status'] == 200
        for item in raw.payload.get('antwort', {}).get('items', []):
            value = item.get('battle', {}).get('type')
            raw_types[value if isinstance(value,str) else 'UNKNOWN'] += 1
    rows = list(inventory(protocol))  # SQL restricts to registered interval before loading.
    now = timezone.now()
    excluded = Counter()
    admitted = []
    def rejection(row):
        if row['source'] != 'api' or row['battle_type'] != 'soloRanked' or not row['is_ranked']:
            return 'not_official_soloRanked'
        if row['has_conflict'] or not row['result_known']:
            return 'unknown_or_conflicting_result'
        if not row['complete_unique_3v3'] or not row['known_context']:
            return 'incomplete_duplicate_or_unknown_context'
        common = protocol['common_context']
        if ([row['map_id'],row['mode_id']] not in common['map_mode_pairs']
            or len(row['brawler_ids']) != 6
            or any(b not in common['brawler_ids'] for b in row['brawler_ids'])
            or row['patch_id'] not in common['allowed_import_patch_ids']):
            return 'outside_frozen_common_context'
        if any(o['sampling']=='observed_discovery_pilot_v1' for o in row['origins']):
            return 'pre_registration_acquisition_pilot'
        at = timestamp(row['played_at'])
        if not any(o['sampling']==POLICY['sampling'] and o['source']=='api'
            and o['format']=='brawlstars.battlelog.raw' and o['run_id'] is not None
            and o.get('protocol_sha256')==protocol_hash and o.get('purpose')=='prospective_test'
            and o.get('code_revision')==protocol['code_revision']
            and at <= timestamp(o['fetched_at']) <= now
            and len(o['content_hash'])==64 and all(c in '0123456789abcdef' for c in o['content_hash'])
            for o in row['origins']):
            return 'unverified_provenance'
        if not all(isinstance(row[k],str) and len(row[k])==64
            and all(c in '0123456789abcdef' for c in row[k])
            for k in ('fingerprint','reconstructed_fingerprint','content_sha256')):
            return 'missing_fingerprint'
        return None
    for row in rows:
        reason = rejection(row)
        if reason:
            excluded[reason] += 1
        else:
            admitted.append(row)
    duplicates = {key:len(admitted)-len({r[key] for r in admitted})
                  for key in ('fingerprint','reconstructed_fingerprint')}
    assert not any(duplicates.values()), 'Duplicate prospective identity: fail closed'
    output = {
        'schema':'prospective-acquisition-audit-1', 'audited_at':now.isoformat(),
        'protocol_sha256':protocol_hash, 'run_id':run.pk,
        'started_at':run.started_at.isoformat(),'finished_at':run.finished_at.isoformat(),
        'parameters':run.parameters, 'collector_report':run.report,
        'raw_payloads':[{'id':r.pk,'content_hash':r.content_hash,'sampling':r.sampling,
                         'fetched_at':r.fetched_at.isoformat(),'parse_status':r.parse_status} for r in raws],
        'independent_raw_type_counts':dict(raw_types), 'raw_content_integrity':'VERIFIED',
        'frozen_files_and_catalog':'VERIFIED',
        'window_inventory_count':len(rows),'window_types':dict(Counter(r['battle_type'] for r in rows)),
        'currently_admissible_not_sealed':len(admitted),'exclusions':dict(excluded),
        'latest_run_linked_admissible':sum(any(o['run_id']==run.pk for o in r['origins']) for r in admitted),
        'pilot_origin_rows_in_window':sum(any(o['sampling']=='observed_discovery_pilot_v1' for o in r['origins']) for r in rows),
        'duplicate_admissible_fingerprints':duplicates,
        'window_runs_used':runs.count(),
        'window_http_attempts_used':sum(r.report.get('battlelog_attempts',0) for r in runs),
        'next_run_not_before':(run.started_at+timedelta(hours=6)).isoformat(),
        'sealed':False,'model_predictions_or_performance_metrics_computed':False,
        'automatic_training':False,'recurring_collector':False,
        'frontier_evidence_count_note':'Collector ranked frontier totals include prior pilot provenance; only currently_admissible_not_sealed counts prospective candidates.',
    }
print(json.dumps(output,indent=2,sort_keys=True))
