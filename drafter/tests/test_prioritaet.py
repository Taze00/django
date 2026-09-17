# -*- coding: utf-8 -*-
"""Priorisierung nach Datenluecken - ohne Netz.

Geprueft wird die Richtung, nicht eine Rangliste: ein Spieler mit einem
Brawler ohne jede Datenlage muss vor einem mit lauter haeufigen stehen,
und Breite allein darf nicht gewinnen.
"""

import io
from unittest import mock

from django.core.management import call_command

from drafter import config
from drafter.models import Brawler, Datenquelle
from drafter.models.collector import TrackedPlayer
from drafter.models.matches import Match, MatchPlayer
from drafter.services.collector import Collector
from drafter.services.prioritaet import Datenluecken, Priorisierung, defizit
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import BASIS


class PrioritaetBasis(DrafterTest):
    def partie(self, paare_a, paare_b, minuten=0, modus=None, sieger="a"):
        """Eine zaehlbare soloRanked-Partie aus (brawler_slug, spieler_tag)-Paaren."""
        m = Match.objects.create(
            fingerprint=f"fp-{minuten}-{paare_a[0][1]}",
            source=Datenquelle.API, played_at=BASIS.replace(minute=minuten % 60),
            battle_type="soloRanked", is_ranked=True, winner_side=sieger,
            game_mode=modus or self.karte().game_mode, mode_name="Gem Grab",
        )
        for seite, paare in (("a", paare_a), ("b", paare_b)):
            for slug, tag in paare:
                MatchPlayer.objects.create(
                    match=m, side=seite, brawler=self.brawler(slug),
                    brawler_name=slug, player_tag=tag,
                )
        return m

    def spieler(self, tag, **extra):
        return TrackedPlayer.objects.create(tag=tag, **extra)


