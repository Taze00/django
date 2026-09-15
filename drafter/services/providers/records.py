# -*- coding: utf-8 -*-
"""Die Datensaetze, die zwischen Providern und dem Rest der App wandern.

Warum eigene Klassen statt Model-Zeilen: sobald die Engine ein
`CounterStat`-Objekt in der Hand haelt, haengt sie an der Datenbank - an
ihren Feldnamen, ihren Fremdschluesseln, ihrem Lazy Loading. Ein
Provider, der Zahlen aus einer JSON-Datei oder direkt aus einem Modell
liefert, muesste dann so tun, als waere er eine Tabelle.

Mit diesen Datensaetzen ist die Richtung umgekehrt: jeder Provider
liefert `StatRecord`s, und woher sie stammen, sieht man nur noch am
Feld `source`. Die Attributnamen entsprechen bewusst den Modellfeldern -
so kann derselbe Code eine Zeile oder einen Datensatz lesen, und die
Umstellung hat keine Komponente veraendert.
"""

from dataclasses import dataclass, field, replace
from datetime import date, datetime

from drafter.models.base import NICHT_GEMESSEN


# =========================================================================
# Status
# =========================================================================

@dataclass(frozen=True)
class ProviderStatus:
    """Kann ein Provider gerade liefern - und wenn nicht, warum nicht.

    Ein fehlender API-Key ist kein Absturz, sondern ein Zustand. Der
    Aufrufer bekommt ihn als Wert mit Begruendung und entscheidet selbst,
    ob er auf eine andere Quelle ausweicht.
    """

    verfuegbar: bool
    grund: str = ""

    @classmethod
    def bereit(cls, grund=""):
        return cls(True, grund)

    @classmethod
    def nicht_verfuegbar(cls, grund):
        return cls(False, grund)

    def __bool__(self):
        return self.verfuegbar


# =========================================================================
# Statistiken - das Einzige, was die Engine zu sehen bekommt
# =========================================================================

ART_BRAWLER = "brawler"
ART_COUNTER = "counter"
ART_SYNERGY = "synergy"
ART_BUILD = "build"


@dataclass(frozen=True)
class StatAnfrage:
    """Wofuer Statistiken gebraucht werden.

    Provider duerfen damit vorfiltern (eine Map-Statistik fuer eine
    andere Map ist wertlos), muessen es aber nicht - die endgueltige
    Auswahl der passendsten Zeile trifft der Datenraum.
    """

    brawler_ids: frozenset = frozenset()
    game_mode_id: int = None
    brawl_map_id: int = None
    rank_pool: str = ""


@dataclass(frozen=True)
class StatRecord:
    """Eine voraggregierte Statistik mit vollem Kontext.

    Jede Aussage traegt mit, WORAUF sie beruht: Stichprobe (games, wins,
    sample_size), Raten (roh und geglaettet), Zeitraum, Patch, Rangbereich
    und Quelle. Eine Zahl ohne diesen Kontext waere nicht pruefbar.
    """

    art: str
    brawler_id: int
    # Gegner (Counter) oder zweiter Brawler (Synergie).
    partner_id: int = None
    # Nur bei Builds.
    item_kind: str = ""
    item_slug: str = ""
    item_id: int = None

    # Kontext
    game_mode_id: int = None
    brawl_map_id: int = None
    patch_id: int = None
    patch: object = None
    rank_pool: str = ""
    window_label: str = ""
    window_start: date = None
    window_end: date = None

    # Stichprobe
    games: int = 0
    wins: int = 0
    sample_size: float = 0.0
    raw_rate: float = None
    adjusted_rate: float = None

    # Abgeleitete Groessen je Art
    advantage: float = 0.0      # Counter, Build
    synergy: float = 0.0        # Synergie
    pick_rate: float = 0.0      # Brawler
    ban_rate: float = 0.0       # Brawler

    confidence: float = 0.0
    source: str = "demo"
    reason: str = ""

    # --- Auswertung -----------------------------------------------------
    @property
    def ist_gemessen(self):
        return self.source not in NICHT_GEMESSEN

    @property
    def is_demo(self):
        """Nicht gemessen. Gleiche Bedeutung wie StatBasis.is_demo."""
        return not self.ist_gemessen

    @property
    def staerke(self):
        """Geglaettete Rate als Abweichung von 50 % in [-1, +1]."""
        rate = self.adjusted_rate if self.adjusted_rate is not None else 0.5
        return max(-1.0, min(1.0, (rate - 0.5) * 2))

    @property
    def paar_schluessel(self):
        if self.art == ART_SYNERGY and self.partner_id is not None:
            return tuple(sorted((self.brawler_id, self.partner_id)))
        return (self.brawler_id, self.partner_id)

    def mit(self, **aenderungen):
        return replace(self, **aenderungen)

    # --- Aus Modellzeilen -----------------------------------------------
    @classmethod
    def aus_model(cls, zeile):
        """Eine Stat-Tabellenzeile in einen Datensatz uebersetzen.

        Die einzige Stelle, an der Modell und Datensatz sich beruehren.
        """
        from drafter.models import BrawlerStat, BuildStat, CounterStat, SynergyStat

        # Typ ZUERST pruefen: sonst scheitert ein falsches Objekt am ersten
        # fehlenden Feld mit einem AttributeError, der nichts ueber die
        # eigentliche Ursache sagt.
        if not isinstance(zeile, (BrawlerStat, CounterStat, SynergyStat, BuildStat)):
            raise TypeError(f"Keine Statistikzeile: {type(zeile).__name__}")

        gemeinsam = dict(
            game_mode_id=zeile.game_mode_id,
            brawl_map_id=zeile.brawl_map_id,
            patch_id=zeile.patch_id,
            patch=zeile.patch if zeile.patch_id else None,
            rank_pool=zeile.rank_pool,
            window_label=zeile.window_label,
            window_start=zeile.window_start,
            window_end=zeile.window_end,
            games=zeile.games,
            wins=zeile.wins,
            sample_size=zeile.sample_size,
            raw_rate=zeile.raw_rate,
            adjusted_rate=zeile.adjusted_rate,
            confidence=zeile.confidence,
            source=zeile.source,
        )
        if isinstance(zeile, BrawlerStat):
            return cls(art=ART_BRAWLER, brawler_id=zeile.brawler_id,
                       pick_rate=zeile.pick_rate, ban_rate=zeile.ban_rate, **gemeinsam)
        if isinstance(zeile, CounterStat):
            return cls(art=ART_COUNTER, brawler_id=zeile.brawler_id,
                       partner_id=zeile.enemy_id, advantage=zeile.advantage,
                       reason=zeile.reason, **gemeinsam)
        if isinstance(zeile, SynergyStat):
            return cls(art=ART_SYNERGY, brawler_id=zeile.brawler_a_id,
                       partner_id=zeile.brawler_b_id, synergy=zeile.synergy,
                       reason=zeile.reason, **gemeinsam)
        if isinstance(zeile, BuildStat):
            return cls(art=ART_BUILD, brawler_id=zeile.brawler_id,
                       item_kind=zeile.item_kind, item_slug=zeile.item_slug,
                       item_id=zeile.item_id, advantage=zeile.advantage, **gemeinsam)
        raise TypeError(f"Keine Statistikzeile: {type(zeile).__name__}")


