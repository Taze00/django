# -*- coding: utf-8 -*-
"""Kontrollierter Test gegen die offizielle Brawl-Stars-API.

    python manage.py test_brawl_api --player "#TAG"        # /players/{tag} + /battlelog
    python manage.py test_brawl_api --brawlers             # /brawlers
    python manage.py test_brawl_api --analysiere DATEI     # Feldstruktur, ohne Netz

Ruft ab und SPEICHERT - importiert nichts, aggregiert nichts. Jede Antwort
landet vollstaendig und unveraendert als Datei in data/brawl_api_raw/,
zusammen mit Endpoint, HTTP-Status und Antwort-Headern.

Der API-Key kommt ausschliesslich aus BRAWL_STARS_API_KEY. Er ist bewusst
KEIN Argument dieses Commands: Argumente landen in der Shell-History und
in Prozesslisten.

`--analysiere` gibt die Struktur einer gespeicherten Antwort aus - Pfade,
Typen und wie oft ein Feld vorkommt, aber keine Werte. So kann die
Struktur geteilt werden, ohne Spielernamen oder Tags auszugeben.
"""

import json
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from drafter import config
from drafter.services.brawl_api_client import ApiFehler, BrawlApiClient, tag_normalisieren
from drafter.services.ingest.parser import (
    FORMAT_OFFIZIELLE_BRAWLER, FORMAT_OFFIZIELLER_BATTLELOG, FORMAT_OFFIZIELLER_SPIELER,
)
from drafter.services.providers.official_api import (
    dateiname, speichere_mitschnitt, verpacke_mitschnitt,
)


def feldstruktur(wert, pfad="", sammlung=None):
    """Alle Pfade einer JSON-Struktur mit Typen und Vorkommen - ohne Werte.

    Listen werden als [] zusammengefasst: "items[].battle.mode" sagt, dass
    jedes Element einer Liste dieses Feld haben KANN. Wie oft es wirklich
    vorkommt, steht daneben - so faellt auf, wenn ein Feld nur manchmal da ist.
    """
    if sammlung is None:
        sammlung = defaultdict(lambda: {"typen": set(), "anzahl": 0})
    eintrag = sammlung[pfad or "(wurzel)"]
    eintrag["anzahl"] += 1
    if isinstance(wert, dict):
        eintrag["typen"].add("objekt")
        for schluessel, kind in wert.items():
            feldstruktur(kind, f"{pfad}.{schluessel}" if pfad else schluessel, sammlung)
    elif isinstance(wert, list):
        eintrag["typen"].add(f"liste")
        for kind in wert:
            feldstruktur(kind, f"{pfad}[]", sammlung)
    else:
        eintrag["typen"].add(type(wert).__name__ if wert is not None else "null")
    return sammlung


class Command(BaseCommand):
    help = "Ruft ausgewählte Endpoints der offiziellen API ab und speichert die Rohantworten."

    def add_arguments(self, parser):
        parser.add_argument("--player", help='Spieler-Tag, z.B. "#2ABC" (Anführungszeichen wegen #)')
        parser.add_argument("--brawlers", action="store_true", help="GET /brawlers")
        parser.add_argument("--analysiere", metavar="DATEI",
                            help="Feldstruktur einer gespeicherten Antwort ausgeben (ohne Netz)")
        parser.add_argument("--ziel", default=str(config.FIXTURE_VERZEICHNIS),
                            help="Verzeichnis für die Rohantworten")

    def handle(self, *args, **optionen):
        if optionen["analysiere"]:
            self._analysiere(Path(optionen["analysiere"]))
            return

        if not (optionen["player"] or optionen["brawlers"]):
            raise CommandError("Nichts zu tun: --player, --brawlers oder --analysiere angeben.")

        client = BrawlApiClient()
        if not client.einsatzbereit:
            raise CommandError(
                "BRAWL_STARS_API_KEY ist nicht gesetzt. In die .env eintragen und den Befehl "
                "über `docker compose run --rm --no-deps -T django-dev …` starten - ein "
                "laufender Container übernimmt eine geänderte .env erst nach Neuerzeugung."
            )

        auftraege = []
        if optionen["player"]:
            tag = optionen["player"]
            kodiert = tag_normalisieren(tag)
            auftraege += [
                ("player", tag, f"players/{kodiert}", FORMAT_OFFIZIELLER_SPIELER),
                ("battlelog", tag, f"players/{kodiert}/battlelog", FORMAT_OFFIZIELLER_BATTLELOG),
            ]
        if optionen["brawlers"]:
            auftraege.append(("brawlers", "alle", "brawlers", FORMAT_OFFIZIELLE_BRAWLER))

        fehler = 0
        for art, referenz, pfad, format_name in auftraege:
            try:
                antwort = client.abrufen(pfad)
            except ApiFehler as problem:
                fehler += 1
                # Die Meldung ist im Client bereits vom Key bereinigt.
                self.stderr.write(self.style.ERROR(f"{art}: {problem}"))
                continue

            ziel = speichere_mitschnitt(
                verpacke_mitschnitt(antwort, referenz, format_name),
                optionen["ziel"], dateiname(art, referenz, antwort.abgerufen_am),
            )
            groesse = ziel.stat().st_size
            self.stdout.write(self.style.SUCCESS(
                f"{art}: HTTP {antwort.status} {antwort.pfad} -> {ziel} ({groesse} Bytes)"
            ))
            self.stdout.write(f"  Antwort-Header: {', '.join(sorted(antwort.header))}")
            if isinstance(antwort.daten, dict):
                self.stdout.write(f"  Oberste Felder: {', '.join(sorted(antwort.daten))}")

        if fehler:
            raise CommandError(f"{fehler} von {len(auftraege)} Abrufen fehlgeschlagen (siehe oben).")

    def _analysiere(self, datei):
        try:
            huelle = json.loads(datei.read_text(encoding="utf-8"))
        except (OSError, ValueError) as problem:
            raise CommandError(f"Datei nicht lesbar: {problem}")
        antwort = huelle.get("antwort") if isinstance(huelle, dict) else None
        if antwort is None:
            raise CommandError("Keine Mitschnitt-Datei: Schlüssel 'antwort' fehlt.")

        self.stdout.write(f"Format: {huelle.get('format')} | Endpoint: {huelle.get('endpoint')} "
                          f"| HTTP {huelle.get('http_status')}")
        self.stdout.write(f"Antwort-Header: {', '.join(sorted(huelle.get('antwort_header') or {}))}")
        struktur = feldstruktur(antwort)
        breite = max(len(p) for p in struktur)
        for pfad in sorted(struktur):
            eintrag = struktur[pfad]
            self.stdout.write(
                f"  {pfad:<{breite}}  {'/'.join(sorted(eintrag['typen'])):<18} x{eintrag['anzahl']}"
            )
