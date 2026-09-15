# -*- coding: utf-8 -*-
"""Rohmatches zaehlen, gewichten, glaetten und als Statistik schreiben.

Einmal je (Quelle, Rangbereich, Zeitfenster). Jede Partie traegt mit

    gewicht = zeit_gewicht(Spieldatum) * patch_gewicht(je beteiligtem Brawler)

zur Statistik bei. Neuere Partien zaehlen mehr, Partien von vor einer
Balanceaenderung weniger - und zwar nur fuer den Brawler, der veraendert
wurde. Wird Gale generft, verlieren Gales alte Partien an Gewicht, die
von Belle in denselben Partien nicht.

Idempotent: jeder Lauf ersetzt die Zeilen seines Kontexts vollstaendig.
Zweimal aggregieren ergibt dasselbe wie einmal.

Was hier NICHT passiert: Demo-Daten anfassen. Geschrieben und geloescht
wird ausschliesslich unter der Zielquelle des Laufs.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import timedelta
from itertools import combinations

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from drafter import config
from drafter.models import (
    Brawler, BrawlerItem, BrawlerStat, BuildStat, CounterStat, Datenquelle, Patch, SynergyStat,
)
from drafter.models.matches import Match
from drafter.services.aggregation.rechnung import (
    Zaehler, erwartet_gegeneinander, erwartet_miteinander, vorteil,
)
from drafter.services.confidence import stichproben_confidence
from drafter.services.patch_weighting import patch_gewicht, zeit_gewicht

GLOBAL, MODUS, MAP = "global", "modus", "map"
STAT_MODELLE = (BrawlerStat, CounterStat, SynergyStat, BuildStat)
KEINE_MATCHES = frozenset({Datenquelle.DEMO, Datenquelle.MANUAL})


def ziel_quelle_fuer(quellen):
    """Unter welcher Quelle die Statistiken gespeichert werden.

    Eine Quelle bleibt sie selbst. Mehrere echte Quellen werden zu
    "aggregated". Synthetische Partien werden NIE mit echten gemischt -
    sonst waere eine ausgedachte Partie in einer echten Statistik nicht
    mehr herauszurechnen.
    """
    quellen = tuple(dict.fromkeys(str(q) for q in quellen))
    if not quellen:
        raise ValueError("Mindestens eine Quelle angeben")
    if set(quellen) & KEINE_MATCHES:
        raise ValueError("Demo- und gepflegte Daten sind keine Matches und werden nicht aggregiert")
    if Datenquelle.SYNTHETIC in quellen and len(quellen) > 1:
        raise ValueError("Synthetische Partien werden nie mit echten zusammen aggregiert")
    return quellen[0] if len(quellen) == 1 else Datenquelle.AGGREGATED


def patches_neu_zuordnen(quellen):
    """Jeder Partie den Patch zuordnen, der zum Spielzeitpunkt galt.

    Noetig, wenn ein Patch nachtraeglich eingetragen wird: beim Import
    war er noch nicht bekannt. Gibt die Anzahl geaenderter Partien zurueck.
    """
    patches = list(Patch.objects.order_by("-released_on"))
    geaendert = []
    for match in Match.objects.filter(source__in=quellen).only("id", "played_at", "patch_id"):
        tag = match.played_at.date()
        passend = next((p for p in patches if p.released_on <= tag), None)
        neu = passend.id if passend else None
        if neu != match.patch_id:
            match.patch_id = neu
            geaendert.append(match)
    Match.objects.bulk_update(geaendert, ["patch"], batch_size=2000)
    return len(geaendert)


@dataclass
class AggregationsBericht:
    quellen: tuple
    ziel_quelle: str
    stichtag: object
    patch: object = None
    partien: dict = field(default_factory=dict)
    zeilen: Counter = field(default_factory=Counter)
    hinweise: list = field(default_factory=list)

    def zeilen_text(self):
        text = [
            f"Quellen: {', '.join(self.quellen)} -> gespeichert als '{self.ziel_quelle}'",
            f"Stichtag: {self.stichtag} | aktueller Patch: {self.patch or 'keiner eingetragen'}",
        ]
        for (pool, fenster), anzahl in sorted(self.partien.items()):
            text.append(f"  {pool:10s} {fenster:10s} {anzahl:6d} zählbare Partien")
        text.append(
            "Geschriebene Zeilen: "
            + ", ".join(f"{art} {n}" for art, n in sorted(self.zeilen.items()))
        )
        return text + [f"  - {h}" for h in self.hinweise]


def _build_teile(build):
    """(Art, Slug) aus einem Build - nur, was tatsaechlich angegeben ist."""
    if not isinstance(build, dict):
        return []
    teile = [(art, build.get(art)) for art in ("gadget", "star_power", "hypercharge")]
    teile += [("gear", g) for g in (build.get("gears") or [])]
    return [(art, slugify(str(slug))) for art, slug in teile if slug]


class Aggregator:
    def __init__(self, quellen, stichtag=None, rank_pools=None, fenster=None, nur_ranked=True):
        self.ziel_quelle = ziel_quelle_fuer(quellen)
        self.quellen = tuple(dict.fromkeys(str(q) for q in quellen))
        self.stichtag = stichtag or timezone.now().date()
        self.rank_pools = list(rank_pools or [k for k, _ in config.RANG_POOLS])
        self.fenster = list(fenster or config.AGGREGATIONS_FENSTER)
        unbekannt = set(self.fenster) - set(config.AGGREGATIONS_FENSTER)
        if unbekannt:
            raise ValueError(f"Unbekannte Zeitfenster: {sorted(unbekannt)}")
        self.nur_ranked = nur_ranked

        # "Aktuell" relativ zum Stichtag, nicht zu heute - so laesst sich
        # spaeter auch rueckwirkend aggregieren (Backtesting).
        self.aktueller_patch = (
            Patch.objects.filter(released_on__lte=self.stichtag).order_by("-released_on").first()
        )
        self._brawler = {
            b.id: b for b in Brawler.objects.prefetch_related("balance_changes__patch")
        }
        self._items = {(i.brawler_id, i.kind, i.slug): i for i in BrawlerItem.objects.all()}
        self._patch_cache = {}

    # --- Ablauf ---------------------------------------------------------
    def ausfuehren(self):
        bericht = AggregationsBericht(
            quellen=self.quellen, ziel_quelle=self.ziel_quelle,
            stichtag=self.stichtag, patch=self.aktueller_patch,
        )
        # Das Prior-Fenster zuerst: die kuerzeren Fenster schrumpfen darauf.
        reihenfolge = sorted(self.fenster, key=lambda f: f != config.PRIOR_FENSTER)
        with transaction.atomic():
            for pool in self.rank_pools:
                prior = {}
                for name in reihenfolge:
                    raten = self._fenster(pool, name, prior, bericht)
                    if name == config.PRIOR_FENSTER and raten:
                        prior = raten
        if self.ziel_quelle == Datenquelle.SYNTHETIC:
            bericht.hinweise.append(
                "Synthetische Daten: diese Statistiken werden von 'auto' nie benutzt."
            )
        return bericht

    def _zeitraum(self, name):
        tage = config.AGGREGATIONS_FENSTER[name]
        if tage is None:
            if self.aktueller_patch is None:
                return None
            return self.aktueller_patch.released_on, self.stichtag
        return self.stichtag - timedelta(days=tage - 1), self.stichtag

    def _partien(self, pool, start, ende):
        partien = Match.objects.filter(
            source__in=self.quellen,
            has_conflict=False,
            winner_side__in=[Match.Seite.A, Match.Seite.B],
            played_at__date__gte=start,
            played_at__date__lte=ende,
        )
        if self.nur_ranked:
            partien = partien.filter(is_ranked=True)
        if pool != "alle":
            partien = partien.filter(rank_pool=pool)
        return partien.prefetch_related("players", "bans")

    def _patch_gewicht(self, brawler_id, match_patch):
        schluessel = (brawler_id, match_patch.id if match_patch else None)
        if schluessel not in self._patch_cache:
            self._patch_cache[schluessel] = patch_gewicht(
                self._brawler[brawler_id], match_patch, self.aktueller_patch
            )
        return self._patch_cache[schluessel]

    @staticmethod
    def _ebenen(match):
        ebenen = [(GLOBAL, None, None)]
        if match.game_mode_id:
            ebenen.append((MODUS, match.game_mode_id, None))
        if match.brawl_map_id:
            ebenen.append((MAP, match.game_mode_id, match.brawl_map_id))
        return ebenen

    # --- Ein Fenster ----------------------------------------------------
    def _fenster(self, pool, name, prior, bericht):
        kontext = dict(source=self.ziel_quelle, window_label=name, rank_pool=pool)
        # Immer erst loeschen - auch wenn das Fenster jetzt leer ist.
        # Sonst blieben Zeilen eines frueheren Laufs stehen, die zu keiner
        # aktuellen Partie mehr passen.
        for modell in STAT_MODELLE:
            modell.objects.filter(**kontext).delete()

        zeitraum = self._zeitraum(name)
        if zeitraum is None:
            bericht.hinweise.append(f"{pool}/{name}: kein Patch eingetragen - Fenster übersprungen")
            return None
        start, ende = zeitraum

        ebenen_fuer = config.AGGREGATIONS_EBENEN
        brawler_z = defaultdict(Zaehler)
        counter_z = defaultdict(Zaehler)
        synergie_z = defaultdict(Zaehler)
        build_z = defaultdict(Zaehler)
        auftritte = Counter()
        partien_je_ebene = Counter()
        ban_partien = Counter()
        bans = Counter()
        anzahl = 0

        for match in self._partien(pool, start, ende).iterator(chunk_size=2000):
            spieler = [s for s in match.players.all() if s.brawler_id]
            if not spieler:
                continue
            anzahl += 1
            zeit = zeit_gewicht(match.played_at.date(), self.stichtag)
            pg = {s.brawler_id: self._patch_gewicht(s.brawler_id, match.patch) for s in spieler}
            teams = {"a": [s for s in spieler if s.side == "a"],
                     "b": [s for s in spieler if s.side == "b"]}
            gebannt = [b.brawler_id for b in match.bans.all() if b.brawler_id]

            for ebene in self._ebenen(match):
                art = ebene[0]
                if art in ebenen_fuer["brawler"]:
                    partien_je_ebene[ebene] += 1
                    for bid in {s.brawler_id for s in spieler}:
                        auftritte[(ebene, bid)] += 1
                    # Banrate nur ueber Partien, deren Quelle Bans kennt -
                    # sonst verduennen Partien ohne Ban-Angabe die Rate.
                    if match.bans.all():
                        ban_partien[ebene] += 1
                        for bid in set(gebannt):
                            bans[(ebene, bid)] += 1
                    for s in spieler:
                        brawler_z[(ebene, s.brawler_id)].zaehle(
                            s.side == match.winner_side, zeit * pg[s.brawler_id]
                        )

                if art in ebenen_fuer["build"]:
                    for s in spieler:
                        for teil_art, slug in _build_teile(s.build):
                            build_z[(ebene, s.brawler_id, teil_art, slug)].zaehle(
                                s.side == match.winner_side, zeit * pg[s.brawler_id]
                            )

                if art in ebenen_fuer["counter"]:
                    for p in teams["a"]:
                        for q in teams["b"]:
                            if p.brawler_id == q.brawler_id:
                                continue
                            w = zeit * pg[p.brawler_id] * pg[q.brawler_id]
                            counter_z[(ebene, p.brawler_id, q.brawler_id)].zaehle(
                                match.winner_side == "a", w)
                            counter_z[(ebene, q.brawler_id, p.brawler_id)].zaehle(
                                match.winner_side == "b", w)

                if art in ebenen_fuer["synergy"]:
                    for seite, team in teams.items():
                        ids = sorted({s.brawler_id for s in team})
                        for x, y in combinations(ids, 2):
                            synergie_z[(ebene, x, y)].zaehle(
                                match.winner_side == seite, zeit * pg[x] * pg[y])

        bericht.partien[(pool, name)] = anzahl

        gemeinsam = lambda ebene: dict(
            game_mode_id=ebene[1], brawl_map_id=ebene[2], patch=self.aktueller_patch,
            window_start=start, window_end=ende, **kontext,
        )

        def stichprobe(z, geglaettet):
            return dict(
                games=z.games, wins=z.wins, sample_size=round(z.gewicht, 4),
                raw_rate=z.roh, adjusted_rate=geglaettet,
                confidence=round(stichproben_confidence(z.gewicht), 4),
            )

        # --- Brawler: von grob nach fein, jede Ebene schrumpft zur groeberen
        raten = {}
        zeilen = []
        for stufe in (GLOBAL, MODUS, MAP):
            for (ebene, bid), z in brawler_z.items():
                if ebene[0] != stufe:
                    continue
                prior_rate = self._brawler_prior(ebene, bid, raten, prior)
                geglaettet = z.geglaettet(prior_rate, config.PRIOR_STAERKE)
                raten[(ebene, bid)] = geglaettet
                zeilen.append(BrawlerStat(
                    brawler_id=bid,
                    pick_rate=round(auftritte[(ebene, bid)] / partien_je_ebene[ebene], 4),
                    ban_rate=(round(bans[(ebene, bid)] / ban_partien[ebene], 4)
                              if ban_partien[ebene] else 0.0),
                    **gemeinsam(ebene), **stichprobe(z, geglaettet),
                ))
        # Brawler, die nur gebannt, aber nie gespielt wurden. Ohne eigene
        # Zeile ginge ausgerechnet die aussagekraeftigste Ban-Information
        # verloren: wer in jeder Partie gebannt wird, wird nie gespielt.
        # Keine Spiele heisst keine Rate - adjusted_rate bleibt leer, und
        # die Meta-Komponente behandelt die Zeile damit als "keine Auskunft".
        for (ebene, bid), anzahl_bans in bans.items():
            if (ebene, bid) in brawler_z:
                continue
            zeilen.append(BrawlerStat(
                brawler_id=bid, pick_rate=0.0,
                ban_rate=round(anzahl_bans / ban_partien[ebene], 4),
                games=0, wins=0, sample_size=0.0, raw_rate=None, adjusted_rate=None,
                confidence=0.0, **gemeinsam(ebene),
            ))
        self._schreibe(BrawlerStat, zeilen, bericht, "brawler")

        # --- Counter: Abweichung von der log5-Erwartung
        zeilen = []
        for (ebene, a, b), z in counter_z.items():
            erwartet = erwartet_gegeneinander(self._rate(raten, ebene, a),
                                              self._rate(raten, ebene, b))
            geglaettet = z.geglaettet(erwartet, config.PAAR_PRIOR_STAERKE)
            zeilen.append(CounterStat(
                brawler_id=a, enemy_id=b, advantage=round(vorteil(geglaettet, erwartet), 4),
                **gemeinsam(ebene), **stichprobe(z, geglaettet),
            ))
        self._schreibe(CounterStat, zeilen, bericht, "counter")

        # --- Synergie: Abweichung von additiven Log-Odds
        zeilen = []
        for (ebene, x, y), z in synergie_z.items():
            erwartet = erwartet_miteinander(self._rate(raten, ebene, x),
                                            self._rate(raten, ebene, y))
            geglaettet = z.geglaettet(erwartet, config.PAAR_PRIOR_STAERKE)
            zeilen.append(SynergyStat(
                brawler_a_id=x, brawler_b_id=y, synergy=round(vorteil(geglaettet, erwartet), 4),
                **gemeinsam(ebene), **stichprobe(z, geglaettet),
            ))
        self._schreibe(SynergyStat, zeilen, bericht, "synergy")

        # --- Builds: Abweichung von der Grundleistung des Brawlers
        zeilen = []
        for (ebene, bid, teil_art, slug), z in build_z.items():
            grund = self._rate(raten, ebene, bid)
            geglaettet = z.geglaettet(grund, config.PRIOR_STAERKE)
            item = self._items.get((bid, teil_art, slug)) or self._items.get((None, teil_art, slug))
            zeilen.append(BuildStat(
                brawler_id=bid, item=item, item_kind=teil_art, item_slug=slug,
                advantage=round(vorteil(geglaettet, grund), 4),
                **gemeinsam(ebene), **stichprobe(z, geglaettet),
            ))
        self._schreibe(BuildStat, zeilen, bericht, "build")

        return {schluessel: rate for schluessel, rate in raten.items()}

    def _brawler_prior(self, ebene, bid, raten, prior):
        if ebene[0] == GLOBAL:
            return prior.get((ebene, bid), config.PRIOR_RATE)
        if ebene[0] == MODUS:
            return raten.get(((GLOBAL, None, None), bid), config.PRIOR_RATE)
        return raten.get(((MODUS, ebene[1], None), bid),
                         raten.get(((GLOBAL, None, None), bid), config.PRIOR_RATE))

    @staticmethod
    def _rate(raten, ebene, bid):
        """Geglaettete Einzelrate - auf der Ebene, sonst global, sonst 50 %."""
        return raten.get((ebene, bid), raten.get(((GLOBAL, None, None), bid), config.PRIOR_RATE))

    @staticmethod
    def _schreibe(modell, zeilen, bericht, art):
        # bulk_create umgeht save() - der Kontextschluessel muss deshalb
        # hier gesetzt werden, sonst waeren alle Zeilen "gleich".
        for zeile in zeilen:
            zeile.context_key = zeile.berechne_context_key()
        modell.objects.bulk_create(zeilen, batch_size=2000)
        bericht.zeilen[art] += len(zeilen)
