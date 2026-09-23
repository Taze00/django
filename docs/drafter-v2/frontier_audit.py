"""Run through isolated manage.py shell with PGOPTIONS read-only. Counts only."""
import json
from datetime import datetime, timedelta, timezone

from django.db.models import Count, Q
from django.utils import timezone as django_timezone

from drafter.models import CollectorRun, MatchPlayer, RawPayload, TaggedPlayer, TaggedPlayerObservation, TrackedPlayer

cutoff = datetime(2026, 9, 18, 15, 4, 42, tzinfo=timezone.utc)
now = django_timezone.now()
run = CollectorRun.objects.filter(parameters__strategie="tagged_frontier_v1").first()
due = TrackedPlayer.objects.filter(tagged_frontier__isnull=False, is_active=True).filter(
    Q(last_fetched_at__isnull=True) | Q(last_fetched_at__lte=now - timedelta(hours=6))
).filter(Q(next_fetch_after__isnull=True) | Q(next_fetch_after__lte=now))
historical = MatchPlayer.objects.filter(match__battle_type="soloRanked", match__played_at__lte=cutoff)
raw = RawPayload.objects.filter(collector_run=run) if run else RawPayload.objects.none()
report = {
    "audit_at": now.isoformat(), "read_only": True,
    "frontier_size": TaggedPlayer.objects.count(), "frontier_due": due.count(),
    "frontier_first_sources": list(TaggedPlayer.objects.values("first_source").annotate(n=Count("pk")).order_by("first_source")),
    "frontier_depths": list(TaggedPlayer.objects.values("discovery_depth").annotate(n=Count("pk")).order_by("discovery_depth")),
    "observation_sources": list(TaggedPlayerObservation.objects.values("source").annotate(n=Count("pk")).order_by("source")),
    "historical_ranked_player_rows": historical.count(),
    "historical_ranked_players_with_tags": historical.exclude(player_tag="").count(),
    "latest_run": None if run is None else {"id": run.pk, "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "status": run.status, "parameters": run.parameters, "report": run.report},
    "payloads": list(raw.values("id", "content_hash", "format", "parse_status", "sampling").order_by("id")),
}
# Nur Strukturbelege; keine Tags, Namen, Antwortkoerper oder Credentials ausgeben.
ranking = raw.filter(format="brawlstars.rankings.raw").first()
if ranking:
    body = ranking.payload.get("antwort")
    items = body.get("items") if isinstance(body, dict) else None
    report["ranking_schema"] = {
        "endpoint": ranking.payload.get("endpoint"),
        "http_status": ranking.payload.get("http_status"),
        "entry_count": len(items) if isinstance(items, list) else None,
        "observed_item_keys": sorted({k for item in (items or []) if isinstance(item, dict) for k in item}),
    }
print(json.dumps(report, indent=2, sort_keys=True))
