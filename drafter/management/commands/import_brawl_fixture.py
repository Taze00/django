# -*- coding: utf-8 -*-
"""Match-Dateien einlesen - idempotent und dedupliziert.

    python manage.py import_brawl_fixture drafter/testdaten/synthetisch_ranked.json
    python manage.py import_brawl_fixture                 # config.FIXTURE_VERZEICHNIS
    python manage.py import_brawl_fixture PFAD --trockenlauf

Schreibt nur Rohdaten (Lieferungen, Partien, Spieler, Bans). Statistiken
entstehen erst mit `aggregate_brawl_stats` - die Trennung erlaubt es,
nach einer Aenderung der Gewichtung neu zu aggregieren, ohne neu zu
importieren.
"""

from django.core.management.base import BaseCommand, CommandError

from drafter import config
from drafter.services.ingest.importer import MatchImporter
from drafter.services.providers.fixture import FixtureDataProvider


class Command(BaseCommand):
    help = "Liest Match-Dateien (drafter.match.v1) ein - idempotent und dedupliziert."

    def add_arguments(self, parser):
        parser.add_argument(
            "pfade", nargs="*",
            help=f"Dateien oder Verzeichnisse. Ohne Angabe: {config.FIXTURE_VERZEICHNIS}",
        )
        parser.add_argument(
            "--trockenlauf", action="store_true",
            help="Alles prüfen und berichten, nichts speichern.",
        )

    def handle(self, *args, **optionen):
        provider = FixtureDataProvider(optionen["pfade"] or [config.FIXTURE_VERZEICHNIS])
        status = provider.status()
        if not status.verfuegbar:
            raise CommandError(status.grund)

        bericht = MatchImporter(provider, trockenlauf=optionen["trockenlauf"]).ausfuehren()
        for zeile in bericht.zeilen():
            self.stdout.write(zeile)
        if bericht.neu and not optionen["trockenlauf"]:
            self.stdout.write(self.style.SUCCESS(
                "\nNächster Schritt: python manage.py aggregate_brawl_stats --quelle ..."
            ))
