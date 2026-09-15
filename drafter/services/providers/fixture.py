# -*- coding: utf-8 -*-
"""Matches aus JSON-Dateien - ohne Live-API.

Zweck: echte API-Antworten einmal mitschneiden, lokal ablegen und die
gesamte Pipeline danach beliebig oft ohne Netz und ohne Key durchlaufen
lassen. Dieselben Dateien dienen als Testgrundlage.

Jede Datei ist eine Lieferung. Welcher Parser sie liest, entscheidet ihr
Feld "format":

    drafter.match.v1           -> eigenes Format, wird ausgewertet
    brawlstars.battlelog.raw   -> Mitschnitt der offiziellen API; wird
                                  gespeichert, aber (noch) NICHT ausgewertet,
                                  weil es dafuer keinen geprueften Parser gibt

Die Herkunft ("herkunft": "synthetisch" | "api-mitschnitt" | ...) ist
Pflicht. Synthetische Dateien landen mit source="synthetic" in der
Datenbank und werden nie automatisch als Messung benutzt.
"""

import json
from pathlib import Path

from drafter.models.base import Datenquelle
from drafter.services.ingest.parser import ParserFehler, parser_fuer, quelle_fuer
from drafter.services.providers.basis import MatchProvider
from drafter.services.providers.records import Lieferung, ProviderStatus


class FixtureDataProvider(MatchProvider):
    name = "fixture"

    def __init__(self, pfade):
        if isinstance(pfade, (str, Path)):
            pfade = [pfade]
        self.pfade = [Path(p) for p in pfade]

    def dateien(self):
        """Alle JSON-Dateien, in stabiler Reihenfolge."""
        gefunden = []
        for pfad in self.pfade:
            if pfad.is_file() and pfad.suffix == ".json":
                gefunden.append(pfad)
            elif pfad.is_dir():
                gefunden += sorted(pfad.rglob("*.json"))
        return gefunden

    def status(self):
        if not self.dateien():
            orte = ", ".join(str(p) for p in self.pfade)
            return ProviderStatus.nicht_verfuegbar(f"Keine JSON-Dateien unter {orte}")
        return ProviderStatus.bereit()

    def lieferungen(self):
        for datei in self.dateien():
            yield self._lies(datei)

    def _lies(self, datei):
        referenz = datei.name
        try:
            daten = json.loads(datei.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as fehler:
            return Lieferung(
                referenz=referenz, format="", rohdaten=None, source=Datenquelle.FIXTURE,
                status="fehler", meldung=f"Datei nicht lesbar: {fehler}",
            )

        format_name = daten.get("format", "") if isinstance(daten, dict) else ""
        try:
            quelle = quelle_fuer(daten)
        except ParserFehler as fehler:
            # Ohne Herkunft wird nichts gespeichert - sonst laege eine
            # Datei unbekannter Echtheit in den Rohdaten.
            return Lieferung(
                referenz=referenz, format=format_name, rohdaten=None,
                source=Datenquelle.FIXTURE, status="fehler", meldung=str(fehler),
            )

        parser = parser_fuer(format_name)
        if parser is None:
            return Lieferung(
                referenz=referenz, format=format_name, rohdaten=daten, source=quelle,
                matches=None, status="nicht_unterstuetzt",
                meldung=(
                    f"Für das Format {format_name!r} gibt es noch keinen geprüften Parser. "
                    "Die Rohdaten sind gespeichert und können später ausgewertet werden."
                ),
            )

        try:
            ergebnis = parser(daten)
        except ParserFehler as fehler:
            return Lieferung(
                referenz=referenz, format=format_name, rohdaten=daten, source=quelle,
                matches=None, status="fehler", meldung=str(fehler),
            )

        return Lieferung(
            referenz=referenz, format=format_name, rohdaten=daten, source=quelle,
            matches=ergebnis.matches, fehler=ergebnis.fehler,
        )
