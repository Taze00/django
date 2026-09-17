# -*- coding: utf-8 -*-
"""Welcher Provider gerade gilt - an genau einer Stelle entschieden.

Die Engine fragt nie selbst, ob es gemessene Daten gibt. Sie bekommt
einen StatProvider und rechnet. Diese Datei ist der einzige Ort, an dem
"Demo oder echt?" entschieden wird - und damit der einzige Ort, der sich
aendert, wenn eine neue Quelle dazukommt.
"""

from drafter import config
from drafter.services.providers.datenbank import (
    gemessen_mit_prior_provider, gemessener_provider, synthetischer_provider,
)
from drafter.services.providers.demo import DemoDataProvider

STAT_PROVIDER_NAMEN = ("auto", "demo", "gemessen", "synthetisch")
MATCH_PROVIDER_NAMEN = ("fixture", "api")


def hole_stat_provider(name=None):
    """Der StatProvider fuer die Engine.

    "auto" nimmt gemessene Statistiken, sobald es welche gibt UND sie
    freigegeben sind (config.GEMESSENE_STATS_FREIGEGEBEN), sonst die
    Demo-Daten. Synthetische Daten waehlt "auto" NIE - sie existieren,
    um die Pipeline zu testen, und duerfen nicht unbemerkt als Messung
    auf der Seite erscheinen.

    Umgeschaltet wird ganz, nicht zeilenweise: gibt es gemessene Daten,
    gelten nur diese. Fehlt fuer einen Brawler eine Messung, faellt die
    Engine auf ihre Heuristik zurueck (und sagt das) - statt eine
    ausgedachte Demo-Zahl neben echte zu stellen.
    """
    name = (name or config.STAT_PROVIDER or "auto").lower()
    if name == "demo":
        return DemoDataProvider()
    if name == "gemessen":
        return gemessener_provider()
    if name == "synthetisch":
        return synthetischer_provider()
    if name == "auto":
        # Die Freigabe ist der Schalter zwischen "aggregiert" und
        # "produktiv". Ohne sie bleibt die Seite bei Demo, auch wenn
        # bereits gemessene Zeilen in der Datenbank stehen: erste echte
        # Aggregationen sind klein und gehoeren zuerst in den
        # Vergleichsbericht, nicht auf die Seite.
        if not config.GEMESSENE_STATS_FREIGEGEBEN:
            return DemoDataProvider()
        gemessen = gemessen_mit_prior_provider()
        return gemessen if gemessen.status().verfuegbar else DemoDataProvider()
    raise ValueError(
        f"Unbekannter StatProvider '{name}'. Erlaubt: {', '.join(STAT_PROVIDER_NAMEN)}"
    )


def hole_match_provider(name, **optionen):
    """Ein MatchProvider fuer den Import.

        hole_match_provider("fixture", pfade=["data/brawl_api_raw"])
        hole_match_provider("api", spieler_tags=["#2ABC"])
    """
    name = (name or "").lower()
    if name == "fixture":
        from drafter.services.providers.fixture import FixtureDataProvider
        return FixtureDataProvider(optionen.get("pfade") or [config.FIXTURE_VERZEICHNIS])
    if name == "api":
        from drafter.services.providers.official_api import OfficialBrawlAPIProvider
        return OfficialBrawlAPIProvider(spieler_tags=optionen.get("spieler_tags", ()))
    raise ValueError(
        f"Unbekannter MatchProvider '{name}'. Erlaubt: {', '.join(MATCH_PROVIDER_NAMEN)}"
    )
