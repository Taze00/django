# -*- coding: utf-8 -*-
"""Welchen Spieler als naechsten abrufen - nach Datenluecken, nicht nach Rang.

Ausgangspunkt ist eine Beobachtung: von JEDEM bekannten Spieler wissen
wir bereits, welche Brawler er gespielt hat - er steht ja mit Tag in den
importierten Partien (`MatchPlayer.player_tag`). Die Auswahl muss deshalb
nicht blind sein.

    Prioritaet(Spieler) = Summe der Defizite, die seine Historie beruehrt

Ein Defizit ist, was einer Einheit (Brawler global, Brawler je Modus,
Counter-Paar, Synergie-Paar) bis zur Zielstichprobe fehlt, auf 0-1
normiert:

    defizit = max(0, ziel - n) / ziel

**Ein Defizit ist eine Reihenfolge, keine Aussage ueber Qualitaet.** Dass
Cosmo ein Defizit von 1,0 hat, heisst "dort fehlt alles" - nicht, dass
irgendeine Zahl ueber Cosmo dadurch belastbarer wuerde. Die
Confidence-Stufen der Engine bleiben unberuehrt.

Drei Leitplanken:

1. **Kappung je Kategorie** (`PRIORITAET_MAX_BEITRAEGE`): nur die groessten
   Beitraege zaehlen. Sonst gewaenne, wer die laengste Historie hat -
   also der Vielspieler mit den haeufigsten Brawlern, genau das Gegenteil
   des Ziels.
2. **Map-Ebene mit Gewicht 0**: 1474 Map-Zeilen mit Median 5 Partien sind
   zu duenn, um eine Auswahl zu steuern. Abschaltbar ueber die Config,
   nicht im Code verdrahtet.
3. **Rang nur als Gleichstandsentscheid**: die API kennt keine
   Ranked-Rangliste, Trophaeen sagen ueber Ranked-Niveau wenig.

Dieses Modul ruft NIE die API. Es liest, was schon importiert ist.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations

from drafter import config
from drafter.models import Brawler
from drafter.models.collector import TrackedPlayer
from drafter.models.matches import Match, MatchPlayer


def _ziel(key):
    return max(1, int(config.PRIORITAET_ZIELE.get(key, 1)))


def defizit(n, key):
    """0-1: wie viel der Zielstichprobe dieser Einheit noch fehlt."""
    ziel = _ziel(key)
    return max(0.0, (ziel - n) / ziel)


@dataclass
class Beitrag:
    """Ein Grund, diesen Spieler zu holen - mit seinem Anteil am Score."""

    kategorie: str
    bezeichnung: str
    n: int
    defizit: float
    punkte: float

    def __str__(self):
        return f"{self.bezeichnung} ({self.n} Spiele, +{self.punkte:.2f})"


@dataclass
class Spielerbewertung:
    tag: str
    punkte: float = 0.0
    beitraege: list = field(default_factory=list)
    seltene_brawler: list = field(default_factory=list)
    katalog_brawler: list = field(default_factory=list)
    trophaeen: int = None
    rang: int = None
    partien: int = 0

    def gruende(self, anzahl=3):
        return sorted(self.beitraege, key=lambda b: -b.punkte)[:anzahl]

    def punkte_je_kategorie(self):
        je = Counter()
        for b in self.beitraege:
            je[b.kategorie] += b.punkte
        return dict(je)


class Datenluecken:
    """Stichproben und Defizite aller Einheiten - einmal gelesen.

    Gezaehlt wird genau das, was auch die Aggregation zaehlt: soloRanked,
    ohne Konflikt, mit bekanntem Ergebnis. Trophaeen-, Turnier-,
    Challenge- und Friendly-Partien bleiben draussen.
    """

    def __init__(self):
        self.brawler_namen = {}
        self.modus_namen = {}
        self.brawler_global = Counter()
        self.brawler_modus = Counter()      # (modus, brawler) -> n
        self.counter = Counter()            # (a, b) sortiert -> n
        self.synergie = Counter()           # (a, b) sortiert -> n
        self.spieler_brawler = defaultdict(Counter)    # tag -> {brawler: n}
        self.spieler_modus = defaultdict(set)          # tag -> {(modus, brawler)}
        self.spieler_counter = defaultdict(set)        # tag -> {(a, b)}
        self.spieler_synergie = defaultdict(set)
        self.spieler_partien = Counter()
        self._laden()

    def _laden(self):
        zaehlbar = Match.objects.filter(
            battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN, has_conflict=False,
        ).exclude(winner_side="")
        for b in Brawler.objects.all():
            self.brawler_namen[b.id] = b.name
        # Nicht ranked-waehlbare Brawler erzeugen kein Defizit: ihre Null
        # ist kein Mangel an Daten, sondern die Abwesenheit des Brawlers.
        self.ausgeschlossen = {
            b.id for b in Brawler.objects.filter(ranked_verfuegbar=False)
        }
        from drafter.models import GameMode
        for m in GameMode.objects.all():
            self.modus_namen[m.id] = m.name

        felder = ("match_id", "match__game_mode_id", "match__mode_name",
                  "side", "player_tag", "brawler_id", "brawler_name")
        partien = defaultdict(lambda: {"modus": None, "teams": defaultdict(list)})
        for zeile in MatchPlayer.objects.filter(match__in=zaehlbar).values_list(*felder):
            mid, modus_id, modus_name, seite, tag, brawler_id, brawler_name = zeile
            schluessel = brawler_id or brawler_name
            eintrag = partien[mid]
            eintrag["modus"] = modus_id or modus_name
            eintrag["teams"][seite].append((schluessel, tag))
            self.brawler_namen.setdefault(schluessel, brawler_name)

        for eintrag in partien.values():
            modus = eintrag["modus"]
            seiten = list(eintrag["teams"].values())
            for seite in seiten:
                for schluessel, tag in seite:
                    self.brawler_global[schluessel] += 1
                    self.brawler_modus[(modus, schluessel)] += 1
                    if tag:
                        self.spieler_brawler[tag][schluessel] += 1
                        self.spieler_modus[tag].add((modus, schluessel))
                        self.spieler_partien[tag] += 1
                # Synergie: Paare innerhalb einer Seite.
                for (a, tag_a), (b, tag_b) in combinations(sorted(seite, key=lambda p: str(p[0])), 2):
                    if a == b:
                        continue
                    paar = (a, b)
                    self.synergie[paar] += 1
                    for tag in (tag_a, tag_b):
                        if tag:
                            self.spieler_synergie[tag].add(paar)
            # Counter: Paare ueber die Seiten hinweg.
            if len(seiten) == 2:
                for a, tag_a in seiten[0]:
                    for b, tag_b in seiten[1]:
                        if a == b:
                            continue
                        paar = tuple(sorted((a, b), key=str))
                        self.counter[paar] += 1
                        for tag in (tag_a, tag_b):
                            if tag:
                                self.spieler_counter[tag].add(paar)

    # --- Abfragen -------------------------------------------------------
    def name(self, schluessel):
        return self.brawler_namen.get(schluessel, str(schluessel))

    def modus_name(self, schluessel):
        return self.modus_namen.get(schluessel, str(schluessel))

    def paar_name(self, paar):
        return f"{self.name(paar[0])} / {self.name(paar[1])}"

    def seltene_brawler(self, grenze=None):
        """Brawler unterhalb der Zielstichprobe - nach Defizit sortiert."""
        grenze = _ziel("brawler_global") if grenze is None else grenze
        alle = (set(self.brawler_namen) | set(self.brawler_global)) - self.ausgeschlossen
        return sorted(
            (b for b in alle if self.brawler_global.get(b, 0) < grenze),
            key=lambda b: self.brawler_global.get(b, 0),
        )


def katalog_brawler_ids(raum=None):
    """Brawler der Stufe "katalog" - ohne Profil und ohne belastbare Messung.

    Sie bekommen den groessten Zuschlag: dort fehlt nicht eine Zahl,
    sondern jede. Die Stufe kommt aus dem Datenraum, damit hier keine
    zweite Definition entsteht.
    """
    if raum is None:
        from drafter.services.daten import Datenraum
        raum = Datenraum().laden()
    return {b.id for b in raum.brawler if raum.stufe(b) == "katalog"}


class Priorisierung:
    """Bewertet Spieler nach den Luecken, die ihre Historie beruehrt."""

    def __init__(self, luecken=None, katalog_ids=None, gewichte=None, kappung=None):
        self.luecken = luecken or Datenluecken()
        self.katalog_ids = katalog_ids if katalog_ids is not None else katalog_brawler_ids()
        self.gewichte = {**config.PRIORITAET_GEWICHTE, **(gewichte or {})}
        self.kappung = {**config.PRIORITAET_MAX_BEITRAEGE, **(kappung or {})}

    def _begrenzt(self, beitraege, kategorie):
        """Nur die groessten Beitraege einer Kategorie zaehlen."""
        grenze = self.kappung.get(kategorie)
        sortiert = sorted(beitraege, key=lambda b: -b.punkte)
        return sortiert[:grenze] if grenze else sortiert

    def bewerte(self, spieler):
        """Ein TrackedPlayer -> Spielerbewertung."""
        tag = spieler.tag
        luecken = self.luecken
        bewertung = Spielerbewertung(
            tag=tag, trophaeen=spieler.ranking_trophies, rang=spieler.ranking_position,
            partien=luecken.spieler_partien.get(tag, 0),
        )

        gesammelt = []

        # 1. Brawler global - der Hauptgrund.
        einzeln = []
        for brawler in luecken.spieler_brawler.get(tag, {}):
            if brawler in luecken.ausgeschlossen:
                continue
            n = luecken.brawler_global.get(brawler, 0)
            d = defizit(n, "brawler_global")
            if d <= 0:
                continue
            punkte = d * self.gewichte["brawler_global"]
            if brawler in self.katalog_ids:
                punkte += d * self.gewichte["katalog_bonus"]
                bewertung.katalog_brawler.append(luecken.name(brawler))
            einzeln.append(Beitrag("brawler_global", luecken.name(brawler), n, d, punkte))
            bewertung.seltene_brawler.append(luecken.name(brawler))
        gesammelt += self._begrenzt(einzeln, "brawler_global")

        # 2. Brawler je Modus.
        einzeln = []
        for modus, brawler in luecken.spieler_modus.get(tag, ()):
            if brawler in luecken.ausgeschlossen:
                continue
            n = luecken.brawler_modus.get((modus, brawler), 0)
            d = defizit(n, "brawler_modus")
            if d <= 0:
                continue
            einzeln.append(Beitrag(
                "brawler_modus", f"{luecken.name(brawler)} in {luecken.modus_name(modus)}", n, d,
                d * self.gewichte["brawler_modus"],
            ))
        gesammelt += self._begrenzt(einzeln, "brawler_modus")

        # 3. und 4. Paare - kleiner Zuschlag, stark gekappt.
        for kategorie, quelle, zaehler in (
            ("counter", luecken.spieler_counter, luecken.counter),
            ("synergie", luecken.spieler_synergie, luecken.synergie),
        ):
            einzeln = []
            for paar in quelle.get(tag, ()):
                n = zaehler.get(paar, 0)
                d = defizit(n, kategorie)
                if d <= 0:
                    continue
                einzeln.append(Beitrag(
                    kategorie, luecken.paar_name(paar), n, d, d * self.gewichte[kategorie],
                ))
            gesammelt += self._begrenzt(einzeln, kategorie)

        bewertung.beitraege = gesammelt
        bewertung.punkte = sum(b.punkte for b in gesammelt) + self._rang_bonus(spieler)
        bewertung.seltene_brawler = sorted(set(bewertung.seltene_brawler))
        bewertung.katalog_brawler = sorted(set(bewertung.katalog_brawler))
        return bewertung

    def _rang_bonus(self, spieler):
        """Gleichstandsentscheid: bekannter Ranglistenplatz, sehr klein."""
        if not spieler.ranking_position:
            return 0.0
        anteil = max(0.0, 1.0 - (spieler.ranking_position - 1) / 200.0)
        return anteil * self.gewichte["rang"]

    # --- Listen ---------------------------------------------------------
    def offene_spieler(self):
        """Nur nie abgefragte, aktive Spieler - die Schutzregel des Kommandos."""
        return TrackedPlayer.objects.filter(is_active=True, last_fetched_at__isnull=True)

    def rangliste(self, spieler=None, anzahl=100):
        spieler = self.offene_spieler() if spieler is None else spieler
        bewertet = [self.bewerte(s) for s in spieler]
        bewertet.sort(key=lambda b: (-b.punkte, b.tag))
        return bewertet[:anzahl] if anzahl else bewertet

    def fuer_brawler(self, brawler, anzahl=100):
        """Offene Spieler, die diesen Brawler nachweislich gespielt haben."""
        schluessel = brawler.id
        passend = [
            s for s in self.offene_spieler()
            if schluessel in self.luecken.spieler_brawler.get(s.tag, {})
        ]
        return self.rangliste(passend, anzahl=anzahl)