# =========================================================================
# Matches - nur fuer den Import, nie fuer die Engine
# =========================================================================

@dataclass
class SpielerRecord:
    """Ein Spieler in einem normalisierten Match."""

    brawler: str                      # Slug aus dem eigenen Katalog - oder Rohname
    player_tag: str = ""
    pick_order: int = None            # nur wenn die Quelle sie kennt
    build: dict = None                # {"gadget": slug, "star_power": slug, "gears": [...], "hypercharge": slug}


@dataclass
class MatchRecord:
    """Ein Match in einem quellenunabhaengigen Format.

    `teams` hat genau zwei Seiten, "a" und "b". Die Zuordnung ist
    willkuerlich - der Import kanonisiert sie, damit dasselbe Match aus
    zwei Blickwinkeln (zwei Battlelogs) als dasselbe erkannt wird.

    Felder, die eine Quelle nicht kennt, bleiben None. Das ist die
    wichtigste Regel dieses Formats: fehlende Information wird nicht
    geraten. Ob die offizielle API Pick-Reihenfolge, Bans oder Builds
    liefert, ist ungeprueft - ein Provider, der sie nicht kennt, laesst
    sie leer, und die Aggregation zaehlt sie dann nicht.
    """

    played_at: datetime
    mode: str
    map: str
    teams: dict = field(default_factory=dict)       # {"a": [SpielerRecord], "b": [...]}
    winner: str = None                                # "a" | "b" | "draw" | None
    rank_pool: str = "alle"
    ranked: bool = True
    first_pick: str = None                            # "a" | "b" | None
    bans: list = field(default_factory=list)          # [{"brawler": slug, "side": "a"|None, "order": int|None}]
    duration_seconds: int = None
    external_id: str = None


@dataclass
class Lieferung:
    """Eine Einheit, die ein Match-Provider liefert: eine Datei, eine Antwort.

    Traegt die Rohdaten UNVERAENDERT mit. Sie werden gespeichert, bevor
    irgendetwas daraus gelesen wird - wer spaeter feststellt, dass ein
    Feld falsch interpretiert wurde, kann neu auswerten, ohne die Quelle
    erneut abzufragen.

    `matches` ist None, wenn die Rohdaten (noch) nicht auswertbar sind -
    etwa eine API-Antwort, fuer die es noch keinen geprueften Parser gibt.
    """

    referenz: str
    format: str
    rohdaten: object
    source: str
    matches: list = None
    status: str = "ausgewertet"       # ausgewertet | nicht_unterstuetzt | fehler
    meldung: str = ""
    # Einzelne Matches, die beim Auswerten verworfen wurden - die
    # Lieferung als Ganzes bleibt gueltig. Ob Daten synthetisch sind,
    # steht in `source`, nicht in einem zweiten Flag.
    fehler: list = field(default_factory=list)
