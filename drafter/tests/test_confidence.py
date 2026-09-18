"""Datenlage: kleine Stichproben duerfen nicht sicher wirken."""

from drafter import config
from drafter.services import confidence
from drafter.services.patch_weighting import bayes
from drafter.tests.basis import DrafterTest


class StichprobeTest(DrafterTest):
    def test_mehr_spiele_bedeuten_mehr_confidence(self):
        self.assertLess(
            confidence.stichproben_confidence(50),
            confidence.stichproben_confidence(5000),
        )

    def test_ohne_spiele_keine_confidence(self):
        self.assertEqual(confidence.stichproben_confidence(0), 0.0)

    def test_confidence_ist_gedeckelt(self):
        self.assertLessEqual(confidence.stichproben_confidence(10**9), 1.0)

    def test_zuwachs_flacht_ab(self):
        # Der Sprung 50 -> 500 muss groesser sein als 5000 -> 5450.
        frueh = confidence.stichproben_confidence(500) - confidence.stichproben_confidence(50)
        spaet = confidence.stichproben_confidence(5450) - confidence.stichproben_confidence(5000)
        self.assertGreater(frueh, spaet)


class BayesTest(DrafterTest):
    def test_kleine_stichprobe_wird_zur_mitte_gezogen(self):
        roh = 13 / 20
        geglaettet = bayes(20, 13)
        self.assertLess(geglaettet, roh)
        self.assertGreater(geglaettet, 0.5)

    def test_grosse_stichprobe_bleibt_fast_unveraendert(self):
        geglaettet = bayes(50000, 29500)      # 59 %
        self.assertAlmostEqual(geglaettet, 0.59, places=2)

    def test_62_prozent_aus_wenigen_spielen_schlagen_59_aus_vielen_nicht(self):
        """Der Fall aus der Aufgabenstellung, als Test."""
        wenige = bayes(150, 93)         # 62 % aus 150
        viele = bayes(30000, 17700)     # 59 % aus 30 000
        self.assertLess(wenige, viele)

    def test_ohne_spiele_gilt_der_prior(self):
        self.assertEqual(bayes(0, 0), config.PRIOR_RATE)


class EmpfehlungsConfidenceTest(DrafterTest):
    def test_demo_daten_werden_nie_als_sicher_ausgewiesen(self):
        for empfehlung in self.engine(gegner=["bull"]).empfehlungen():
            self.assertLessEqual(empfehlung.confidence, confidence.DEMO_DECKEL)
            self.assertNotEqual(empfehlung.confidence_label, "Hoch")

    def test_mehr_bekannter_draft_erhoeht_die_confidence(self):
        # Mit reinen Demo-Daten liegen beide Werte am Deckel - der
        # Zusammenhang waere dann nicht messbar. Also eine Statistik auf
        # "gemessen" stellen, damit der Deckel nicht greift. Seit es die
        # Freigabe gibt, reicht die Quelle dafuer nicht mehr: ohne sie
        # nimmt "auto" weiterhin die Demo-Daten.
        from unittest import mock

        from drafter.models import Brawler, BrawlerStat, Datenquelle
        from drafter.models.stats import CounterStat, SynergyStat
        BrawlerStat.objects.update(source=Datenquelle.AGGREGATED, confidence=0.8)
        # Die Paarwerte ebenso belastbar machen wie die Siegquoten. Seit
        # die Counter- und Synergie-Confidence aus der Stichprobe DES
        # PAARES kommt (2026-09-18), macht ein bekannter Draft die Aussage
        # nur dann sicherer, wenn zu den Matchups auch etwas bekannt ist.
        # Bliebe es bei geratenen Matchups, waere ein voller Draft zu
        # Recht unsicherer - dann pruefte dieser Test die Zahl der Picks
        # statt des Wissens. Die Quelle bleibt "demo": berechnete Counter
        # duerfen laut Constraint nur in kanonischer Richtung stehen.
        for modell in (CounterStat, SynergyStat):
            modell.objects.update(confidence=0.8)
        # Seit 2026-09-16 deckelt auch ein Demo-PROFIL die Confidence, nicht
        # nur ein reiner Demo-Datenraum. Manuell gepflegte Profile nicht.
        Brawler.objects.update(source=Datenquelle.MANUAL)

        with mock.patch.object(config, "GEMESSENE_STATS_FREIGEGEBEN", True):
            wenig = self.engine().empfehlungen()[0].confidence
            viel = self.engine(
                eigene=["gale"], gegner=["bull", "tick"]
            ).empfehlungen()[0].confidence
        self.assertGreater(viel, wenig)

    def test_erklaerung_nennt_die_demo_lage(self):
        engine = self.engine(gegner=["bull"])
        text = confidence.erklaerung(0.3, engine.raum, engine.ctx)
        self.assertIn("Demo", text)

    def test_schlechte_datenlage_zieht_den_score(self):
        # Die Unsicherheits-Komponente muss negativ beitragen.
        for empfehlung in self.engine(gegner=["bull"]).empfehlungen():
            self.assertLess(empfehlung.komponenten[config.K_UNCERTAINTY].beitrag, 0)
