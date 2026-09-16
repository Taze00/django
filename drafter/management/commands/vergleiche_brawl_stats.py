# -*- coding: utf-8 -*-
"""Vergleichsbericht: gemessene Statistiken neben den Demo-Daten.

    python manage.py vergleiche_brawl_stats --quelle api
    python manage.py vergleiche_brawl_stats --quelle api --fenster 30d --min-spiele 30

**Aktiviert nichts.** Die Seite nimmt gemessene Werte erst, wenn
DRAFTER_GEMESSENE_STATS_FREIGEGEBEN gesetzt ist. Dieser Bericht ist die
Grundlage fuer genau diese Entscheidung: Wie gross sind die Stichproben,
wie sicher die Zahlen, und wuerde sich die Empfehlung ueberhaupt aendern?
"""

from collections import Counter
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from drafter import config
from drafter.management.commands.aggregate_brawl_stats import QUELLEN_WAHL
from drafter.models import BrawlerStat, BrawlMap, CounterStat, Datenquelle, SynergyStat
from drafter.models.matches import Match
from drafter.services.aggregation.aggregator import ziel_quelle_fuer
from drafter.services.confidence import label
from drafter.services.context import DraftContext
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import DatenbankStatProvider
from drafter.services.providers.demo import DemoDataProvider


def _prozent(wert):
    return "–" if wert is None else f"{wert * 100:.1f} %"


def _tabelle(kopf, zeilen):
    text = ["| " + " | ".join(kopf) + " |", "|" + "---|" * len(kopf)]
    text += ["| " + " | ".join(str(z) for z in zeile) + " |" for zeile in zeilen]
    return text + [""]