class DefizitTest(PrioritaetBasis):
    def test_defizit_ist_der_fehlende_anteil(self):
        ziel = config.PRIORITAET_ZIELE["brawler_global"]
        self.assertEqual(defizit(0, "brawler_global"), 1.0)
        self.assertEqual(defizit(ziel, "brawler_global"), 0.0)
        self.assertEqual(defizit(ziel * 2, "brawler_global"), 0.0)
        self.assertAlmostEqual(defizit(ziel // 2, "brawler_global"), 0.5, places=1)

    def test_nur_soloranked_zaehlt(self):
        self.partie([("gale", "#A")], [("bull", "#B")])
        trophy = self.partie([("gale", "#A")], [("bull", "#B")], minuten=5)
        Match.objects.filter(pk=trophy.pk).update(battle_type="ranked")
        luecken = Datenluecken()
        self.assertEqual(luecken.brawler_global[self.brawler("gale").id], 1)


class SpielerbewertungTest(PrioritaetBasis):
    def test_katalog_brawler_schlaegt_breite(self):
        """Ein Spieler mit einem Brawler ohne Daten steht vor dem Vielspieler."""
        haeufig = ["gale", "belle", "max", "bull", "buster"]
        for i, slug in enumerate(haeufig):
            self.partie([(slug, "#BREIT")], [("tick", "#X")], minuten=i)
        selten = Brawler.objects.create(name="COSMO", slug="cosmo", external_id="900",
                                        is_active=False)
        m = self.partie([("gale", "#SELTEN")], [("tick", "#Y")], minuten=30)
        MatchPlayer.objects.create(match=m, side="a", brawler=selten,
                                   brawler_name="COSMO", player_tag="#SELTEN")

        prio = Priorisierung(katalog_ids={selten.id})
        breit = prio.bewerte(self.spieler("#BREIT"))
        knapp = prio.bewerte(self.spieler("#SELTEN"))
        self.assertGreater(knapp.punkte, breit.punkte)
        self.assertEqual(knapp.katalog_brawler, ["COSMO"])

    def test_kappung_begrenzt_die_breite(self):
        grenze = config.PRIORITAET_MAX_BEITRAEGE["brawler_global"]
        viele = ["gale", "belle", "max", "bull", "buster", "tick", "sandy", "poco"]
        for i, slug in enumerate(viele):
            self.partie([(slug, "#VIEL")], [("brock", "#Z")], minuten=i)
        prio = Priorisierung(katalog_ids=set())
        bewertung = prio.bewerte(self.spieler("#VIEL"))
        global_beitraege = [b for b in bewertung.beitraege if b.kategorie == "brawler_global"]
        self.assertEqual(len(global_beitraege), grenze,
                         "nur die groessten Beitraege zaehlen")

    def test_map_ebene_fliesst_nicht_ein(self):
        self.assertEqual(config.PRIORITAET_GEWICHTE["brawler_map"], 0.0)
        prio = Priorisierung(katalog_ids=set())
        self.partie([("gale", "#A")], [("bull", "#B")])
        bewertung = prio.bewerte(self.spieler("#A"))
        self.assertFalse([b for b in bewertung.beitraege if b.kategorie == "brawler_map"])

    def test_rang_entscheidet_nur_den_gleichstand(self):
        self.partie([("gale", "#OHNE")], [("bull", "#MIT")])
        prio = Priorisierung(katalog_ids=set())
        ohne = prio.bewerte(self.spieler("#OHNE"))
        mit = prio.bewerte(self.spieler("#MIT", ranking_position=1, ranking_trophies=90000))
        self.assertLess(abs(mit.punkte - ohne.punkte), config.PRIORITAET_GEWICHTE["rang"] + 1e-9)

    def test_nur_nie_abgefragte_spieler(self):
        self.partie([("gale", "#OFFEN")], [("bull", "#SCHON")])
        self.spieler("#OFFEN")
        self.spieler("#SCHON", last_fetched_at=BASIS)
        tags = {b.tag for b in Priorisierung(katalog_ids=set()).rangliste()}
        self.assertIn("#OFFEN", tags)
        self.assertNotIn("#SCHON", tags)

    def test_fuer_brawler_findet_nur_passende_spieler(self):
        self.partie([("gale", "#GALE")], [("bull", "#BULL")])
        self.spieler("#GALE")
        self.spieler("#BULL")
        prio = Priorisierung(katalog_ids=set())
        treffer = [b.tag for b in prio.fuer_brawler(self.brawler("gale"))]
        self.assertEqual(treffer, ["#GALE"])


class KommandoTest(PrioritaetBasis):
    def test_kommando_ruft_die_api_nicht_auf(self):
        self.partie([("gale", "#A")], [("bull", "#B")])
        self.spieler("#A")
        with mock.patch("drafter.services.brawl_api_client.BrawlApiClient.abrufen") as abruf:
            ausgabe = io.StringIO()
            call_command("collector_prioritaet", "--top", "5", stdout=ausgabe)
        abruf.assert_not_called()
        self.assertIn("nie abgefragt", ausgabe.getvalue())

    def test_brawlerabfrage_nennt_das_defizit(self):
        self.partie([("gale", "#A")], [("bull", "#B")])
        self.spieler("#A")
        ausgabe = io.StringIO()
        call_command("collector_prioritaet", "--brawler", "gale", stdout=ausgabe)
        text = ausgabe.getvalue()
        self.assertIn("Gale", text)
        self.assertIn("#A", text)


class StrategieTest(PrioritaetBasis):
    def test_luecken_strategie_waehlt_den_spieler_mit_der_groessten_luecke(self):
        selten = Brawler.objects.create(name="COSMO", slug="cosmo", external_id="900",
                                        is_active=False)
        for i, slug in enumerate(["gale", "belle", "max"]):
            self.partie([(slug, "#BREIT")], [("tick", "#X")], minuten=i)
        m = self.partie([("gale", "#LUECKE")], [("tick", "#Y")], minuten=30)
        MatchPlayer.objects.create(match=m, side="a", brawler=selten,
                                   brawler_name="COSMO", player_tag="#LUECKE")
        self.spieler("#BREIT", depth=0, ranking_position=1)   # stünde sonst vorn
        self.spieler("#LUECKE", depth=1)

        standard = Collector(client=mock.Mock(einsatzbereit=True), strategie="standard")
        luecken = Collector(client=mock.Mock(einsatzbereit=True), strategie="luecken")
        self.assertEqual(standard._naechster(set()).tag, "#BREIT")
        self.assertEqual(luecken._naechster(set()).tag, "#LUECKE")

    def test_unbekannte_strategie_wird_abgewiesen(self):
        with self.assertRaises(ValueError):
            Collector(client=mock.Mock(einsatzbereit=True), strategie="zufall")

    def test_strategie_steht_im_laufbericht(self):
        collector = Collector(client=mock.Mock(einsatzbereit=True), strategie="luecken")
        self.assertEqual(collector._parameter()["strategie"], "luecken")
