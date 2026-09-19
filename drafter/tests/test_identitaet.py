# -*- coding: utf-8 -*-
"""Einen Brawler aus einer Eingabe finden - ohne zu raten.

Die Web-App schickt Slugs aus ihrem eigenen Katalog. Ein Mensch tippt,
was er sieht: "WILLOW", "Larry & Lawrie", "R-T", "Mr. P". Beides muss auf
denselben Eintrag zeigen, und wo es mehrdeutig waere, muss es scheitern.
"""

import io

from django.core.management import call_command
from django.core.management.base import CommandError

from drafter.models import Brawler, Datenquelle, Praxisfall
from drafter.services.identitaet import Mehrdeutig, finde_brawler
from drafter.tests.basis import DrafterTest


class AufloesungTest(DrafterTest):
    def test_slug_name_und_schreibweise(self):
        gale = self.brawler("gale")
        for eingabe in ("gale", "GALE", "Gale", " gale "):
            self.assertEqual(finde_brawler(eingabe), gale, eingabe)

    def test_name_mit_sonderzeichen(self):
        """Der Fall aus dem Praxistest: 'Larry & Lawrie' ist kein Slug."""
        larry = Brawler.objects.create(name="LARRY & LAWRIE", slug="larry-lawrie",
                                       external_id="96001", is_active=True)
        for eingabe in ("larry-lawrie", "LARRY & LAWRIE", "Larry & Lawrie"):
            self.assertEqual(finde_brawler(eingabe), larry, eingabe)

    def test_punkt_und_bindestrich(self):
        """Exakter Name schlaegt kanonischen Schluessel - und ist eindeutig."""
        mrp = Brawler.objects.create(name="MR. P", slug="mr-p", external_id="96002",
                                     is_active=True)
        rt = Brawler.objects.create(name="R-T", slug="r-t", external_id="96003",
                                    is_active=True)
        for eingabe, erwartet in (("mr. p", mrp), ("MR. P", mrp), ("mr-p", mrp),
                                  ("r-t", rt), ("R-T", rt)):
            self.assertEqual(finde_brawler(eingabe), erwartet, eingabe)

    def test_externe_id(self):
        b = Brawler.objects.create(name="NORI", slug="nori", external_id="16000107",
                                   is_active=True)
        self.assertEqual(finde_brawler("16000107"), b)

    def test_unbekannt_ist_none(self):
        self.assertIsNone(finde_brawler("gibtsnicht"))
        self.assertIsNone(finde_brawler(""))
        self.assertIsNone(finde_brawler(None))

    def test_mehrdeutig_wird_gemeldet_statt_geraten(self):
        """Zwei verschiedene Namen, ein kanonischer Schluessel.

        `Brawler.name` ist eindeutig, zwei gleiche Namen kann es also
        nicht geben. Sehr wohl aber zwei Schreibweisen, die auf denselben
        Schluessel fallen - "MR. P" und "Mr P" werden beide zu `mr-p`.
        Dann wird gemeldet statt geraten.
        """
        Brawler.objects.create(name="Mr. P", slug="mr-p-eins", external_id="96010",
                               is_active=True)
        Brawler.objects.create(name="Mr P", slug="mr-p-zwei", external_id="96011",
                               is_active=True)
        # Weder Slug noch exakter Name treffen - erst der kanonische
        # Schluessel, und der passt auf beide.
        with self.assertRaises(Mehrdeutig) as fehler:
            finde_brawler("mr-p")
        self.assertIn("mr-p-eins", str(fehler.exception))
        self.assertIn("mr-p-zwei", str(fehler.exception))

    def test_inaktive_brawler_werden_gefunden(self):
        """Der Katalog kennt sie, die Engine bewertet sie - also auch hier."""
        b = Brawler.objects.create(name="KATALOG", slug="katalog", external_id="96020",
                                   is_active=False, source=Datenquelle.API)
        self.assertEqual(finde_brawler("KATALOG"), b)


class KommandoTest(DrafterTest):
    """Der Praxisfall-Befehl benutzt dieselbe Aufloesung."""

    def eintragen(self, **extra):
        call_command("praxisfall", map=self.karte().slug, stdout=io.StringIO(), **extra)
        return Praxisfall.objects.latest("id")

    def test_name_statt_slug(self):
        fall = self.eintragen(gewaehlt="Gale", eigene="SANDY")
        self.assertEqual(fall.gewaehlt, "gale")
        self.assertEqual(fall.own_picks, ["sandy"])

    def test_unbekannter_brawler_nennt_das_feld(self):
        with self.assertRaises(CommandError) as fehler:
            self.eintragen(gegner="gibtsnicht")
        self.assertIn("--gegner", str(fehler.exception))
        self.assertIn("gibtsnicht", str(fehler.exception))

    def test_mehrdeutige_eingabe_bricht_ab(self):
        Brawler.objects.create(name="Mr. P", slug="mr-p-eins", external_id="96030",
                               is_active=True)
        Brawler.objects.create(name="Mr P", slug="mr-p-zwei", external_id="96031",
                               is_active=True)
        with self.assertRaises(CommandError) as fehler:
            self.eintragen(gewaehlt="mr-p")
        self.assertIn("mehrdeutig", str(fehler.exception).lower())

    def test_konkurrenzliste_wird_ebenfalls_aufgeloest(self):
        fall = self.eintragen(konkurrenz="Gale, SANDY")
        self.assertEqual(fall.competitor_top, ["gale", "sandy"])
