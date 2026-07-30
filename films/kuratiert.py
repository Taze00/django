"""Laedt die handgepflegten Empfehlungen aus films/data/.

filme.json  - Kinofilme, mit Stimmung und Highlight-Flag
serien.json - Serien und Anime, unterschieden ueber `gattung`

Die Serien-Eintraege stammen aus dem frueheren RANKINGS-Datensatz in
main.js; Texte und Wertungen sind uebernommen (Wertung von der
10er- auf die 5er-Skala umgerechnet).
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATEN = Path(__file__).resolve().parent / "data"
DATEI = DATEN / "filme.json"
DATEI_SERIEN = DATEN / "serien.json"

# Reihenfolge bestimmt auch die Reihenfolge der Filter-Buttons.
STIMMUNGEN = [
    ("mitnehmen", "Mitnehmen"),
    ("nachdenken", "Nachdenken"),
    ("nebenbei", "Nebenbei"),
    ("geheimtipp", "Geheimtipp"),
]

# Erste Filterebene. Reihenfolge = Reihenfolge der Buttons.
GATTUNGEN = [
    ("film", "Filme"),
    ("serie", "Serien"),
    ("anime", "Anime"),
]


def _lade(pfad):
    """JSON-Array aus einer Datei. Bei jedem Problem leer.

    Wie beim RSS gilt: die Sektion ist Beiwerk. Eine kaputte oder
    fehlende JSON-Datei darf die Startseite nicht mitreissen.
    """
    try:
        with pfad.open(encoding="utf-8") as datei:
            daten = json.load(datei)
    except FileNotFoundError:
        logger.warning("%s nicht gefunden", pfad.name)
        return []
    except (json.JSONDecodeError, OSError) as fehler:
        logger.warning("%s unlesbar: %s", pfad.name, fehler)
        return []

    if not isinstance(daten, list):
        logger.warning("%s enthaelt kein JSON-Array", pfad.name)
        return []

    return [e for e in daten if isinstance(e, dict) and e.get("titel")]


def get_filme():
    """Kuratierte Kinofilme. Jeder Eintrag bekommt gattung="film"."""
    filme = _lade(DATEI)
    for film in filme:
        film.setdefault("gattung", "film")
    return filme


def get_serien():
    """Serien und Anime. `gattung` steht bereits in den Daten."""
    return [e for e in _lade(DATEI_SERIEN) if e.get("gattung") in ("serie", "anime")]


def get_gattungen(eintraege):
    """Nur die Gattungen, die auch wirklich vorkommen."""
    vorhanden = {e.get("gattung") for e in eintraege}
    return [(wert, label) for wert, label in GATTUNGEN if wert in vorhanden]


def get_stimmungen(filme):
    """Nur die Stimmungen, die auch wirklich vorkommen.

    Verhindert Filter-Buttons, die auf eine leere Liste filtern.
    """
    vorhanden = {film.get("stimmung") for film in filme}
    return [(wert, label) for wert, label in STIMMUNGEN if wert in vorhanden]
