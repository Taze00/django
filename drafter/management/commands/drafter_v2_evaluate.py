"""Run the frozen, time-based Drafter V2 baseline evaluation."""

import json
import os
import subprocess
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from drafter import config
from drafter.models import Brawler
from drafter.models.matches import Match
from drafter.services.context import DraftContext, DraftFehler
from drafter.services.daten import Datenraum
from drafter.services.draft_engine import DraftEngine
from drafter.services.evaluation import evaluate, examples_from_queryset, time_split
from drafter.services.v2_model import evaluate_model, train_model


class Command(BaseCommand):
    help = "Evaluate read-only V2 baselines on a time-based match split"

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.add_argument("--train-fraction", type=float, default=0.6)
        parser.add_argument("--validation-fraction", type=float, default=0.2)
        parser.add_argument("--skip-legacy", action="store_true",
                    help="Skip the unchanged Legacy benchmark")
        parser.add_argument("--git-commit", default="", help="Host commit for reproducible reports")

    def handle(self, *args, **options):
        queryset = Match.objects.filter(
            is_ranked=True,
            battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN,
        )
        examples, skipped = examples_from_queryset(queryset)
        train, validation, holdout = time_split(
            examples, options["train_fraction"], options["validation_fraction"]
        )
        report = {
            "status": "ok" if holdout else "DATA_UNAVAILABLE",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "git_commit": options["git_commit"] or self._git_commit(),
            "split": {
                "train_fraction": options["train_fraction"],
                "validation_fraction": options["validation_fraction"],
                "holdout_fraction": 1 - options["train_fraction"] - options["validation_fraction"],
                "train": self._range(train),
                "validation": self._range(validation),
                "holdout": self._range(holdout),
            },
            "counts": {
                "input": len(examples),
                "skipped": skipped,
                "train": len(train),
                "validation": len(validation),
                "holdout": len(holdout),
            },
            "models": evaluate(train, validation, holdout) if train else {},
        }
        if train:
            v2_candidate = train_model(train, regularization=1.0, epochs=300)
            report["v2_candidate"] = {
                "validation": evaluate_model(v2_candidate, validation),
                "holdout": evaluate_model(v2_candidate, holdout),
                "training": {"regularization": 1.0, "epochs": 300},
            }
        if holdout and not options["skip_legacy"]:
            legacy = self._legacy_predictions(holdout)
            report["legacy"] = self._legacy_result(legacy[0])
            report["legacy"]["skipped"] = legacy[1]
            report["shared_subset"] = self._shared_subset_result(
                train, legacy[0]
            )
        if options["format"] == "json":
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        else:
            self.stdout.write(self.style.SUCCESS("Drafter V2 evaluation (read-only)"))
            self.stdout.write(f"Status: {report['status']}")
            self.stdout.write(f"Counts: {report['counts']}")
            for name, result in report["models"].items():
                self.stdout.write(f"{name}: holdout={result['holdout']}")

    @staticmethod
    def _range(rows):
        return {
            "first": rows[0].played_at.isoformat() if rows else None,
            "last": rows[-1].played_at.isoformat() if rows else None,
        }

    @staticmethod
    def _git_commit():
        if os.environ.get("DRAFTER_V2_COMMIT"):
            return os.environ["DRAFTER_V2_COMMIT"]
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return "UNKNOWN"

    @staticmethod
    def _legacy_predictions(rows):
        """Evaluate the unchanged Legacy probability layer on the holdout."""
        brawlers = {b.id: b for b in Brawler.objects.all()}
        predictions = []
        skipped = {}
        raum_cache = {}
        for row in rows:
            try:
                match = Match.objects.select_related("game_mode", "brawl_map").prefetch_related(
                    "players__brawler"
                ).get(fingerprint=row.fingerprint)
            except Match.DoesNotExist:
                continue
            players = [player for player in match.players.all() if player.brawler_id in brawlers]
            own = tuple(player.brawler for player in players if player.side == "a")
            enemy = tuple(player.brawler for player in players if player.side == "b")
            if len(own) != 3 or len(enemy) != 3:
                continue
            try:
                cache_key = (match.game_mode_id, match.brawl_map_id, match.patch_id)
                raum = raum_cache.get(cache_key)
                if raum is None:
                    raum = Datenraum(
                        brawl_map=match.brawl_map,
                        game_mode=match.game_mode,
                        patch=match.patch,
                        rank_pool="alle",
                    ).laden()
                    raum_cache[cache_key] = raum
                context = DraftContext(
                    game_mode=match.game_mode,
                    brawl_map=match.brawl_map,
                    own_picks=own,
                    enemy_picks=enemy,
                    own_team_first_pick=True,
                )
                prediction = DraftEngine(context, raum=raum).siegchance()["prozent"] / 100.0
            except DraftFehler as error:
                reason = str(error)
                skipped[reason] = skipped.get(reason, 0) + 1
                continue
            predictions.append((row, prediction))
        return predictions, skipped

    @staticmethod
    def _legacy_result(predictions):
        if not predictions:
            return {"status": "DATA_UNAVAILABLE", "n": 0}
        from drafter.services.evaluation import metrics

        class Row:
            def __init__(self, prediction, label):
                self.prediction = prediction
                self.label = label

        # Reuse the metric definition without making the Legacy probability
        # layer part of V2 training or changing its output.
        return metrics(lambda row: row.prediction, [
            Row(prediction, row.label) for row, prediction in predictions
        ])

    @staticmethod
    def _shared_subset_result(train, legacy_predictions):
        """Compare fixed V2 and Legacy only on identical Legacy-eligible rows."""
        if not legacy_predictions:
            return {"status": "DATA_UNAVAILABLE", "n": 0}
        from drafter.services.evaluation import metrics

        model = train_model(train, regularization=1.0, epochs=300)
        rows = [row for row, _ in legacy_predictions]
        legacy_rows = [
            type("Prediction", (), {"prediction": prediction, "label": row.label})
            for row, prediction in legacy_predictions
        ]
        return {
            "n": len(rows),
            "fingerprints": [row.fingerprint for row in rows],
            "legacy": metrics(lambda item: item.prediction, legacy_rows),
            "v2_candidate": evaluate_model(model, rows),
        }