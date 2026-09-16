# -*- coding: utf-8 -*-
"""Brawler-Katalog mit /brawlers abgleichen - IDs eintragen, Fehlende anlegen.

    python manage.py sync_brawler_katalog --datei data/brawl_api_raw/brawlers_ALLE_*.json
    python manage.py sync_brawler_katalog --abrufen
    python manage.py sync_brawler_katalog --datei DATEI --trockenlauf

Gepflegte Eintraege werden nie ueberschrieben: gesetzt wird nur eine leere
`external_id`. Neue Brawler kommen ohne Profil und inaktiv in den Katalog -
Engine und Oberflaeche sehen sie nicht, Import und Aggregation schon.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from drafter import config
from drafter.services.brawl_api_client import PFAD_BRAWLER, ApiFehler, BrawlApiClient
from drafter.services.ingest.parser import FORMAT_OFFIZIELLE_BRAWLER
from drafter.services.katalog import brawler_abgleichen
from drafter.services.providers.official_api import (
    dateiname, speichere_mitschnitt, verpacke_mitschnitt,
)


def items_aus_datei(pfad):
    """Liste aus einem Mitschnitt - oder aus einer blanken API-Antwort."""
    try:
        inhalt = json.loads(Path(pfad).read_text(encoding="utf-8"))
    except (OSError, ValueError) as fehler:
        raise CommandError(f"Datei nicht lesbar: {fehler}")
    antwort = inhalt.get("antwort", inhalt) if isinstance(inhalt, dict) else None
    items = antwort.get("items") if isinstance(antwort, dict) else None
    if not isinstance(items, list):
        raise CommandError("Die Datei enthält keine Liste 'items'.")
    return items


class Command(BaseCommand):
    help = "Gleicht den Brawler-Katalog mit /brawlers ab (IDs eintragen, Fehlende inaktiv anlegen)."

    def add_arguments(self, parser):
        parser.add_argument("--datei", help="Gespeicherter Mitschnitt von /brawlers")
        parser.add_argument("--abrufen", action="store_true", help="/brawlers jetzt abrufen")
        parser.add_argument("--trockenlauf", action="store_true", help="Nur berichten, nichts speichern")

    def handle(self, *args, **optionen):
        if bool(optionen["datei"]) == bool(optionen["abrufen"]):
            raise CommandError("Genau eines angeben: --datei ODER --abrufen.")

        if optionen["datei"]:
            items = items_aus_datei(optionen["datei"])
        else:
            client = BrawlApiClient()
            if not client.einsatzbereit:
                raise CommandError("BRAWL_STARS_API_KEY ist nicht gesetzt.")
            try:
                antwort = client.abrufen(PFAD_BRAWLER)
            except ApiFehler as fehler:
                raise CommandError(str(fehler))
            ziel = speichere_mitschnitt(
                verpacke_mitschnitt(antwort, "alle", FORMAT_OFFIZIELLE_BRAWLER),
                config.FIXTURE_VERZEICHNIS, dateiname("brawlers", "alle", antwort.abgerufen_am),
            )
            self.stdout.write(f"Rohantwort gespeichert: {ziel}")
            items = antwort.daten.get("items") if isinstance(antwort.daten, dict) else None
            if not isinstance(items, list):
                raise CommandError("Die Antwort enthält keine Liste 'items'.")

        with transaction.atomic():
            ergebnis = brawler_abgleichen(items)
            if optionen["trockenlauf"]:
                transaction.set_rollback(True)

        for zeile in ergebnis.zeilen():
            self.stdout.write(zeile)
        if optionen["trockenlauf"]:
            self.stdout.write("  - Trockenlauf - nichts wurde gespeichert")
