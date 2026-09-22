"""Emit a read-only manifest for the eligible V2 evaluation dataset."""

import hashlib
import json
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from drafter import config
from drafter.models.matches import Match
from drafter.services.evaluation import examples_from_queryset, time_split


class Command(BaseCommand):
    help = "Create a deterministic, read-only manifest of the V2 dataset split"

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.add_argument("--train-fraction", type=float, default=0.6)
        parser.add_argument("--validation-fraction", type=float, default=0.2)
        parser.add_argument("--git-commit", default="", help="Host commit for the manifest")

    def handle(self, *args, **options):
        queryset = Match.objects.filter(
            is_ranked=True,
            battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN,
        )
        examples, skipped = examples_from_queryset(queryset)
        train, validation, holdout = time_split(
            examples, options["train_fraction"], options["validation_fraction"]
        )
        ordered = train + validation + holdout
        fingerprint_digest = hashlib.sha256(
            "\n".join(row.fingerprint for row in ordered).encode("utf-8")
        ).hexdigest()
        report = {
            "manifest_version": "v2-dataset-freeze-1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "git_commit": options["git_commit"] or "UNKNOWN",
            "filter": {
                "is_ranked": True,
                "battle_types": list(config.DRAFT_STATISTIK_BATTLE_TYPEN),
                "known_winner": True,
                "no_conflict": True,
                "complete_3v3": True,
            },
            "counts": {
                "eligible": len(ordered),
                "skipped": skipped,
                "train": len(train),
                "validation": len(validation),
                "holdout": len(holdout),
            },
            "fingerprint_sha256": fingerprint_digest,
            "ranges": {
                name: {
                    "first": rows[0].played_at.isoformat() if rows else None,
                    "last": rows[-1].played_at.isoformat() if rows else None,
                }
                for name, rows in (
                    ("train", train), ("validation", validation), ("holdout", holdout)
                )
            },
        }
        if options["format"] == "json":
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        else:
            self.stdout.write(self.style.SUCCESS("Drafter V2 dataset freeze (read-only)"))
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))