"""Read-only inventory for the Drafter V2 data audit."""

import json
from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models import Count, Max, Min

from drafter import config
from drafter.models import Brawler, BrawlMap, GameMode, Patch
from drafter.models.collector import CollectorRun, TrackedPlayer
from drafter.models.matches import Match, MatchPlayer, RawPayload
from drafter.models.praxis import Praxisfall
from drafter.models.stats import BuildStat, BrawlerStat, CounterStat, SynergyStat


class Command(BaseCommand):
    help = "Read-only inventory for the Drafter V2 data and provenance audit"

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=("text", "json"),
            default="text",
            help="Output format (default: text)",
        )

    def handle(self, *args, **options):
        report = self._report()
        if options["format"] == "json":
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
            return
        self._write_text(report)

    def _report(self):
        matches = Match.objects.all()
        ranked = matches.filter(
            is_ranked=True,
            battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN,
        )
        countable = ranked.filter(
            winner_side__in=(Match.Seite.A, Match.Seite.B), has_conflict=False
        )
        duplicate_reconstructed = sum(
            row["count"] - 1
            for row in Match.objects.values("reconstructed_fingerprint")
            .exclude(reconstructed_fingerprint="")
            .annotate(count=Count("id"))
            if row["count"] > 1
        )

        return {
            "audit": {
                "command": "python manage.py drafter_v2_audit --format json",
                "ranked_types": list(config.DRAFT_STATISTIK_BATTLE_TYPEN),
                "read_only": True,
            },
            "counts": {
                "raw_payloads": RawPayload.objects.count(),
                "matches": matches.count(),
                "ranked_matches": ranked.count(),
                "countable_ranked_matches": countable.count(),
                "match_players": MatchPlayer.objects.count(),
                "match_bans": self._count("drafter.MatchBan"),
                "tracked_players": TrackedPlayer.objects.count(),
                "collector_runs": CollectorRun.objects.count(),
                "brawlers": Brawler.objects.count(),
                "active_brawlers": Brawler.objects.filter(is_active=True).count(),
                "ranked_available_brawlers": Brawler.objects.filter(
                    ranked_verfuegbar=True
                ).count(),
                "maps": BrawlMap.objects.count(),
                "modes": GameMode.objects.count(),
                "patches": Patch.objects.count(),
                "praxisfaelle": Praxisfall.objects.count(),
                "brawler_stats": BrawlerStat.objects.count(),
                "counter_stats": CounterStat.objects.count(),
                "synergy_stats": SynergyStat.objects.count(),
                "build_stats": BuildStat.objects.count(),
            },
            "matches": {
                "date_range": self._date_range(matches),
                "by_source": self._field_counts(matches, "source"),
                "by_battle_type": self._field_counts(matches, "battle_type"),
                "by_mode": self._field_counts(ranked, "mode_name"),
                "by_map": self._field_counts(ranked, "map_name"),
                "by_patch": self._field_counts(ranked, "patch_id"),
                "conflicts": matches.filter(has_conflict=True).count(),
                "reconstructed_fingerprint_duplicates": duplicate_reconstructed,
                "sampling": self._sampling_counts(ranked),
            },
            "stat_samples": {
                model.__name__: self._sample_summary(model)
                for model in (BrawlerStat, CounterStat, SynergyStat, BuildStat)
            },
            "patches": [
                {
                    **patch,
                    "released_on": patch["released_on"].isoformat(),
                }
                for patch in Patch.objects.order_by("released_on", "id").values(
                    "id", "name", "released_on", "datum_bestaetigt", "datum_quelle"
                )
            ],
        }

    @staticmethod
    def _count(label):
        from django.apps import apps

        app_label, model_name = label.split(".")
        return apps.get_model(app_label, model_name).objects.count()

    @staticmethod
    def _field_counts(queryset, field):
        return [
            {"value": row[field] or "", "count": row["count"]}
            for row in queryset.values(field)
            .annotate(count=Count("id"))
            .order_by("-count", field)
        ]

    @staticmethod
    def _date_range(queryset):
        values = queryset.aggregate(first=Min("played_at"), last=Max("played_at"))
        return {
            "first": values["first"].isoformat() if values["first"] else None,
            "last": values["last"].isoformat() if values["last"] else None,
        }

    @staticmethod
    def _sampling_counts(queryset):
        counts = Counter()
        for match in queryset.prefetch_related("payloads").iterator(chunk_size=500):
            sources = {payload.sampling or "" for payload in match.payloads.all()}
            for source in sources or {""}:
                counts[source] += 1
        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    @staticmethod
    def _sample_summary(model):
        values = model.objects.aggregate(
            min_games=Min("games"),
            max_games=Max("games"),
        )
        games = sorted(model.objects.values_list("games", flat=True))
        if games:
            values["median_games"] = games[(len(games) - 1) // 2]
            values["p90_games"] = games[min(len(games) - 1, int(len(games) * 0.9))]
        else:
            values["median_games"] = None
            values["p90_games"] = None
        return {
            **values,
            "at_least": {str(limit): sum(game >= limit for game in games)
                         for limit in (10, 20, 50, 100, 250, 500)},
        }

    def _write_text(self, report):
        counts = report["counts"]
        self.stdout.write(self.style.SUCCESS("Drafter V2 data audit (read-only)"))
        self.stdout.write("Counts:")
        for key, value in counts.items():
            self.stdout.write(f"  {key}: {value}")
        matches = report["matches"]
        self.stdout.write(
            f"Match dates: {matches['date_range']['first'] or '-'} .. "
            f"{matches['date_range']['last'] or '-'}"
        )
        self.stdout.write(
            f"Fingerprint duplicates: {matches['reconstructed_fingerprint_duplicates']}"
        )
        self.stdout.write(f"Sampling: {matches['sampling']}")
        self.stdout.write("Stat samples:")
        for name, summary in report["stat_samples"].items():
            self.stdout.write(f"  {name}: {summary}")