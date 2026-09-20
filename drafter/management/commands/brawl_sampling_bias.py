# -*- coding: utf-8 -*-
"""Wie stark faerbt die Auswahl der abgefragten Spieler unsere Statistiken?

**Misst nur. Korrigiert nichts.** Der Befund aus dem Praxistest vom
2026-09-20: der jeweils abgefragte Spieler gewinnt 58 % seiner Partien -
er wurde ja danach ausgesucht, weit oben in der Rangliste zu stehen.
Damit haengt jeder gemessene Wert daran, auf welcher Seite dieser
Spieler stand: EDGAR kam auf 54,9 % in seinem Team und 44,4 % gegen ihn,
ein Unterschied von 10,5 Punkten, der nichts mit EDGAR zu tun hat.

Zwei Kennzahlen, beide je Brawler oder je Paar:

    queried_side_balance   Anteil der Partien, in denen der abgefragte
                           Spieler auf DERSELBEN Seite stand. 0,5 waere
                           ausgeglichen; alles andere ist Schieflage.
    sampled_side_winrate   Siegquote der Seite des abgefragten Spielers.
                           Sie misst die Staerke der Auswahl, nicht die
                           des Brawlers.

Warum als Kommando und nicht in der API: die Engine liest grundsaetzlich
keine Rohmatches (siehe DRAFTER_DOKUMENTATION §16). Wer die Zahlen im
Draft sehen will, muss sie beim Aggregieren an die Statistikzeile
schreiben - ein Feld, keine Abfrage zur Laufzeit. Solange keine
Korrekturformel steht, ist das verfrueht.
"""

from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from drafter import config
from drafter.models import Brawler
from drafter.models.matches import Match
from drafter.services.identitaet import Mehrdeutig, finde_brawler

RANKED = Q(is_ranked=True, battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN)


def _tags(match):
    """Die Spieler-Tags, deren Battlelog diese Partie geliefert hat."""
    return {(p.reference or "").upper().lstrip("#") for p in match.payloads.all()
            if p.reference}


def _abgefragte_seiten(match):
    tags = _tags(match)
    return {s.side for s in match.players.all()
            if (s.player_tag or "").upper().lstrip("#") in tags}


class Lage:
    """Zaehlwerk fuer einen Brawler oder ein Paar."""

    def __init__(self):
        self.gleiche_seite = self.gegenseite = self.ohne = 0
        self.siege_gleich = self.siege_gegen = 0
        self.abgefragt_siege = self.abgefragt_partien = 0

    def zaehle(self, gleiche_seite, sieg, abgefragt_sieg):
        if gleiche_seite is None:
            self.ohne += 1
            return
        self.abgefragt_partien += 1
        self.abgefragt_siege += 1 if abgefragt_sieg else 0
        if gleiche_seite:
            self.gleiche_seite += 1
            self.siege_gleich += 1 if sieg else 0
        else:
            self.gegenseite += 1
            self.siege_gegen += 1 if sieg else 0

    @property
    def partien(self):
        return self.gleiche_seite + self.gegenseite + self.ohne

    @property
    def queried_side_balance(self):
        n = self.gleiche_seite + self.gegenseite
        return self.gleiche_seite / n if n else None

    @property
    def sampled_side_winrate(self):
        return (self.abgefragt_siege / self.abgefragt_partien
                if self.abgefragt_partien else None)

    @property
    def spreizung(self):
        """Siegquote mit dem Abgefragten minus ohne ihn - das Artefakt."""
        if not (self.gleiche_seite and self.gegenseite):
            return None
        return (self.siege_gleich / self.gleiche_seite
                - self.siege_gegen / self.gegenseite)


