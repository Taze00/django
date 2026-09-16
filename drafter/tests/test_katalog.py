# -*- coding: utf-8 -*-
"""Katalog aus echten Antworten: IDs eintragen, nichts erfinden.

Die Brawler-IDs hier stammen aus der echten /brawlers-Antwort vom
2026-09-15; Modi und Maps aus dem anonymisierten Battlelog-Fixture.
"""

from django.test import SimpleTestCase
from django.urls import reverse

from drafter.models import Brawler, BrawlMap, Datenquelle, GameMode
from drafter.models.matches import Match, MatchPlayer
from drafter.services.ingest.fingerprint import katalog_schluessel
from drafter.services.ingest.importer import MatchImporter
from drafter.services.katalog import brawler_abgleichen, modus_anzeigename
from drafter.services.providers.fixture import FixtureDataProvider
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import FixtureMixin, katalog_aus_battlelog
from drafter.tests.test_offizieller_battlelog import lade, team_eintraege

GALE = {"id": 16000035, "name": "GALE"}
SHELLY = {"id": 16000000, "name": "SHELLY"}
ACHT_BIT = {"id": 16000034, "name": "8-BIT"}


class NamenTest(SimpleTestCase):
    def test_camelcase_wird_nur_getrennt_nicht_uebersetzt(self):
        self.assertEqual(modus_anzeigename("hotZone"), "Hot Zone")
        self.assertEqual(modus_anzeigename("brawlBall"), "Brawl Ball")
        self.assertEqual(modus_anzeigename("knockout"), "Knockout")


class BrawlerAbgleichTest(DrafterTest):
    def test_demo_brawler_bekommt_seine_id_und_behaelt_das_profil(self):
        gale = self.brawler("gale")
        vorher = (gale.name, gale.role, gale.tags, gale.attributes, gale.draft_values,
                  gale.source, gale.is_active)
        ergebnis = brawler_abgleichen([GALE])
        gale.refresh_from_db()
        self.assertEqual(gale.external_id, "16000035")
        self.assertEqual(
            (gale.name, gale.role, gale.tags, gale.attributes, gale.draft_values,
             gale.source, gale.is_active),
            vorher, "Der Abgleich setzt nur die ID - sonst nichts",
        )
        self.assertEqual(len(ergebnis.verknuepft), 1)
        self.assertEqual(ergebnis.neu, [])

    def test_neuer_brawler_kommt_ohne_profil_und_inaktiv(self):
        brawler_abgleichen([SHELLY])
        shelly = Brawler.objects.get(external_id="16000000")
        self.assertEqual(shelly.name, "SHELLY")
        self.assertEqual(shelly.slug, "shelly")
        self.assertFalse(shelly.is_active)
        self.assertEqual(shelly.source, Datenquelle.API)
        self.assertEqual(shelly.attributes, {})
        self.assertEqual(shelly.draft_values, {})
        self.assertEqual(shelly.role, "")
        self.assertEqual(shelly.tags, [])

    def test_sonderzeichen_im_namen(self):
        brawler_abgleichen([ACHT_BIT])
        self.assertTrue(Brawler.objects.filter(slug="8-bit", external_id="16000034").exists())

    def test_zweiter_abgleich_aendert_nichts(self):
        brawler_abgleichen([GALE, SHELLY])
        anzahl = Brawler.objects.count()
        ergebnis = brawler_abgleichen([GALE, SHELLY])
        self.assertEqual(ergebnis.bestaetigt, 2)
        self.assertEqual(ergebnis.verknuepft, [])
        self.assertEqual(ergebnis.neu, [])
        self.assertEqual(Brawler.objects.count(), anzahl)

    def test_andere_id_ist_ein_konflikt_und_wird_nicht_ueberschrieben(self):
        gale = self.brawler("gale")
        gale.external_id = "999"
        gale.save(update_fields=["external_id"])
        ergebnis = brawler_abgleichen([GALE])
        gale.refresh_from_db()
        self.assertEqual(gale.external_id, "999")
        self.assertEqual(len(ergebnis.konflikte), 1)
        self.assertEqual(Brawler.objects.filter(external_id="16000035").count(), 0)

    def test_eintraege_ohne_id_oder_name_werden_uebersprungen(self):
        ergebnis = brawler_abgleichen([{"name": "OHNE ID"}, {"id": "16000000"}, "kaputt"])
        self.assertEqual(ergebnis.uebersprungen, 3)
        self.assertEqual(ergebnis.neu, [])

    def test_neue_brawler_erreichen_weder_engine_noch_oberflaeche(self):
        brawler_abgleichen([SHELLY])
        self.assertNotIn("shelly", {e.brawler.slug for e in self.alle()})
        katalog = self.client.get(reverse("drafter:api_katalog")).json()
        self.assertNotIn("shelly", {b["slug"] for b in katalog["brawler"]})


