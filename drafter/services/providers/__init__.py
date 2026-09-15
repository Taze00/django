# -*- coding: utf-8 -*-
"""Datenquellen hinter austauschbaren Schnittstellen.

Dieses Paket exportiert bewusst nur die Schnittstellen und Datensaetze.
Die konkreten Provider werden aus ihren Modulen importiert:

    from drafter.services.providers.demo import DemoDataProvider
    from drafter.services.providers.fixture import FixtureDataProvider
    from drafter.services.providers.official_api import OfficialBrawlAPIProvider
    from drafter.services.providers.registry import hole_stat_provider

Grund: der Fixture-Provider braucht den Parser, und der Parser braucht
die Datensaetze aus diesem Paket. Wuerde diese Datei alle Provider
eifrig importieren, entstuende daraus ein Importzirkel, der je nach
Importreihenfolge mal auftritt und mal nicht.
"""

from drafter.services.providers.basis import DataProvider, MatchProvider, StatProvider
from drafter.services.providers.records import (
    Lieferung, MatchRecord, ProviderStatus, SpielerRecord, StatAnfrage, StatRecord,
)

__all__ = [
    "DataProvider", "MatchProvider", "StatProvider",
    "Lieferung", "MatchRecord", "ProviderStatus", "SpielerRecord",
    "StatAnfrage", "StatRecord",
]
