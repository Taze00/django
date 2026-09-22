"""Run the frozen, time-based Drafter V2 baseline evaluation."""

import json
import subprocess
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from drafter import config
from drafter.models.matches import Match
from drafter.services.evaluation import evaluate, examples_from_queryset, time_split


class Command(BaseCommand):
    help = "Evaluate read-only V2 baselines on a time-based match split"

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.add_argument("--train-fraction", type=float, default=0.6)
        parser.add_argument("--validation-fraction", type=float, default=0.2)

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
            "git_commit": self._git_commit(),
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
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return "UNKNOWN"