class KatalogErgaenzenTest(FixtureMixin, DrafterTest):
    def setUp(self):
        super().setUp()
        self.daten = lade()
        brawler_abgleichen(katalog_aus_battlelog(self.daten))

    def importiere(self, daten=None, **optionen):
        pfad = self.schreibe(daten or lade())
        return MatchImporter(FixtureDataProvider(pfad), **optionen).ausfuehren()

    def test_ohne_schalter_wird_nichts_angelegt(self):
        modi, maps = GameMode.objects.count(), BrawlMap.objects.count()
        self.importiere()
        self.assertEqual((GameMode.objects.count(), BrawlMap.objects.count()), (modi, maps))

    def test_modi_und_maps_bekommen_die_ids_aus_dem_battlelog(self):
        bericht = self.importiere(katalog_ergaenzen=True)
        for eintrag in team_eintraege(self.daten):
            e = eintrag["event"]
            karte = BrawlMap.objects.select_related("game_mode").get(external_id=str(e["id"]))
            self.assertEqual(karte.game_mode.external_id, str(e["modeId"]))
            self.assertEqual(katalog_schluessel(karte.name), katalog_schluessel(e["map"]))
        self.assertEqual(bericht.id_widersprueche, [])
        # Gepflegte Modi werden verknüpft, nicht verdoppelt.
        self.assertEqual(GameMode.objects.get(slug="brawl-ball").external_id, "5")
        self.assertEqual(GameMode.objects.filter(slug="brawl-ball").count(), 1)

    def test_neue_modi_und_maps_sind_inaktiv_und_ohne_anforderungen(self):
        self.importiere(katalog_ergaenzen=True)
        neue_modi = GameMode.objects.exclude(external_id=None).filter(is_active=False)
        self.assertTrue(neue_modi.exists(), "Der Battlelog enthält Modi ausserhalb des Demo-Katalogs")
        for modus in neue_modi:
            self.assertEqual(modus.base_requirements, {})
        for karte in BrawlMap.objects.filter(source=Datenquelle.API):
            self.assertFalse(karte.is_active)
            self.assertEqual(karte.requirements, {})
            self.assertEqual(karte.traits, {})

    def test_gepflegte_map_behaelt_ihre_anforderungen(self):
        undermine = BrawlMap.objects.get(slug="undermine")
        vorher = (undermine.name, undermine.requirements, undermine.traits,
                  undermine.source, undermine.is_active)
        self.importiere(katalog_ergaenzen=True)
        undermine.refresh_from_db()
        self.assertEqual(
            (undermine.name, undermine.requirements, undermine.traits,
             undermine.source, undermine.is_active),
            vorher,
        )

    def test_alles_ist_zugeordnet_und_die_ids_stehen_an_der_partie(self):
        self.importiere(katalog_ergaenzen=True)
        self.assertFalse(Match.objects.filter(brawl_map__isnull=True).exists())
        self.assertFalse(Match.objects.filter(game_mode__isnull=True).exists())
        self.assertFalse(Match.objects.filter(external_map_id="").exists())
        self.assertFalse(MatchPlayer.objects.filter(brawler__isnull=True).exists())
        self.assertFalse(MatchPlayer.objects.filter(external_brawler_id="").exists())

    def test_gleicher_name_mit_anderer_id_wird_ein_eigener_modus(self):
        """Gemessen: "brawlBall" gibt es mit modeId 5, 32 und 45 (3v3 und 5v5).

        Der Name unterscheidet die Modi also nicht - die ID schon.
        """
        self.importiere(katalog_ergaenzen=True)
        brawl_ball = GameMode.objects.get(slug="brawl-ball")
        self.assertEqual(brawl_ball.external_id, "5")

        daten = lade()
        eintrag = team_eintraege(daten)[0]
        eintrag["event"]["modeId"] = 999
        eintrag["event"]["id"] = 99999          # eigene Map, sonst widerspricht sie ihrem Modus
        eintrag["event"]["map"] = "Eigene Testmap"
        eintrag["battle"]["mode"] = eintrag["event"]["mode"] = "brawlBall"
        eintrag["battleTime"] = "20260101T120000.000Z"
        daten["antwort"]["items"] = [eintrag]
        bericht = self.importiere(daten, katalog_ergaenzen=True)

        neu = GameMode.objects.get(external_id="999")
        self.assertNotEqual(neu.id, brawl_ball.id)
        self.assertIn("999", neu.name)
        self.assertFalse(neu.is_active)
        self.assertEqual(bericht.id_widersprueche, [])
        brawl_ball.refresh_from_db()
        self.assertEqual(brawl_ball.external_id, "5")

    def test_dieselbe_id_mit_anderem_namen_wird_gemeldet(self):
        self.importiere(katalog_ergaenzen=True)
        daten = lade()
        eintrag = team_eintraege(daten)[0]
        eintrag["event"]["map"] = "Umbenannte Karte"
        eintrag["battleTime"] = "20260101T120000.000Z"
        daten["antwort"]["items"] = [eintrag]
        bericht = self.importiere(daten, katalog_ergaenzen=True)
        self.assertEqual(len(bericht.id_widersprueche), 1)
        self.assertIn("Umbenannte Karte", bericht.id_widersprueche[0])
        self.assertFalse(BrawlMap.objects.filter(name="Umbenannte Karte").exists())

    def test_trockenlauf_legt_nichts_an(self):
        modi, maps = GameMode.objects.count(), BrawlMap.objects.count()
        self.importiere(katalog_ergaenzen=True, trockenlauf=True)
        self.assertEqual((GameMode.objects.count(), BrawlMap.objects.count()), (modi, maps))
        self.assertEqual(Match.objects.count(), 0)
