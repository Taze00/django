"""Bounded official-ranking bootstrap; never trains or aggregates."""

import json

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from drafter.services.brawl_api_client import ApiFehler
from drafter.services.tagged_frontier import TaggedFrontierCollector


class Command(BaseCommand):
    help = "Isolated tagged frontier: up to one ranking GET and five battlelog HTTP attempts"

    def add_arguments(self, parser):
        parser.add_argument("--after", required=True, help="Exclusive sealed played-at cutoff with timezone")
        parser.add_argument("--ranking-seeds", type=int, choices=range(6), default=0)
        parser.add_argument("--max-battlelogs", type=int, choices=range(6), default=5)
        parser.add_argument("--max-depth", type=int, choices=(0, 1), default=1)
        parser.add_argument("--code-revision", default="UNKNOWN")

    def handle(self, *args, **options):
        try:
            collector = TaggedFrontierCollector(
                after=parse_datetime(options["after"]), ranking_seeds=options["ranking_seeds"],
                max_battlelogs=options["max_battlelogs"], max_depth=options["max_depth"],
                code_revision=options["code_revision"],
            )
        except (TypeError, ValueError) as error:
            raise CommandError(str(error)) from None
        try:
            report = collector.execute()
        except ApiFehler as error:
            raise CommandError(str(error)) from None
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        if report["abbruch"]:
            raise CommandError(report["abbruch"])
