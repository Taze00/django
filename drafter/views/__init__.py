"""Views des Drafters - aufgeteilt nach Seiten und Schnittstelle."""

from drafter.views.api import (
    confidence_speichern, detail, empfehlen, endanalyse, katalog,
)
from drafter.views.pages import draft, meine_brawler

__all__ = [
    "draft", "meine_brawler",
    "katalog", "empfehlen", "endanalyse", "detail", "confidence_speichern",
]
