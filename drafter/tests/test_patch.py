"""Patch- und Zeitgewichtung alter Statistiken."""

from datetime import date, timedelta

from drafter import config
from drafter.models import BrawlerBalanceChange, BrawlerStat, Patch
from drafter.services.patch_weighting import (
    patch_gewicht, statistik_gewicht, zeit_gewicht,
)
from drafter.tests.basis import DrafterTest


class ZeitgewichtTest(DrafterTest):
    def test_heutige_daten_zaehlen_voll(self):
        self.assertAlmostEqual(zeit_gewicht(date.today()), 1.0, places=3)

    def test_nach_einer_halbwertszeit_zaehlt_die_haelfte(self):
        alt = date.today() - timedelta(days=config.ZEIT_HALBWERTSZEIT_TAGE)
        self.assertAlmostEqual(zeit_gewicht(alt), 0.5, places=3)

    def test_alte_daten_zaehlen_wenig(self):
        self.assertLess(zeit_gewicht(date.today() - timedelta(days=180)), 0.01)


class PatchgewichtTest(DrafterTest):
    def setUp(self):
        self.alt = Patch.objects.create(
            name="Alt", released_on=date.today() - timedelta(days=60)
        )
        self.neu = Patch.objects.create(
            name="Neu", released_on=date.today() - timedelta(days=5)
        )
        self.gale = self.brawler("gale")

    def test_ohne_aenderung_bleiben_daten_gueltig(self):
        self.assertEqual(patch_gewicht(self.gale, self.alt, self.neu), 1.0)

    def test_rework_entwertet_alte_daten_fast_vollstaendig(self):
        BrawlerBalanceChange.objects.create(
            patch=self.neu, brawler=self.gale, is_rework=True,
        )
        gewicht = patch_gewicht(self.gale, self.alt, self.neu)
        self.assertLessEqual(gewicht, config.PATCH_GEWICHT["rework"])

    def test_kleine_aenderung_entwertet_kaum(self):
        BrawlerBalanceChange.objects.create(
            patch=self.neu, brawler=self.gale,
            severity=BrawlerBalanceChange.Severity.SMALL,
        )
        self.assertGreater(patch_gewicht(self.gale, self.alt, self.neu), 0.7)

    def test_mehrere_aenderungen_multiplizieren_sich(self):
        zwischen = Patch.objects.create(
            name="Zwischen", released_on=date.today() - timedelta(days=30)
        )
        for patch in (zwischen, self.neu):
            BrawlerBalanceChange.objects.create(
                patch=patch, brawler=self.gale,
                severity=BrawlerBalanceChange.Severity.MEDIUM,
            )
        erwartet = config.PATCH_GEWICHT["medium"] ** 2
        self.assertAlmostEqual(
            patch_gewicht(self.gale, self.alt, self.neu), erwartet, places=6
        )

    def test_aenderungen_vor_der_messung_zaehlen_nicht(self):
        # Was VOR dem Messzeitraum passiert ist, steckt bereits in den Daten.
        frueher = Patch.objects.create(
            name="Frueher", released_on=date.today() - timedelta(days=90)
        )
        BrawlerBalanceChange.objects.create(
            patch=frueher, brawler=self.gale, is_rework=True,
        )
        self.assertEqual(patch_gewicht(self.gale, self.alt, self.neu), 1.0)

    def test_veraenderter_brawler_verliert_meta_gewicht(self):
        stat = BrawlerStat.objects.create(
            brawler=self.gale, patch=self.alt, win_rate=0.60, confidence=0.8,
            window_end=date.today(),
        )
        ohne = statistik_gewicht(stat, self.gale, self.neu)
        BrawlerBalanceChange.objects.create(
            patch=self.neu, brawler=self.gale,
            severity=BrawlerBalanceChange.Severity.LARGE,
        )
        self.gale.refresh_from_db()
        mit = statistik_gewicht(stat, self.gale, self.neu)
        self.assertLess(mit, ohne)
