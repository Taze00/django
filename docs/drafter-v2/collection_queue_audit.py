"""Run via manage.py shell under PostgreSQL read-only protection.

Print aggregate selection diagnostics only, never player tags or credentials.
The cutoff/refresh parameters mirror COLLECTION_RUNBOOK.md, not model inputs.
No Collector instance, API client, sampling mutation or evaluator is invoked.
"""

import json
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from drafter import config
from drafter.models.collector import CollectorRun, TrackedPlayer
from drafter.models.matches import MatchPlayer
from drafter.services.stichprobe import HighRankStichprobe

now = timezone.now()
sample = HighRankStichprobe()
qualified = [tag for tag, rank in sample.belegte_kandidaten()]
active = TrackedPlayer.objects.filter(is_active=True, depth__lte=1)
due = active.filter(Q(last_fetched_at__isnull=True) | Q(last_fetched_at__lt=now-timedelta(hours=6))).filter(Q(next_fetch_after__isnull=True) | Q(next_fetch_after__lte=now))
ranked_players = MatchPlayer.objects.filter(match__battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN)
run = CollectorRun.objects.latest('id')
print(json.dumps({
    'read_only': True,
    'checked_at': now.isoformat(),
    'ranked_player_rows': ranked_players.count(),
    'ranked_player_rows_with_tags': ranked_players.exclude(player_tag='').count(),
    'broad_min_rank_config': config.BROAD_MIN_RANG,
    'broad_qualified_players': len(qualified),
    'active_tracked_depth_at_most_1': active.count(),
    'due_tracked_players': due.count(),
    'due_broad_qualified_players': due.filter(tag__in=qualified).count(),
    'latest_run': {'id': run.id, 'started_at': run.started_at.isoformat(), 'status': run.status,
        'strategy': run.parameters.get('strategie'), 'max_players': run.parameters.get('max_spieler'),
        'max_depth': run.parameters.get('max_tiefe')},
}, indent=2))
