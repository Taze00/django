"""Laedt die handgepflegten Filmempfehlungen aus films/data/filme.json."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATEI = Path(__file__).resolve().parent / "data" / "filme.json"

# Reihenfolge bestimmt auch die Reihenfolge der Filter-Buttons.
STIMMUNGEN = [
    ("mitnehmen", "Mitnehmen"),
    ("nachdenken", "Nachdenken"),
    ("nebenbei", "Nebenbei"),
    ("geheimtipp", "Geheimtipp"),
]


def get_filme():
    """Liste der kuratierten Filme. Bei Problemen leer.

    Wie beim RSS gilt: die Sektion ist Beiwerk. Eine kaputte oder
    fehlende JSON-Datei darf die Startseite nicht mitreissen.
    """
    try:
        with DATEI.open(encoding="utf-8") as datei:
            daten = json.load(datei)
    except FileNotFoundError:
        logger.warning("filme.json nicht gefunden: %s", DATEI)
        return []
    except (json.JSONDecodeError, OSError) as fehler:
        logger.warning("filme.json unlesbar: %s", fehler)
        return []

    if not isinstance(daten, list):
        logger.warning("filme.json enthaelt kein JSON-Array")
        return []

    return [film for film in daten if isinstance(film, dict) and film.get("titel")]


def get_stimmungen(filme):
    """Nur die Stimmungen, die auch wirklich vorkommen.

    Verhindert Filter-Buttons, die auf eine leere Liste filtern.
    """
    vorhanden = {film.get("stimmung") for film in filme}
    return [(wert, label) for wert, label in STIMMUNGEN if wert in vorhanden]
