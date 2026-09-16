# -*- coding: utf-8 -*-
"""Aus echten Partien Statistik - getrennt nach Partietyp, nicht automatisch produktiv.

Grundlage ist das anonymisierte Battlelog-Fixture: 17 Partien, davon 4
soloRanked (Draft) und 13 aus der Trophaeen-Rangliste. Genau diese
Trennung wird hier geprueft - und dass die Zahlen nicht von selbst auf die
Seite wandern.
"""

import io
from datetime import date
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase

from drafter import config
from drafter.models import BrawlerStat, Datenquelle
from drafter.models.matches import Match, MatchPlayer
from drafter.services.aggregation.aggregator import Aggregator
from drafter.services.confidence import label, stichproben_confidence
from drafter.services.ingest.importer import MatchImporter
from drafter.services.katalog import brawler_abgleichen
from drafter.services.providers.fixture import FixtureDataProvider
from drafter.services.providers.registry import hole_stat_provider
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import FixtureMixin, katalog_aus_battlelog
from drafter.tests.test_offizieller_battlelog import lade

STICHTAG = date(2026, 9, 16)


class EchteStatistikTest(FixtureMixin, DrafterTest):
    def setUp(self):
        super().setUp()
        daten = lade()
        brawler_abgleichen(katalog_aus_battlelog(daten))
        MatchImporter(
            FixtureDataProvider(self.schreibe(daten)), katalog_ergaenzen=True,
        ).ausfuehren()

    def aggregiere(self):
        return Aggregator(
            (Datenquelle.FIXTURE,), stichtag=STICHTAG, rank_pools=["alle"], fenster=["90d"],
        ).ausfuehren()

    def global_zeilen(self):
        return BrawlerStat.objects.filter(
            source=Datenquelle.FIXTURE, window_label="90d", rank_pool="alle",
            game_mode__isnull=True, brawl_map__isnull=True,
        )

    def zaehlbare_soloranked(self):
        return Match.objects.filter(
            battle_type="soloRanked", winner_side__in=["a", "b"], has_conflict=False,
        )

    def test_nur_soloranked_wird_gezaehlt(self):
        partien = self.zaehlbare_soloranked().count()
        self.assertEqual(partien, 4, "Das Fixture enthält vier Ranked-Partien")
        self.aggregiere()
        self.assertEqual(
            sum(z.games for z in self.global_zeilen()), partien * 6,
            "Gezählt werden genau die Spielerzeilen der soloRanked-Partien",
        )

    def test_trophaeen_partie_zaehlt_auch_mit_falschem_ranked_flag_nicht(self):
        # Wenn `is_ranked` je falsch gesetzt wäre, hält der Partietyp dagegen.
        Match.objects.filter(battle_type="ranked").update(is_ranked=True)
        self.aggregiere()
        self.assertEqual(sum(z.games for z in self.global_zeilen()),
                         self.zaehlbare_soloranked().count() * 6)

    def test_brawler_nur_aus_trophaeen_partien_bekommen_keine_zeile(self):
        solo_ids = set(MatchPlayer.objects.filter(
            match__in=self.zaehlbare_soloranked()).values_list("brawler_id", flat=True))
        trophaeen_ids = set(MatchPlayer.objects.filter(
            match__battle_type="ranked").values_list("brawler_id", flat=True))
        self.assertTrue(trophaeen_ids - solo_ids, "Es gibt reine Trophäen-Brawler im Fixture")

        self.aggregiere()
        gezaehlt = set(self.global_zeilen().values_list("brawler_id", flat=True))
        self.assertTrue(gezaehlt)
        self.assertEqual(gezaehlt - solo_ids, set())

    # Die Seite hat die Freigabe seit 2026-09-16 gesetzt (settings.py).
    # Geprueft wird hier der MECHANISMUS - deshalb ausdruecklich ohne sie.
    @mock.patch.object(config, "GEMESSENE_STATS_FREIGEGEBEN", False)
    def test_aggregation_macht_die_seite_nicht_produktiv(self):
        self.aggregiere()
        self.assertTrue(self.global_zeilen().exists())
        self.assertEqual(
            hole_stat_provider("auto").name, "demo",
            "Ohne Freigabe bleibt die Oberfläche bei den Demo-Daten",
        )

    @mock.patch.object(config, "GEMESSENE_STATS_FREIGEGEBEN", False)
    def test_vergleichsbericht_beschreibt_und_aktiviert_nichts(self):
        self.aggregiere()
        ziel = self.verzeichnis / "vergleich.md"
        call_command(
            "vergleiche_brawl_stats", "--quelle", "fixture", "--fenster", "90d",
            "--rank-pool", "alle", "--min-spiele", "1", "--ausgabe", str(ziel),
            stdout=io.StringIO(),
        )
        text = ziel.read_text(encoding="utf-8")
        for abschnitt in ("## Datenbasis", "## Brawler", "## Map + Modus", "## Counter",
                          "## Synergien", "## Engine", "## Was das heißt"):
            self.assertIn(abschnitt, text)
        self.assertIn("**nicht** aktiv", text)
        self.assertIn("DRAFTER_GEMESSENE_STATS_FREIGEGEBEN", text)
        self.assertEqual(hole_stat_provider("auto").name, "demo")


class KleineStichprobeTest(SimpleTestCase):
    def test_kleine_stichproben_heissen_nie_hoch(self):
        """Solange wenig gemessen wurde, darf nichts als belastbar erscheinen."""
        for spiele in (1, 20, 100, 500, 800):
            with self.subTest(spiele=spiele):
                self.assertNotEqual(label(stichproben_confidence(spiele)), "Hoch")

    def test_hoch_erst_bei_vielen_spielen(self):
        noetig = config.CONFIDENCE_STUFEN[0][0] ** 2 * config.CONFIDENCE_VOLL_AB
        self.assertEqual(label(stichproben_confidence(noetig + 1)), "Hoch")
