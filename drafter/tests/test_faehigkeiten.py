# -*- coding: utf-8 -*-
"""Fachquelle als Rueckfallebene - und was sie NICHT darf.

Kernsatz: Unknown ist nicht 0. Ein Brawler ohne Profil, der laut Map
Waende bricht, darf nicht als "bricht keine Waende" gelten - aber aus
"bricht Waende" darf auch keine Zahl entstehen.
"""

from drafter import config
from drafter.models import Brawler
from drafter.services import faehigkeiten as f
from drafter.tests.basis import DrafterTest


class AuskunftTest(DrafterTest):
    def setUp(self):
        self.ohne_profil = Brawler.objects.create(
            name="GRIFF", slug="griff-test", external_id="16000300",
            is_active=False, draft_rolle="anti_tank", draft_faehigkeiten=["wallbreak"],
        )
        self.unbekannt = Brawler.objects.create(
            name="NORI", slug="nori-test", external_id="16000301", is_active=False,
        )

    def test_profil_gewinnt_und_nennt_die_staerke(self):
        aus = f.auskunft(self.brawler("brock"), "wallbreak")
        self.assertEqual(aus.quelle, f.PROFILE)
        self.assertIsNotNone(aus.wert)

    def test_fachquelle_ersetzt_die_null(self):
        aus = f.auskunft(self.ohne_profil, "wallbreak")
        self.assertEqual(aus.quelle, f.FACHQUELLE)
        self.assertTrue(aus.vorhanden)
        self.assertIsNone(aus.wert, "aus 'kann das' wird keine Zahl")

    def test_fehlender_marker_in_der_quelle_ist_eine_aussage(self):
        aus = f.auskunft(self.ohne_profil, "knockback_stun")
        self.assertEqual(aus.quelle, f.FACHQUELLE)
        self.assertFalse(aus.vorhanden)

    def test_ohne_profil_und_ohne_quelle_bleibt_unknown(self):
        aus = f.auskunft(self.unbekannt, "wallbreak")
        self.assertEqual(aus.quelle, f.UNKNOWN)
        self.assertIsNone(aus.vorhanden)
        self.assertFalse(aus.bekannt)

    def test_qualitative_faehigkeiten_haben_nie_einen_wert(self):
        for key in ("pierce", "good_hyper", "special"):
            aus = f.auskunft(self.brawler("gale"), key)
            self.assertIsNone(aus.wert, key)


class WandabhaengigkeitTest(DrafterTest):
    def test_rolle_allein_reicht(self):
        thrower = Brawler.objects.create(
            name="GROM", slug="grom-test", external_id="16000302",
            is_active=False, draft_rolle="thrower",
        )
        sniper = Brawler.objects.create(
            name="MANDY", slug="mandy-test", external_id="16000303",
            is_active=False, draft_rolle="sniper",
        )
        hoch = f.wandabhaengigkeit(thrower)
        niedrig = f.wandabhaengigkeit(sniper)
        self.assertEqual(hoch.quelle, f.FACHQUELLE)
        self.assertGreater(hoch.wert, niedrig.wert)

    def test_ohne_rolle_und_ohne_profil_unknown(self):
        leer = Brawler.objects.create(name="X", slug="x-test", external_id="16000304",
                                      is_active=False)
        self.assertFalse(f.wandabhaengigkeit(leer).bekannt)

    def test_profil_fliesst_ein(self):
        self.assertTrue(f.wandabhaengigkeit(self.brawler("gale")).bekannt)


class WallbreakValueTest(DrafterTest):
    def karte_mit_waenden(self):
        return self.karte("hard-rock-mine")

    def test_ohne_faehigkeit_ist_der_wert_null_nicht_unknown(self):
        poco = self.brawler("poco")
        aus, _ = f.wallbreak_value(poco, [self.brawler("gale")], [self.brawler("bull")],
                                   self.karte_mit_waenden())
        self.assertEqual(aus.wert, 0.0)
        self.assertEqual(aus.quelle, f.PROFILE)

    def test_ohne_map_merkmale_unknown(self):
        karte = self.karte_mit_waenden()
        karte.traits = {}
        aus, grund = f.wallbreak_value(self.brawler("brock"), [self.brawler("gale")],
                                       [self.brawler("bull")], karte)
        self.assertFalse(aus.bekannt)
        self.assertIn("Wanddichte", grund)

    def test_vorzeichen_dreht_sich_mit_der_aufstellung(self):
        """Derselbe Kandidat, getauschte Teams - kein Brawler steht in der Regel."""
        brock = self.brawler("brock")
        wand_team = [self.brawler("barley")]     # Thrower: lebt von Wänden
        offen_team = [self.brawler("piper")]     # Sniper: will Sichtlinien
        karte = self.karte_mit_waenden()
        gegen_wandteam, _ = f.wallbreak_value(brock, offen_team, wand_team, karte)
        gegen_offenteam, _ = f.wallbreak_value(brock, wand_team, offen_team, karte)
        self.assertGreater(gegen_wandteam.wert, 0)
        self.assertLess(gegen_offenteam.wert, 0)

    def test_kandidat_ohne_profil_wird_ueber_die_fachquelle_bewertet(self):
        griff = Brawler.objects.create(
            name="GRIFF", slug="griff-test2", external_id="16000305", is_active=False,
            draft_rolle="anti_tank", draft_faehigkeiten=["wallbreak"],
        )
        aus, _ = f.wallbreak_value(griff, [self.brawler("piper")], [self.brawler("barley")],
                                   self.karte_mit_waenden())
        self.assertTrue(aus.bekannt)
        self.assertEqual(aus.quelle, f.FACHQUELLE)
        self.assertGreater(aus.wert, 0)
