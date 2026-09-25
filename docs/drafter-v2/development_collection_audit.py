"""Read-only development acquisition/lineage audit; no model-quality computation."""
import json
from collections import Counter
from pathlib import Path
from django.db import connection,transaction
from django.utils import timezone
from drafter.models import CollectorRun,RawPayload,Match
from drafter.models.discovery import DiscoveryPlayer
from drafter.services.development_collection import SAMPLING
from drafter.services.development_dataset import new_development_inventory
from drafter.services.ingest.importer import inhalts_hash

with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    now=timezone.now()
    members,coverage=new_development_inventory(now)
    runs=list(CollectorRun.objects.filter(parameters__strategie=SAMPLING).order_by('id'))
    closed=[r for r in runs if r.finished_at]
    totals=Counter();statuses=Counter();raw_types=Counter()
    for run in closed:
        report=run.report
        for name in ('battlelog_attempts','spieler_abgefragt','new_discovered_tags',
                     'new_eligible_solo_ranked_matches','duplikate','konflikte'):
            totals[name]+=report.get(name,0)
        totals['retries']+=report.get('api',{}).get('wiederholungen',0)
        statuses.update(report.get('api',{}).get('status',{}))
        raw_types.update(report.get('raw_battle_types',{}))
    payloads=[]
    for raw in RawPayload.objects.filter(collector_run__in=closed).order_by('pk').iterator(chunk_size=100):
        assert raw.content_hash==inhalts_hash(raw.payload)
        payloads.append({'id':raw.pk,'sha256':raw.content_hash,'run_id':raw.collector_run_id})
    tags=Counter();missing=0
    for match in Match.objects.filter(fingerprint__in=[m['fingerprint'] for m in members]).prefetch_related('players'):
        for player in match.players.all():
            if player.player_tag:tags[player.player_tag]+=1
            else:missing+=1
    report={'schema':'ranked-development-acquisition-audit-1','audited_at':now.isoformat(),
        'closed_run_ids':[r.pk for r in closed],'running_run_ids':[r.pk for r in runs if not r.finished_at],
        'runs':[{'id':r.pk,'started_at':r.started_at.isoformat(),
                 'finished_at':r.finished_at.isoformat() if r.finished_at else None,
                 'status':r.status,'parameters':r.parameters,'report':r.report} for r in runs],
        'closed_run_totals':dict(totals),'http_status_counts':dict(statuses),'raw_type_counts':dict(raw_types),
        'verified_raw_payloads':payloads,'raw_integrity':'VERIFIED','current_dataset':coverage,
        'discovery_frontier_size':DiscoveryPlayer.objects.count(),
        'sampling_diagnostics':{'unique_observed_player_tags_in_eligible_matches':len(tags),
            'observed_player_occurrences':sum(tags.values()),'missing_player_tag_occurrences':missing,
            'max_matches_for_one_observed_player':max(tags.values(),default=0),
            'interpretation':'repeated-player graph sample; matches are not independent; no weights inferred'},
        'performance_metrics_computed':False,'old_holdout_read':False,'final_test_registered':False}
print(json.dumps(report,indent=2,sort_keys=True))
