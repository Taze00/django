"""Train and evaluate the non-active Drafter V2 composition model."""

import json

from django.core.management.base import BaseCommand

from drafter import config
from drafter.models.matches import Match
from drafter.services.evaluation import examples_from_queryset, time_split
from drafter.services.v2_model import dump_model, evaluate_model, train_model


class Command(BaseCommand):
    help = "Train the non-active V2 composition model on a time split"

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.add_argument("--model-path", default="", help="Optional explicit model output path")
        parser.add_argument("--epochs", type=int, default=500)
        parser.add_argument("--regularization", type=float, default=1.0)

    def handle(self, *args, **options):
        queryset = Match.objects.filter(
            is_ranked=True,
            battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN,
        )
        examples, skipped = examples_from_queryset(queryset)
        train, validation, holdout = time_split(examples)
        model = train_model(train, options["regularization"], options["epochs"])
        if model is not None and options["model_path"]:
            dump_model(model, options["model_path"])
        report = {
            "status": "ok" if model and holdout else "DATA_UNAVAILABLE",
            "counts": {
                "input": len(examples), "skipped": skipped,
                "train": len(train), "validation": len(validation), "holdout": len(holdout),
            },
            "model": model.as_dict() if model else None,
            "validation": evaluate_model(model, validation),
            "holdout": evaluate_model(model, holdout),
            "persisted": bool(model and options["model_path"]),
        }
        if options["format"] == "json":
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        else:
            self.stdout.write(self.style.SUCCESS("Drafter V2 model training (non-active)"))
            self.stdout.write(f"Status: {report['status']}")
            self.stdout.write(f"Counts: {report['counts']}")
            self.stdout.write(f"Holdout: {report['holdout']}")