class Command(BaseCommand):
    help = (
        "Vergleicht aggregierte echte Statistiken mit den Demo-Daten und schreibt "
        "einen Bericht. Ändert keine Daten und aktiviert nichts."
    )

    def add_arguments(self, parser):
        parser.add_argument("--quelle", default="api",
                            choices=sorted(q for q in QUELLEN_WAHL if q != "synthetisch"))
        parser.add_argument("--fenster", default=config.PRIOR_FENSTER,
                            choices=list(config.AGGREGATIONS_FENSTER))
        parser.add_argument("--rank-pool", default="alle",
                            choices=[k for k, _ in config.RANG_POOLS])
        parser.add_argument("--min-spiele", type=int, default=20,
                            help="Mindestspiele für Counter- und Synergie-Listen")
        parser.add_argument("--top", type=int, default=15)
        parser.add_argument("--ausgabe", default=None, help="Zieldatei (Standard: data/brawl_reports/)")

    def handle(self, *args, **o):
        quellen = QUELLEN_WAHL[o["quelle"]]
        ziel_quelle = ziel_quelle_fuer(quellen)
        kontext = dict(source=ziel_quelle, window_label=o["fenster"], rank_pool=o["rank_pool"])

        global_zeilen = list(
            BrawlerStat.objects.filter(game_mode__isnull=True, brawl_map__isnull=True, **kontext)
            .select_related("brawler").order_by("-games")
        )
        if not global_zeilen:
            raise CommandError(
                f"Keine Statistiken für Quelle '{ziel_quelle}', Fenster {o['fenster']}, "
                f"Rangbereich {o['rank_pool']}. Zuerst aggregate_brawl_stats laufen lassen."
            )

        text = [f"# Vergleich: gemessen ('{ziel_quelle}') gegen Demo", ""]
        text += self._datenbasis(quellen, ziel_quelle, global_zeilen, o)
        text += self._brawler(global_zeilen, o)
        text += self._map_modus(kontext, o)
        text += self._paare(kontext, o)
        text += self._engine(ziel_quelle, o)
        text += [
            "## Was das heißt", "",
            "- Diese Zahlen sind **nicht** aktiv. `auto` liefert weiter die Demo-Daten, "
            "solange `DRAFTER_GEMESSENE_STATS_FREIGEGEBEN` nicht gesetzt ist.",
            "- Kleine Stichproben bleiben durch die Bayes-Glättung nahe der Erwartung, und "
            "ihre Confidence bleibt niedrig - die Oberfläche zeigt sie nie als belastbar.",
            "- Erst wenn die Stichproben je Map und Paar groß genug sind, lohnt die Freigabe.",
        ]

        ziel = Path(o["ausgabe"]) if o["ausgabe"] else (
            Path(config.BERICHT_VERZEICHNIS)
            / f"vergleich_{datetime.now(dt_timezone.utc):%Y%m%dT%H%M%SZ}.md"
        )
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text("\n".join(text) + "\n", encoding="utf-8")
        self.stdout.write("\n".join(text[:40]))
        self.stdout.write(self.style.SUCCESS(f"\nBericht: {ziel}"))

    # --- Abschnitte -----------------------------------------------------
    def _datenbasis(self, quellen, ziel_quelle, global_zeilen, o):
        start = min((z.window_start for z in global_zeilen if z.window_start), default=None)
        ende = max((z.window_end for z in global_zeilen if z.window_end), default=None)
        partien = Match.objects.filter(source__in=quellen)
        if start and ende:
            partien = partien.filter(played_at__date__gte=start, played_at__date__lte=ende)
        zaehlbar = partien.filter(
            is_ranked=True, has_conflict=False, winner_side__in=["a", "b"],
            battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN,
        ).count()
        stufen = Counter(label(z.confidence) for z in global_zeilen)
        hoch_ab = round(config.CONFIDENCE_STUFEN[0][0] ** 2 * config.CONFIDENCE_VOLL_AB)
        return [
            "## Datenbasis", "",
            f"- Quelle: `{ziel_quelle}` | Fenster: {o['fenster']} ({start} bis {ende}) "
            f"| Rangbereich: {o['rank_pool']}",
            f"- Partien der Quelle im Fenster: {partien.count()} "
            f"({dict(Counter(partien.values_list('battle_type', flat=True)))})",
            f"- Davon gezählt (soloRanked, mit Ergebnis, ohne Konflikt): **{zaehlbar}**",
            f"- Brawler mit Messwerten: {len(global_zeilen)} | Confidence-Stufen: {dict(stufen)}",
            f"- „Hoch\" erreicht eine Zeile erst ab rund {hoch_ab} gewichteten Spielen.",
            "",
        ]

    def _brawler(self, global_zeilen, o):
        demo = {
            z.brawler_id: z.adjusted_rate
            for z in BrawlerStat.objects.filter(
                source=Datenquelle.DEMO, game_mode__isnull=True, brawl_map__isnull=True)
        }
        zeilen = []
        for z in global_zeilen[:o["top"]]:
            demo_rate = demo.get(z.brawler_id)
            diff = (None if demo_rate is None or z.adjusted_rate is None
                    else z.adjusted_rate - demo_rate)
            zeilen.append([
                z.brawler.name, z.games, round(z.sample_size, 1), _prozent(z.pick_rate),
                _prozent(z.raw_rate), _prozent(z.adjusted_rate),
                f"{z.confidence:.2f} ({label(z.confidence)})",
                _prozent(demo_rate), "–" if diff is None else f"{diff * 100:+.1f} pp",
            ])
        return ["## Brawler (modusübergreifend)", ""] + _tabelle(
            ["Brawler", "Spiele", "gewichtet", "Pickrate", "Winrate roh",
             "Winrate geglättet", "Confidence", "Demo", "Differenz"],
            zeilen,
        )

    def _map_modus(self, kontext, o):
        zeilen = [
            [z.brawl_map.name, z.game_mode.name if z.game_mode else "–", z.brawler.name,
             z.games, _prozent(z.raw_rate), _prozent(z.adjusted_rate), f"{z.confidence:.2f}"]
            for z in BrawlerStat.objects.filter(brawl_map__isnull=False, **kontext)
            .select_related("brawler", "brawl_map", "game_mode").order_by("-games")[:o["top"]]
        ]
        return ["## Map + Modus", "",
                "Die feinste Ebene - und die dünnste. Hier zeigt sich zuerst, "
                "wenn die Datenmenge noch nicht reicht.", ""] + _tabelle(
            ["Map", "Modus", "Brawler", "Spiele", "Winrate roh", "geglättet", "Confidence"],
            zeilen,
        )

    def _paare(self, kontext, o):
        demo_counter = {
            (z.brawler_id, z.enemy_id): z.advantage
            for z in CounterStat.objects.filter(source=Datenquelle.DEMO)
        }
        counter = [
            z for z in CounterStat.objects.filter(
                game_mode__isnull=True, brawl_map__isnull=True, **kontext)
            .select_related("brawler", "enemy")
            if z.games >= o["min_spiele"]
        ]
        counter.sort(key=lambda z: -abs(z.advantage or 0))
        counter_zeilen = [
            [f"{z.brawler.name} vs. {z.enemy.name}", z.games, _prozent(z.raw_rate),
             f"{z.advantage:+.3f}", f"{z.confidence:.2f}",
             ("–" if demo_counter.get((z.brawler_id, z.enemy_id)) is None
              else f"{demo_counter[(z.brawler_id, z.enemy_id)]:+.2f}"),
             ("–" if demo_counter.get((z.enemy_id, z.brawler_id)) is None
              else f"{demo_counter[(z.enemy_id, z.brawler_id)]:+.2f}")]
            for z in counter[:o["top"]]
        ]

        synergie = [
            z for z in SynergyStat.objects.filter(
                game_mode__isnull=True, brawl_map__isnull=True, **kontext)
            .select_related("brawler_a", "brawler_b")
            if z.games >= o["min_spiele"]
        ]
        synergie.sort(key=lambda z: -abs(z.synergy or 0))
        synergie_zeilen = [
            [f"{z.brawler_a.name} + {z.brawler_b.name}", z.games, _prozent(z.raw_rate),
             f"{z.synergy:+.3f}", f"{z.confidence:.2f}"]
            for z in synergie[:o["top"]]
        ]

        text = ["## Counter", "",
                f"Abweichung von der log5-Erwartung, ab {o['min_spiele']} Spielen je Paar. "
                f"Gemessene Paare stehen einmal (kleinere Brawler-ID zuerst); die "
                f"Gegenrichtung ist ihr Negativ.", ""]
        text += _tabelle(["Paarung", "Spiele", "Winrate", "Vorteil (gemessen)", "Confidence",
                          "Demo hin", "Demo her"], counter_zeilen)
        text += ["## Synergien", "", f"Ab {o['min_spiele']} Spielen je Paar.", ""]
        text += _tabelle(["Paar", "Spiele", "Winrate", "Synergie", "Confidence"], synergie_zeilen)
        return text

    def _engine(self, ziel_quelle, o):
        """Wuerde sich die Empfehlung ueberhaupt aendern?"""
        gemessen = DatenbankStatProvider((ziel_quelle,), name="gemessen-vergleich")
        zeilen = []
        for karte in BrawlMap.objects.filter(is_active=True).select_related("game_mode"):
            namen = []
            for provider in (DemoDataProvider(), gemessen):
                ctx = DraftContext(
                    game_mode=karte.game_mode, brawl_map=karte, own_picks=(), enemy_picks=(),
                    bans=(), own_team_first_pick=True, rank_pool=o["rank_pool"], personal={},
                )
                empfehlungen = DraftEngine(ctx, provider=provider).empfehlungen(
                    anzahl=5, mit_details=0)
                namen.append([e.brawler.name for e in empfehlungen])
            gleich = len(set(namen[0]) & set(namen[1]))
            zeilen.append([karte.name, ", ".join(namen[0]), ", ".join(namen[1]), f"{gleich}/5"])
        return ["## Engine: First Pick je Map", "",
                "Dieselbe Lage, einmal mit Demo-Daten, einmal mit den gemessenen. "
                "Die letzte Spalte zählt, wie viele der Top 5 übereinstimmen.", ""] + _tabelle(
            ["Map", "Demo", "Gemessen", "gleich"], zeilen,
        )
