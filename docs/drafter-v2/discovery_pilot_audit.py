"""Read-only audit of D-023 pilot, never historical examples or raw player tags.

Run with manage.py shell < this file under PGOPTIONS read-only.
"""
import json
from collections import Counter
from drafter.models import CollectorRun, Match, RawPayload
from drafter.models.discovery import DiscoveryPlayer, DiscoveryObservation
from drafter.services.tagged_frontier import eligible
from drafter.services.ingest.parser import parse_offizieller_battlelog
from drafter.services.ingest.importer import inhalts_hash
from django.utils.dateparse import parse_datetime

run = CollectorRun.objects.get(parameters__pilot_id="D-023-single-observed-frontier-pilot")
raws = list(RawPayload.objects.filter(collector_run=run).order_by("id"))
cutoff = parse_datetime(run.parameters["after_exclusive"])
types, modes, parsed_types, raw_keys = Counter(), Counter(), Counter(), Counter()
invalid_time, entries, parse_errors, skipped = 0, 0, 0, 0
for raw in raws:
    assert raw.content_hash == inhalts_hash(raw.payload)
    parsed = parse_offizieller_battlelog(raw.payload)
    parse_errors += len(parsed.fehler)
    skipped += len(parsed.uebersprungen)
    for match in parsed.matches:
        parsed_types[match.battle_type] += 1
        invalid_time += int(match.played_at > raw.fetched_at)
    for item in raw.payload.get("antwort", {}).get("items", []):
        entries += 1
        battle = item.get("battle", {})
        types[battle.get("type", "UNKNOWN")] += 1
        modes[battle.get("mode", "UNKNOWN")] += 1
        raw_keys.update(battle.keys())
matches = list(Match.objects.filter(payloads__in=raws, played_at__gt=cutoff).distinct().prefetch_related("players"))
valid = [m for m in matches if eligible(m)]
evidence_match_ids = set(DiscoveryObservation.objects.filter(source="solo_ranked", match__isnull=False).values_list("match_id", flat=True))
evidence_valid = {m.pk for m in Match.objects.filter(pk__in=evidence_match_ids, played_at__gt=cutoff).prefetch_related("players") if eligible(m)}
print(json.dumps({
    "run_id": run.pk, "started_at": run.started_at.isoformat(),
    "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    "status": run.status, "parameters": run.parameters, "report": run.report,
    "payloads": [{"id": r.pk, "content_hash": r.content_hash, "format": r.format,
                  "sampling": r.sampling, "parse_status": r.parse_status,
                  "fetched_at": r.fetched_at.isoformat()} for r in raws],
    "independent_raw_entry_count": entries, "independent_raw_types": dict(types),
    "independent_raw_modes": dict(modes), "observed_battle_key_counts": dict(raw_keys),
    "parsed_types": dict(parsed_types), "parser_error_count": parse_errors,
    "parser_skipped_count": skipped, "played_after_fetch_count": invalid_time,
    "linked_post_cutoff_matches": len(matches), "linked_eligible_soloRanked": len(valid),
    "linked_match_types": dict(Counter(m.battle_type for m in matches)),
    "linked_conflicts": sum(m.has_conflict for m in matches),
    "discovery_frontier_size": DiscoveryPlayer.objects.count(),
    "ranked_evidence_frontier_size": DiscoveryObservation.objects.filter(source="solo_ranked",
        match_id__in=evidence_valid).values("player_id").distinct().count(),
    "future_window_registered": False, "future_test_eligible": False,
}, indent=2, sort_keys=True))
