# -*- coding: utf-8 -*-
"""Statistiken als feste Liste im Speicher.

Drei Einsatzzwecke, alle ohne Datenbankzugriff auf Stat-Tabellen:

1. **Tests** - der Beweis, dass die Engine nicht an der Datenbank haengt:
   dieselben Datensaetze aus einem anderen Provider muessen dieselben
   Empfehlungen ergeben.
2. **Backtesting** (spaeter) - "was haette das System mit den Statistiken
   von damals empfohlen?" braucht eingefrorene Statistiken, nicht die
   heutigen Tabellen.
3. **Was-waere-wenn** - Statistiken gezielt veraendern und die Wirkung
   auf die Empfehlung ansehen, ohne Produktivdaten anzufassen.
"""

from drafter.services.providers.basis import StatProvider
from drafter.services.providers.records import (
    ART_BRAWLER, ART_BUILD, ART_COUNTER, ART_SYNERGY, ProviderStatus, StatAnfrage,
)


class SnapshotStatProvider(StatProvider):
    name = "snapshot"

    def __init__(self, records, name=None, modus_records=()):
        self._records = list(records)
        self._modus = list(modus_records)
        if name:
            self.name = name

    @classmethod
    def von(cls, provider, anfrage=None, name=None):
        """Momentaufnahme eines anderen Providers."""
        anfrage = anfrage or StatAnfrage()
        records = (
            provider.brawler_stats(anfrage)
            + provider.counter_stats(anfrage)
            + provider.synergy_stats(anfrage)
            + provider.build_stats(anfrage)
        )
        # Modus-Zeilen anderer Modi getrennt merken: sie wuerden vom
        # Kontextfilter verworfen, werden aber fuer den Modusvergleich
        # gebraucht.
        modus = [r for r in provider.modus_stats(anfrage)]
        eigen = cls(records, name=name or f"snapshot:{provider.name}")
        eigen._modus = modus
        return eigen

    def modus_stats(self, anfrage):
        if not anfrage.brawler_ids:
            return list(self._modus)
        return [r for r in self._modus if r.brawler_id in anfrage.brawler_ids]

    def status(self):
        if self._records:
            return ProviderStatus.bereit()
        return ProviderStatus.nicht_verfuegbar("Momentaufnahme ist leer")

    def _filter(self, art, anfrage):
        ergebnis = []
        for r in self._records:
            if r.art != art:
                continue
            if anfrage.brawler_ids and r.brawler_id not in anfrage.brawler_ids:
                continue
            if r.game_mode_id is not None and r.game_mode_id != anfrage.game_mode_id:
                continue
            if r.brawl_map_id is not None and r.brawl_map_id != anfrage.brawl_map_id:
                continue
            ergebnis.append(r)
        return ergebnis

    def brawler_stats(self, anfrage):
        return self._filter(ART_BRAWLER, anfrage)

    def counter_stats(self, anfrage):
        return self._filter(ART_COUNTER, anfrage)

    def synergy_stats(self, anfrage):
        return self._filter(ART_SYNERGY, anfrage)

    def build_stats(self, anfrage):
        return self._filter(ART_BUILD, anfrage)
