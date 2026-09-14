"""Datenraum: alle Statistiken eines Drafts in wenigen Abfragen.

Das Problem, das diese Datei loest: eine Empfehlung bewertet rund
zwanzig Kandidaten gegen bis zu drei Gegner und drei Mitspieler. Naiv
sind das hunderte Einzelabfragen - bei jedem Klick. Der Datenraum holt
stattdessen einmal alles Noetige und beantwortet danach jede Frage aus
dem Speicher.

Zweite Aufgabe: **Kontext-Spezifitaet**. Zu einem Paar kann es mehrere
Zeilen geben - eine fuer diese Map, eine fuer den Modus, eine
allgemeine. Die spezifischste gewinnt, denn "Gale gegen Buster auf
dieser engen Map" ist eine bessere Auskunft als "Gale gegen Buster
allgemein". Diese Aufloesung steht genau hier und nicht in fuenf
Komponenten verteilt.
"""

from drafter.models import Brawler, BrawlerStat, CounterStat, SynergyStat


def _spezifitaet(zeile, brawl_map, game_mode, rank_pool):
    """Wie gut passt eine Statistikzeile auf den aktuellen Draft?

    Hoeher ist besser. Eine Zeile fuer eine *andere* Map oder einen
    *anderen* Modus ist nicht schwach passend, sondern falsch - sie
    bekommt -1 und wird verworfen.
    """
    punkte = 0.0

    if zeile.brawl_map_id:
        if not brawl_map or zeile.brawl_map_id != brawl_map.id:
            return -1.0
        punkte += 4.0
    if zeile.game_mode_id:
        if not game_mode or zeile.game_mode_id != game_mode.id:
            return -1.0
        punkte += 2.0
    if zeile.rank_pool and rank_pool and zeile.rank_pool == rank_pool:
        punkte += 0.5
    # Mehr Spiele entscheiden bei sonst gleicher Passung.
    punkte += min(0.4, zeile.games / 100000.0)
    return punkte


class Datenraum:
    """Vorgeladene Statistiken fuer genau einen Draft-Kontext."""

    def __init__(self, brawl_map=None, game_mode=None, patch=None, rank_pool=None):
        self.brawl_map = brawl_map
        self.game_mode = game_mode or (brawl_map.game_mode if brawl_map else None)
        self.patch = patch
        self.rank_pool = rank_pool

        self.brawler = []
        self._nach_id = {}
        self._counter = {}    # (brawler_id, enemy_id) -> CounterStat
        self._synergie = {}   # (kleinere_id, groessere_id) -> SynergyStat
        self._stat = {}       # brawler_id -> BrawlerStat
        self._geladen = False

    # --- Laden ----------------------------------------------------------
    def laden(self):
        """Ein Aufruf, vier Abfragen. Danach faellt kein Query mehr an."""
        if self._geladen:
            return self

        # Balanceaenderungen gleich mitladen: die Meta-Komponente fragt
        # fuer JEDEN Kandidaten, ob er seit der Messung veraendert wurde
        # (services/patch_weighting.py). Ohne prefetch ist das eine
        # Abfrage je Brawler - genau die Art N+1, gegen die es diese
        # Klasse gibt. Faellt nur auf, wenn ein Patch gesetzt ist, also
        # ueber die API und nicht im schnellen Direkttest.
        self.brawler = list(
            Brawler.objects.filter(is_active=True)
            .prefetch_related("balance_changes__patch")
        )
        self._nach_id = {b.id: b for b in self.brawler}
        ids = set(self._nach_id)

        # select_related("patch") ist kein Feinschliff, sondern
        # notwendig: die Patchgewichtung liest `stat.patch` fuer JEDEN
        # Kandidaten, und ohne das Mitladen holt Django den Patch je
        # Zeile einzeln nach - zwanzig Abfragen fuer einen einzigen
        # Datensatz, den alle teilen.
        self._counter = self._bestes_je_schluessel(
            CounterStat.objects.filter(
                brawler_id__in=ids, enemy_id__in=ids
            ).select_related("patch"),
            lambda z: (z.brawler_id, z.enemy_id),
        )
        self._synergie = self._bestes_je_schluessel(
            SynergyStat.objects.filter(
                brawler_a_id__in=ids, brawler_b_id__in=ids
            ).select_related("patch"),
            lambda z: (z.brawler_a_id, z.brawler_b_id),
        )
        self._stat = self._bestes_je_schluessel(
            BrawlerStat.objects.filter(brawler_id__in=ids).select_related("patch"),
            lambda z: z.brawler_id,
        )
        self._geladen = True
        return self

    def _bestes_je_schluessel(self, queryset, schluessel):
        """Je Schluessel die passendste Zeile behalten."""
        gewaehlt = {}
        bewertung = {}
        for zeile in queryset:
            punkte = _spezifitaet(zeile, self.brawl_map, self.game_mode, self.rank_pool)
            if punkte < 0:
                continue
            k = schluessel(zeile)
            if punkte > bewertung.get(k, -1):
                gewaehlt[k] = zeile
                bewertung[k] = punkte
        return gewaehlt

    # --- Abfragen -------------------------------------------------------
    def counter(self, brawler, gegner):
        """Gepflegter Vorteil von `brawler` gegen `gegner`, sonst None.

        None heisst ausdruecklich "keine Auskunft" und nicht "kein
        Vorteil" - die Counter-Komponente faellt dann auf ihre
        Heuristik zurueck und kennzeichnet das auch so.
        """
        return self._counter.get((brawler.id, gegner.id))

    def synergie(self, a, b):
        schluessel = (a.id, b.id) if a.id < b.id else (b.id, a.id)
        return self._synergie.get(schluessel)

    def stat(self, brawler):
        return self._stat.get(brawler.id)

    def hat_statistik(self):
        """Gibt es ueberhaupt gemessene Daten - oder laeuft alles auf Demo?"""
        return bool(self._stat or self._counter)

    @property
    def nur_demo(self):
        alle = list(self._stat.values()) + list(self._counter.values()) + list(
            self._synergie.values()
        )
        return all(z.is_demo for z in alle) if alle else True

    def verfuegbare(self, gesperrte_ids):
        return [b for b in self.brawler if b.id not in gesperrte_ids]
