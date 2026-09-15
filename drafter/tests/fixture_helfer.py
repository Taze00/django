# -*- coding: utf-8 -*-
"""Werkzeuge fuer Tests mit Match-Dateien.

Alle hier erzeugten Partien sind SYNTHETISCH und tragen das auch in der
Datei ("herkunft": "synthetisch"). Kein Test legt etwas an, das wie eine
echte Spielstatistik aussieht, ohne so gekennzeichnet zu sein.
"""

import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from drafter.services.ingest.importer import MatchImporter
from drafter.services.providers.fixture import FixtureDataProvider

# Fester Bezugspunkt statt "jetzt": Zeitgewichte sollen in jedem Lauf
# dieselben sein, egal an welchem Tag die Tests laufen.
BASIS = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def zeit(tage_zurueck=0, minuten=0, sekunden=0):
    """Ein Zeitpunkt VOR dem Bezugspunkt - nie danach.

    Alle Versaetze gehen rueckwaerts. Frueher wurden Minuten addiert: eine
    Serie mit minuten=1000 lag dann am naechsten Tag, also hinter dem
    Stichtag der Aggregation, und wurde vom Zeitfenster still ignoriert.
    Zwei Counter-Tests waren dadurch gruen, obwohl zwei ihrer drei Serien
    nie gezaehlt wurden. AggregationsTest.aggregiere prueft das jetzt aktiv.
    """
    punkt = BASIS - timedelta(days=tage_zurueck, minutes=minuten, seconds=sekunden)
    return punkt.isoformat().replace("+00:00", "Z")


def _spieler(eintrag):
    return {"brawler": eintrag} if isinstance(eintrag, str) else dict(eintrag)


def partie(a=("gale", "belle", "max"), b=("buster", "gene", "tick"), sieger="a",
           tage_zurueck=0, minuten=0, sekunden=0, modus="Gem Grab", karte="Hard Rock Mine",
           rank_pool="masters", **extra):
    eintrag = {
        "played_at": zeit(tage_zurueck, minuten, sekunden),
        "mode": modus,
        "map": karte,
        "rank_pool": rank_pool,
        "winner": sieger,
        "teams": {"a": [_spieler(s) for s in a], "b": [_spieler(s) for s in b]},
    }
    eintrag.update(extra)
    return eintrag


def serie(anzahl, siege, **kwargs):
    """`anzahl` gleiche Partien, davon `siege` fuer Team a - zeitlich getrennt, rueckwaerts.

    Fuenf Minuten Abstand liegen sicher ausserhalb der Deduplizierungs-
    toleranz; sonst wuerden die Partien zu einer zusammengefasst.
    """
    start = kwargs.pop("minuten", 0)
    return [
        partie(sieger="a" if i < siege else "b", minuten=start + i * 5, **kwargs)
        for i in range(anzahl)
    ]


def datei(matches, herkunft="synthetisch", **extra):
    inhalt = {"format": "drafter.match.v1", "herkunft": herkunft, "matches": list(matches)}
    inhalt.update(extra)
    return inhalt


class FixtureMixin:
    """Temporaeres Verzeichnis und Import in einem Schritt."""

    def setUp(self):
        super().setUp()
        self.verzeichnis = Path(tempfile.mkdtemp(prefix="drafter-test-"))
        self.addCleanup(shutil.rmtree, self.verzeichnis, ignore_errors=True)
        self._zaehler = 0

    def schreibe(self, inhalt, name=None):
        self._zaehler += 1
        pfad = self.verzeichnis / (name or f"lieferung_{self._zaehler:03d}.json")
        text = inhalt if isinstance(inhalt, str) else json.dumps(inhalt, ensure_ascii=False)
        pfad.write_text(text, encoding="utf-8")
        return pfad

    def importiere(self, *matches, herkunft="synthetisch", trockenlauf=False, **extra):
        pfad = self.schreibe(datei(matches, herkunft=herkunft, **extra))
        return MatchImporter(FixtureDataProvider(pfad), trockenlauf=trockenlauf).ausfuehren()
