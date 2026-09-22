"""Audit newer API observations without training or reopening a sealed holdout."""

import json
from collections import Counter
from datetime import timezone

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Max
from django.utils.dateparse import parse_datetime

from drafter import config
from drafter.models import Datenquelle
from drafter.models.collector import CollectorRun
from drafter.models.matches import Match


class Command(BaseCommand):
    help = "Read-only inventory of API matches played strictly after a sealed cutoff"

    def add_arguments(self, parser):
        parser.add_argument("--after", required=True, help="Sealed last match timestamp with timezone")
        parser.add_argument("--format", choices=("text", "json"), default="text")

    def handle(self, *args, **options):
        try:
            after = parse_datetime(options["after"])
        except (TypeError, ValueError):
            after = None
        if after is None or after.utcoffset() is None:
            raise CommandError("--after must be an ISO-8601 timestamp with an explicit timezone")
        after = after.astimezone(timezone.utc)
        api = Match.objects.filter(source=Datenquelle.API)
        ranked = api.filter(is_ranked=True, battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN)
        newer = api.filter(played_at__gt=after)
        candidates = ranked.filter(played_at__gt=after)
        excluded, sampling = Counter(), Counter()
        eligible = 0
        first = last = None
        # Nur neue Zeilen pruefen; keine Labels/Features des alten Holdouts laden.
        for match in candidates.order_by("played_at", "fingerprint").prefetch_related(
                "players", "payloads").iterator(chunk_size=500):
            if match.has_conflict or match.winner_side not in ("a", "b"):
                excluded["unknown_or_conflict_result"] += 1
                continue
            players = list(match.players.all())
            sides = Counter(player.side for player in players)
            if (len(players) != 6 or sides != {"a": 3, "b": 3}
                    or any(player.brawler_id is None for player in players)):
                excluded["not_complete_known_3v3"] += 1
                continue
            eligible += 1
            first = first or match.played_at
            last = match.played_at
            # Mehrere Sichtungen derselben Partie sind keine weiteren Samples.
            origins = {payload.sampling or "UNKNOWN" for payload in match.payloads.all()}
            sampling.update(origins or {"UNKNOWN"})

        latest = ranked.aggregate(last=Max("played_at"))["last"]
        report = {
            "report_version": "v2-growth-1",
            "read_only": True,
            "after_exclusive": after.isoformat(),
            "filter": {"source": Datenquelle.API, "ranked_types": list(config.DRAFT_STATISTIK_BATTLE_TYPEN)},
            "status": "OBSERVATIONS_AVAILABLE" if eligible else "DATA_UNAVAILABLE",
            "latest_api_ranked_at": latest.isoformat() if latest else None,
            "new_api_matches": newer.count(),
            "new_api_by_battle_type": list(newer.values("battle_type").annotate(n=Count("id")).order_by("battle_type")),
            "new_api_ranked_matches": candidates.count(),
            "eligible_new_ranked_matches": eligible,
            "excluded": dict(sorted(excluded.items())),
            "eligible_range": {"first": first.isoformat() if first else None,
                               "last": last.isoformat() if last else None},
            "sampling_match_counts": dict(sorted(sampling.items())),
            "sampling_counts_overlap": True,
            "promotion": "NOT_ASSESSED",
            "holdout_evaluated": False,
            "recent_collector_runs": self._runs(),
        }
        if options["format"] == "text":
            self.stdout.write("Drafter V2 growth audit: no training, evaluation or new freeze")
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True))

    @staticmethod
    def _runs():
        runs = []
        # Nur Zaehler ausgeben; keine Spieler-Tags, Rohantworten oder Fehlertexte.
        fields = ("spieler_abgefragt", "neu", "duplikate", "konflikte", "neu_nach_typ", "duplikate_nach_typ")
        for run in CollectorRun.objects.order_by("-started_at", "-id")[:5]:
            report = run.report or {}
            api = report.get("api") or {}
            runs.append({
                "id": run.pk,
                "started_at": run.started_at.isoformat(),
                "status": run.status,
                "counts": {key: report.get(key) for key in fields},
                "api": {key: api.get(key) for key in ("anfragen", "status", "wiederholungen")},
            })
        return runs
