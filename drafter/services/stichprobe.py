# -*- coding: utf-8 -*-
"""Breite High-Rank-Stichprobe - ohne Auswahl nach Brawler.

Gegenstueck zu services/prioritaet.py. Die Luecken-Strategie sucht
gezielt seltene Brawler und ist damit **absichtlich verzerrt**; fuer
Winrates, Meta und Paarstatistiken taugt sie nicht. Diese Auswahl hier
fragt nur zwei Dinge:

    1. Ist fuer den Spieler ein hoher Ranked-Rang BELEGT?
    2. Deckt er eine Partie ab, aus der noch niemand geholt wurde?

Der Rang kommt aus den importierten Partien selbst: in soloRanked-Eintraegen
traegt `brawler.trophies` nicht Trophaeen, sondern den Ranked-Rang
(beobachtet 2026-09-17, Werte 3-22 bei Power 11; Trophaeen-Partien tragen
dort Werte bis 5882). Welche Zahl welcher benannten Stufe entspricht, ist
aus der API NICHT belegt - deshalb rechnet dieses Modul ausschliesslich
numerisch und vergibt keine Namen.

Die Regel "hoechstens ein Kandidat je bereits bekannter Partie" ist der
eigentliche Kern: sechs Spieler derselben Partie liefern sechs Battlelogs
mit derselben Partie darin. Gemessen am Bestand vom 2026-09-18 enthalten
1434 von 2596 Partien mehr als einen offenen Kandidaten.
"""

from collections import defaultdict

from drafter import config
from drafter.models.collector import TrackedPlayer
from drafter.models.matches import Match, MatchPlayer


class HighRankStichprobe:
    """Offene Spieler mit belegtem Rang, gestreut ueber moeglichst viele Partien."""

    def __init__(self, min_rang=None, max_je_partie=None):
        self.min_rang = config.BROAD_MIN_RANG if min_rang is None else int(min_rang)
        self.max_je_partie = (config.BROAD_MAX_JE_PARTIE if max_je_partie is None
                              else int(max_je_partie))
        self.rang = {}                  # tag -> hoechster belegter Rang
        self.partien = defaultdict(set)  # tag -> {match_id}
        self.je_partie = defaultdict(set)  # match_id -> {tag}
        self._laden()

    def _laden(self):
        solo = Match.objects.filter(battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN)
        felder = ("player_tag", "trophies", "match_id", "match__played_at")
        self.gespielt_am = {}
        for tag, rang, match_id, gespielt in MatchPlayer.objects.filter(
            match__in=solo
        ).values_list(*felder):
            if not tag:
                continue
            if rang:
                self.rang[tag] = max(self.rang.get(tag, 0), rang)
            self.partien[tag].add(match_id)
            self.je_partie[match_id].add(tag)
            self.gespielt_am[match_id] = gespielt

    # --- Auswahl --------------------------------------------------------
    def belegte_kandidaten(self, tags=None):
        """Tags mit Rang >= min_rang, hoechster Rang zuerst."""
        auswahl = (
            (tag, rang) for tag, rang in self.rang.items()
            if rang >= self.min_rang and (tags is None or tag in tags)
        )
        return sorted(auswahl, key=lambda p: (-p[1], p[0]))

    def reihenfolge(self, offene_tags=None):
        """Auswahl, die moeglichst viele VERSCHIEDENE Partien abdeckt.

        Greedy ueber den Rang: wer dran ist, belegt seine Partien; weitere
        Spieler aus denselben Partien kommen erst, wenn dort noch Platz
        ist (`max_je_partie`). Wer keine Partie mehr frei hat, faellt ans
        Ende - nicht heraus: sein Battlelog enthaelt auch Partien, die wir
        noch nicht kennen.
        """
        belegt = defaultdict(int)
        vorne, hinten = [], []
        for tag, _rang in self.belegte_kandidaten(offene_tags):
            frei = [m for m in self.partien[tag] if belegt[m] < self.max_je_partie]
            if frei:
                for m in frei:
                    belegt[m] += 1
                vorne.append(tag)
            else:
                hinten.append(tag)
        return vorne + hinten

    # --- Berichtszahlen -------------------------------------------------
    def kennzahlen(self, offene_tags=None):
        kandidaten = self.belegte_kandidaten(offene_tags)
        reihenfolge = self.reihenfolge(offene_tags)
        ohne_ueberschneidung = len(reihenfolge) - sum(
            1 for tag in reihenfolge[len(reihenfolge):]
        )
        abgedeckt = set()
        for tag in reihenfolge:
            abgedeckt |= self.partien[tag]
        return {
            "kandidaten": len(kandidaten),
            "min_rang": self.min_rang,
            "rangverteilung": self._rangverteilung(kandidaten),
            "partien_abgedeckt": len(abgedeckt),
            "ohne_ueberschneidung": ohne_ueberschneidung,
        }

    def _rangverteilung(self, kandidaten):
        verteilung = defaultdict(int)
        for _tag, rang in kandidaten:
            verteilung[rang] += 1
        return dict(sorted(verteilung.items()))

    def fehlende_spieler(self):
        """Belegte High-Rank-Spieler, die noch gar nicht im Katalog stehen.

        Sie tauchen in importierten Partien auf, wurden aber wegen der
        Tiefengrenze nie als TrackedPlayer gespeichert. Nachtragen kostet
        keine einzige API-Anfrage.
        """
        bekannt = set(TrackedPlayer.objects.values_list("tag", flat=True))
        return sorted(
            tag for tag, rang in self.rang.items()
            if rang >= self.min_rang and tag not in bekannt
        )

    def nachtragen(self, tiefe=1):
        """Fehlende High-Rank-Spieler als TrackedPlayer anlegen. Ohne Netz."""
        fehlende = self.fehlende_spieler()
        TrackedPlayer.objects.bulk_create(
            [
                TrackedPlayer(tag=tag, origin=TrackedPlayer.Origin.DISCOVERED, depth=tiefe)
                for tag in fehlende
            ],
            ignore_conflicts=True,
        )
        return fehlende
