# -*- coding: utf-8 -*-
"""Statistiken aus den Stat-Tabellen - gefiltert nach Quelle.

Die Stat-Tabellen enthalten Zeilen verschiedener Herkunft nebeneinander:
gepflegte Demo-Werte, aus Fixtures aggregierte, spaeter aus der API
aggregierte. Dieser Provider liest genau die Quellen, fuer die er
angelegt wurde - und NIE eine Mischung, die niemand bestellt hat.

Das ist wichtiger, als es aussieht: mischt man stillschweigend gemessene
Counter mit geschaetzten Demo-Countern, steht neben einer Zahl aus
40 000 Matches eine ausgedachte, und beide sehen in der Aufschluesselung
gleich aus.
"""

from django.db.models import Q

from drafter.models import BrawlerStat, BuildStat, CounterStat, Datenquelle, SynergyStat
from drafter.services.providers.basis import StatProvider
from drafter.services.providers.records import ProviderStatus, StatRecord


class DatenbankStatProvider(StatProvider):
    """Liest voraggregierte Zeilen der angegebenen Quellen."""

    name = "datenbank"

    def __init__(self, quellen, name=None):
        self.quellen = tuple(str(q) for q in quellen)
        if name:
            self.name = name

    def status(self):
        vorhanden = (
            BrawlerStat.objects.filter(source__in=self.quellen).exists()
            or CounterStat.objects.filter(source__in=self.quellen).exists()
        )
        if vorhanden:
            return ProviderStatus.bereit()
        labels = ", ".join(self.quellen)
        return ProviderStatus.nicht_verfuegbar(
            f"Keine Statistiken der Quelle(n) {labels} vorhanden"
        )

    # --- Abfragen -------------------------------------------------------
    def _zeilen(self, modell, anfrage, brawler_feld, partner_feld=None):
        """Grundabfrage mit Vorfilter auf Kontext und Quelle.

        Vorgefiltert wird nur, was sicher nicht passt: eine andere Map,
        ein anderer Modus. Die Feinauswahl (Map vor Modus vor allgemein,
        Zeitfenster, Rangbereich) bleibt beim Datenraum, damit sie fuer
        alle Provider identisch ist.
        """
        zeilen = modell.objects.filter(source__in=self.quellen).select_related("patch")
        if anfrage.brawler_ids:
            zeilen = zeilen.filter(**{f"{brawler_feld}__in": anfrage.brawler_ids})
            if partner_feld:
                zeilen = zeilen.filter(**{f"{partner_feld}__in": anfrage.brawler_ids})
        zeilen = zeilen.filter(
            Q(game_mode_id__isnull=True) | Q(game_mode_id=anfrage.game_mode_id)
        ).filter(
            Q(brawl_map_id__isnull=True) | Q(brawl_map_id=anfrage.brawl_map_id)
        )
        return [StatRecord.aus_model(z) for z in zeilen]

    def brawler_stats(self, anfrage):
        return self._zeilen(BrawlerStat, anfrage, "brawler_id")

    def counter_stats(self, anfrage):
        return self._zeilen(CounterStat, anfrage, "brawler_id", "enemy_id")

    def synergy_stats(self, anfrage):
        return self._zeilen(SynergyStat, anfrage, "brawler_a_id", "brawler_b_id")

    def build_stats(self, anfrage):
        return self._zeilen(BuildStat, anfrage, "brawler_id")

    def modus_stats(self, anfrage):
        """Alle Modus-Zeilen, unabhaengig vom gefragten Modus."""
        zeilen = (BrawlerStat.objects
                  .filter(source__in=self.quellen,
                          brawl_map__isnull=True, game_mode__isnull=False)
                  .select_related("patch"))
        if anfrage.brawler_ids:
            zeilen = zeilen.filter(brawler_id__in=anfrage.brawler_ids)
        return [StatRecord.aus_model(z) for z in zeilen]


class OverlayStatProvider(StatProvider):
    """Gemessene Werte bevorzugen, gepflegte Werte je Schluessel behalten."""

    name = "gemessen"

    def __init__(self, gemessen, prior):
        self.gemessen = gemessen
        self.prior = prior

    def status(self):
        return self.gemessen.status()

    def _overlay(self, gemessen, prior, schluessel):
        zeilen = {schluessel(record): record for record in prior}
        for record in gemessen:
            if record.games > 0:
                zeilen[schluessel(record)] = record
        return list(zeilen.values())

    def brawler_stats(self, anfrage):
        return self._overlay(self.gemessen.brawler_stats(anfrage), self.prior.brawler_stats(anfrage),
                             lambda r: (r.brawler_id, r.game_mode_id, r.brawl_map_id,
                                        r.rank_pool, r.window_label))

    def counter_stats(self, anfrage):
        return self._overlay(self.gemessen.counter_stats(anfrage), self.prior.counter_stats(anfrage),
                             lambda r: (r.brawler_id, r.partner_id, r.game_mode_id,
                                        r.brawl_map_id, r.rank_pool, r.window_label))

    def modus_stats(self, anfrage):
        # Nur die gemessene Seite: die Frage "laeuft er ueberall aehnlich"
        # ist eine Messfrage, ein gepflegter Prior beantwortet sie nicht.
        return self.gemessen.modus_stats(anfrage)

    def synergy_stats(self, anfrage):
        return self._overlay(self.gemessen.synergy_stats(anfrage), self.prior.synergy_stats(anfrage),
                             lambda r: (r.brawler_id, r.partner_id, r.game_mode_id,
                                        r.brawl_map_id, r.rank_pool, r.window_label))

    def build_stats(self, anfrage):
        return self._overlay(self.gemessen.build_stats(anfrage), self.prior.build_stats(anfrage),
                             lambda r: (r.brawler_id, r.item_kind, r.item_slug,
                                        r.game_mode_id, r.brawl_map_id, r.rank_pool,
                                        r.window_label))


# Quellen, deren Zeilen aus echten Matches aggregiert wurden. SYNTHETIC
# fehlt hier mit Absicht: synthetische Fixtures testen die Pipeline und
# duerfen nie automatisch als Messung auf der Seite landen.
GEMESSENE_QUELLEN = (Datenquelle.FIXTURE, Datenquelle.API, Datenquelle.AGGREGATED)


def gemessener_provider():
    return DatenbankStatProvider(GEMESSENE_QUELLEN, name="gemessen")


def gemessen_mit_prior_provider():
    return OverlayStatProvider(gemessener_provider(), DatenbankStatProvider(
        (Datenquelle.DEMO, Datenquelle.MANUAL), name="prior"
    ))


def synthetischer_provider():
    return DatenbankStatProvider((Datenquelle.SYNTHETIC,), name="synthetisch")
