"""Read-only operational counts. No historical holdout rows or secrets loaded."""
import json
from datetime import timedelta
from django.db.models import Q, Min
from django.utils import timezone
from drafter.models import TaggedPlayer, TrackedPlayer, Match, Praxisfall
from drafter.services.v2_snapshots import response_digest

now = timezone.now()
frontier = TrackedPlayer.objects.filter(tagged_frontier__isnull=False, is_active=True)
due = frontier.filter(Q(last_fetched_at__isnull=True) | Q(last_fetched_at__lte=now-timedelta(hours=6))).filter(
    Q(next_fetch_after__isnull=True) | Q(next_fetch_after__lte=now))
records = Praxisfall.objects.filter(snapshot_metadata__schema='drafter-shadow-1')
integrity = sum(response_digest(r.snapshot_metadata['response']) != r.snapshot_metadata['response_sha256'] for r in records)
new = Match.objects.filter(played_at__gt='2026-09-18T15:04:42Z', source='api')
print(json.dumps({'at':now.isoformat(), 'read_only':True, 'frontier_size':TaggedPlayer.objects.count(),
                  'frontier_due':due.count(), 'next_fetch_after_min':frontier.aggregate(t=Min('next_fetch_after'))['t'],
                  'new_api_soloRanked':new.filter(battle_type='soloRanked',is_ranked=True).count(),
                  'new_api_trophy_ranked':new.filter(battle_type='ranked').count(),
                  'shadow_snapshots':records.count(), 'shadow_integrity_failures':integrity,
                  'collection_started':False, 'holdout_read':False},default=str,sort_keys=True,indent=2))
