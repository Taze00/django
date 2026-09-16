# -*- coding: utf-8 -*-
"""Zuordnung ueber IDs vor Namen, Partie-ID vor Zeittoleranz."""

import copy

from drafter.models import Brawler, BrawlMap
from drafter.models.matches import Match
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import FixtureMixin, partie

TEAM_A = ("gale", "belle", "max")
TEAM_B = ("buster", "gene", "tick")


class IdentitaetTest(FixtureMixin, DrafterTest):
    def setUp(self):
        super().setUp()
        # Ausgedachte IDs - ausschliesslich fuer diesen Test. Welche IDs die
        # offizielle API benutzt, ist nicht bekannt und wird nicht erfunden.
        for i, slug in enumerate(TEAM_A + TEAM_B + ("piper",), start=1):
            Brawler.objects.filter(slug=slug).update(external_id=f"TEST-B{i}")
        BrawlMap.objects.filter(slug="hard-rock-mine").update(external_id="TEST-K1")

    def _nur_ids(self, eintrag):
        """Dieselbe Partie, aber nur mit IDs statt Namen."""
        ids = dict(Brawler.objects.exclude(external_id=None).values_list("slug", "external_id"))
        neu = copy.deepcopy(eintrag)
        for seite in ("a", "b"):
            neu["teams"][seite] = [{"brawler_id": ids[s["brawler"]]} for s in neu["teams"][seite]]
        del neu["mode"], neu["map"]
        neu["map_id"] = "TEST-K1"
        return neu

    def test_namen_und_ids_fuehren_zur_selben_partie(self):
        mit_namen = partie(a=TEAM_A, b=TEAM_B)
        self.importiere(mit_namen)
        bericht = self.importiere(self._nur_ids(partie(a=TEAM_A, b=TEAM_B)))
        self.assertEqual(bericht.duplikate, 1)
        self.assertEqual(Match.objects.count(), 1)

    def test_id_hat_vorrang_vor_dem_namen(self):
        eintrag = partie(a=({"brawler": "belle", "brawler_id": "TEST-B1"}, "piper", "max"))
        bericht = self.importiere(eintrag)
        match = Match.objects.get()
        spieler = match.players.get(brawler_name="belle")
        self.assertEqual(spieler.brawler.slug, "gale", "Die ID TEST-B1 gehoert zu Gale")
        # Gezaehlt wird, WIE geliefert wurde: nur der erste Spieler kam mit
        # ID, die uebrigen fuenf mit Namen - auch wenn der Katalog fuer sie
        # ebenfalls IDs kennt.
        self.assertEqual(bericht.zuordnung_per_id, 1)
        self.assertEqual(bericht.zuordnung_per_name, 5)

    def test_unbekannte_id_faellt_auf_den_namen_zurueck(self):
        bericht = self.importiere(partie(a=({"brawler": "gale", "brawler_id": "UNBEKANNT"}, "belle", "max")))
        self.assertEqual(Match.objects.get().players.get(brawler_name="gale").brawler.slug, "gale")
        self.assertGreaterEqual(bericht.zuordnung_per_name, 1)

    def test_nur_id_ohne_katalogtreffer_bleibt_als_id_erhalten(self):
        bericht = self.importiere(partie(a=({"brawler_id": "NEU-99"}, "belle", "max")))
        self.assertIn("id:NEU-99", bericht.unbekannte_brawler)
        self.assertIsNone(Match.objects.get().players.get(brawler_name="id:NEU-99").brawler)

    def test_map_wird_ueber_die_id_zugeordnet(self):
        self.importiere(self._nur_ids(partie(a=TEAM_A, b=TEAM_B)))
        match = Match.objects.get()
        self.assertEqual(match.brawl_map.slug, "hard-rock-mine")
        self.assertEqual(match.game_mode.slug, "gem-grab")


class PartieIdVorToleranzTest(FixtureMixin, DrafterTest):
    """Die Partie-ID der Quelle schlaegt die Rekonstruktion aus Zeit und Teams."""

    def test_gleiche_partie_id_ist_dieselbe_partie_ohne_zeittoleranz(self):
        self.importiere(partie(external_id="SYNTH-7"))
        bericht = self.importiere(partie(minuten=180, external_id="SYNTH-7"))
        self.assertEqual(bericht.duplikate, 1)

    def test_verschiedene_partie_ids_sind_zwei_partien_trotz_gleicher_rekonstruktion(self):
        self.importiere(partie(external_id="SYNTH-1"))
        self.importiere(partie(external_id="SYNTH-2"))
        self.assertEqual(Match.objects.count(), 2)

    def test_sichtung_ohne_id_findet_partie_mit_id(self):
        self.importiere(partie(external_id="SYNTH-3"))
        bericht = self.importiere(partie())
        self.assertEqual(bericht.duplikate, 1)
        self.assertEqual(Match.objects.get().external_id, "SYNTH-3")

    def test_sichtung_mit_id_ergaenzt_partie_ohne_id(self):
        self.importiere(partie())
        bericht = self.importiere(partie(external_id="SYNTH-4"))
        self.assertEqual(bericht.duplikate, 1)
        match = Match.objects.get()
        self.assertEqual(match.external_id, "SYNTH-4")
        self.assertTrue(match.reconstructed_fingerprint)


class MigrationsRechnungTest(FixtureMixin, DrafterTest):
    def test_migration_rechnet_denselben_fingerprint_wie_der_importer(self):
        """Sonst wuerden bereits gespeicherte Partien nie wiedererkannt.

        Geprueft wird die JUENGSTE Rechnung (0009, sekundengenau). Aeltere
        Migrationen frieren die Regel ein, die zu ihrer Zeit galt - sie
        duerfen nicht mit dem heutigen Importer uebereinstimmen muessen.
        """
        import importlib
        from django.apps import apps

        modul = importlib.import_module("drafter.migrations.0009_fingerprint_sekundengenau")
        self.importiere(
            partie(a=TEAM_A, b=TEAM_B),
            partie(a=("Kit", "belle", "max"), karte="Unbekannte Testmap", minuten=30),
            partie(a=TEAM_B, b=TEAM_A, sieger="b", minuten=60),
        )
        erwartet = dict(Match.objects.values_list("id", "reconstructed_fingerprint"))
        self.assertTrue(all(erwartet.values()))

        Match.objects.update(reconstructed_fingerprint="")
        modul.neu_berechnen(apps, None)
        self.assertEqual(dict(Match.objects.values_list("id", "reconstructed_fingerprint")), erwartet)