class Command(BaseCommand):
    help = "Sampling-Bias der abgefragten Spieler messen (read-only, korrigiert nichts)"

    def add_arguments(self, parser):
        parser.add_argument("--brawler", default="",
                            help="Nur diesen Brawler (Name, Slug oder ID)")
        parser.add_argument("--paar", default="",
                            help="Zwei Brawler, kommagetrennt - Paarsicht")
        parser.add_argument("--top", type=int, default=15,
                            help="Wie viele Brawler in der Rangliste (Standard: %(default)s)")
        parser.add_argument("--min-partien", type=int, default=50,
                            help="Brawler unter dieser Partienzahl auslassen")

    def handle(self, *args, **o):
        partien = Match.objects.filter(RANKED).prefetch_related("players", "payloads")
        gesamt = Lage()
        je_brawler = defaultdict(Lage)
        paar_ids = self._paar(o["paar"])
        paar = Lage()

        namen = dict(Brawler.objects.values_list("id", "name"))
        for match in partien.iterator(chunk_size=500):
            seiten = _abgefragte_seiten(match)
            spieler = [s for s in match.players.all() if s.brawler_id]
            if not spieler:
                continue
            for s in spieler:
                gleiche = (s.side in seiten) if seiten else None
                sieg = match.winner_side == s.side
                abgefragt_sieg = bool(seiten) and match.winner_side in seiten
                je_brawler[s.brawler_id].zaehle(gleiche, sieg, abgefragt_sieg)
            # Gesamtsicht je Partie, nicht je Spieler.
            if seiten:
                gesamt.zaehle(True, match.winner_side in seiten,
                              match.winner_side in seiten)
            else:
                gesamt.zaehle(None, False, False)

            if paar_ids:
                self._paar_zaehlen(match, seiten, paar_ids, paar)

        self._gesamt(gesamt)
        if paar_ids:
            self._paarbericht(paar, paar_ids, namen)
        if o["brawler"]:
            b = self._einer(o["brawler"])
            self._zeile(namen[b.id], je_brawler[b.id], kopf=True)
            return
        self._rangliste(je_brawler, namen, o["top"], o["min_partien"])

    # --- Teile ----------------------------------------------------------
    def _einer(self, eingabe):
        try:
            b = finde_brawler(eingabe)
        except Mehrdeutig as fehler:
            raise CommandError(str(fehler))
        if b is None:
            raise CommandError(f"Unbekannter Brawler '{eingabe}'")
        return b

    def _paar(self, eingabe):
        if not eingabe:
            return ()
        teile = [t.strip() for t in eingabe.replace(";", ",").split(",") if t.strip()]
        if len(teile) != 2:
            raise CommandError("--paar erwartet genau zwei Brawler")
        return tuple(self._einer(t).id for t in teile)

    @staticmethod
    def _paar_zaehlen(match, seiten, paar_ids, lage):
        a, b = paar_ids
        seiten_a = {s.side for s in match.players.all() if s.brawler_id == a}
        seiten_b = {s.side for s in match.players.all() if s.brawler_id == b}
        if not (seiten_a and seiten_b):
            return
        # Bezugsseite: bei gemeinsamer Seite diese, sonst die des ersten.
        bezug = next(iter(seiten_a & seiten_b), None) or next(iter(seiten_a))
        gleiche = (bezug in seiten) if seiten else None
        lage.zaehle(gleiche, match.winner_side == bezug,
                    bool(seiten) and match.winner_side in seiten)

    def _gesamt(self, lage):
        self.stdout.write(self.style.SUCCESS("\nGesamt (je Partie)"))
        self.stdout.write(f"  Ranked-Partien:            {lage.partien}")
        self.stdout.write(f"  ohne zuordenbaren Spieler: {lage.ohne}")
        wr = lage.sampled_side_winrate
        self.stdout.write(
            f"  sampled_side_winrate:      {wr:.4f}" if wr is not None else
            "  sampled_side_winrate:      -")
        self.stdout.write(
            "  (Siegquote der Seite, von der der Battlelog stammt. 0,5 hiesse: "
            "die Auswahl faerbt nicht.)")

    def _zeile(self, name, lage, kopf=False):
        if kopf:
            self.stdout.write(self.style.HTTP_INFO(
                f"\n{'Brawler':<18} {'Partien':>8} {'balance':>8} {'WR mit':>8} "
                f"{'WR gegen':>9} {'Spreizung':>10}"))
        bal = lage.queried_side_balance
        mit = (lage.siege_gleich / lage.gleiche_seite) if lage.gleiche_seite else None
        gegen = (lage.siege_gegen / lage.gegenseite) if lage.gegenseite else None
        spr = lage.spreizung
        f = lambda w: f"{w:.3f}" if w is not None else "    -"
        self.stdout.write(f"{name:<18} {lage.partien:>8} {f(bal):>8} {f(mit):>8} "
                          f"{f(gegen):>9} {f(spr):>10}")

    def _rangliste(self, je_brawler, namen, top, min_partien):
        eintraege = [(bid, l) for bid, l in je_brawler.items() if l.partien >= min_partien]
        eintraege.sort(key=lambda e: -abs(e[1].spreizung or 0))
        self.stdout.write(self.style.SUCCESS(
            f"\nGroesste Spreizung (mind. {min_partien} Partien, {len(eintraege)} Brawler)"))
        for i, (bid, lage) in enumerate(eintraege[:top]):
            self._zeile(namen.get(bid, str(bid)), lage, kopf=(i == 0))
        werte = [abs(l.spreizung) for _, l in eintraege if l.spreizung is not None]
        if werte:
            werte.sort()
            self.stdout.write(
                f"\n  Median |Spreizung| {werte[len(werte)//2]:.4f}, "
                f"max {werte[-1]:.4f} - ueber {len(werte)} Brawler")
        balancen = sorted(l.queried_side_balance for _, l in eintraege
                          if l.queried_side_balance is not None)
        if balancen:
            self.stdout.write(
                f"  queried_side_balance: median {balancen[len(balancen)//2]:.4f}, "
                f"min {balancen[0]:.4f}, max {balancen[-1]:.4f} (0,5 waere ausgeglichen)")

    def _paarbericht(self, lage, paar_ids, namen):
        a, b = (namen.get(i, str(i)) for i in paar_ids)
        self.stdout.write(self.style.SUCCESS(f"\nPaar {a} / {b}"))
        self._zeile(f"{a}+{b}", lage, kopf=True)
