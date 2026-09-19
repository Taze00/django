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
        """Bei gleich guten Komponenten macht ein bekannter Draft sicherer.

        Geprueft wird der Mechanismus, nicht das Feld: nimmt man zwei
        echte Lagen, kommen mit den Gegnern auch Matchups ohne gemessene
        Paardaten dazu (Heuristik-Confidence), und der Schnitt faellt - zu
        Recht. Die Aussage dieses Tests ist die andere: WENN das Wissen je
        Komponente gleich bleibt, zaehlt der Draftstand positiv.
        """
        from unittest import mock

        from drafter.models import Brawler, BrawlerStat, Datenquelle
        from drafter.services.scoring import Komponente

        # Ohne das greift der Demo-Deckel und beide Werte landen bei 0.35.
        BrawlerStat.objects.update(source=Datenquelle.AGGREGATED, confidence=0.8)
        Brawler.objects.update(source=Datenquelle.MANUAL)

        engine = self.engine()
        komponenten = {
            config.K_MAP_MODE: Komponente(key=config.K_MAP_MODE, gewicht=0.3,
                                          confidence=0.8),
            config.K_META: Komponente(key=config.K_META, gewicht=0.2, confidence=0.8),
        }
        with mock.patch.object(config, "GEMESSENE_STATS_FREIGEGEBEN", True):
            raum = self.engine().raum.laden()
            wenig = confidence.fuer_empfehlung(
                komponenten, self.context(), raum, self.brawler("gale"))
            viel = confidence.fuer_empfehlung(
                komponenten, self.context(eigene=["gale"], gegner=["bull", "tick"]),
                raum, self.brawler("gale"))
        self.assertGreater(viel, wenig)

    def test_erklaerung_nennt_die_demo_lage(self):
        engine = self.engine(gegner=["bull"])
        text = confidence.erklaerung(0.3, engine.raum, engine.ctx)
        self.assertIn("Demo", text)

    def test_datenlage_bestraft_nur_den_rueckstand_aufs_feld(self):
        """Seit 2026-09-18 ein Risikoabschlag, keine zweite Abwertung.

        `-(1 - confidence)` traf jeden Kandidaten, auch wenn alle gleich
        gut belegt waren - ein Sockel ohne Aussage, und fuer duenne
        Stichproben die dritte Strafe nach Shrinkage und niedriger
        Confidence. Jetzt zaehlt nur der Abstand nach unten zum Median.
        """
        empfehlungen = self.engine(gegner=["bull"]).empfehlungen(anzahl=200)
        beitraege = [e.komponenten[config.K_UNCERTAINTY].beitrag for e in empfehlungen]
        self.assertTrue(all(b <= 0 for b in beitraege), "nie ein Bonus")
        self.assertTrue(any(b == 0 for b in beitraege),
                        "wer mindestens so sicher ist wie das Feld, zahlt nichts")
        # Und der Abschlag folgt der Confidence, nicht dem Zufall.
        sicherster = max(empfehlungen, key=lambda e: e.confidence)
        unsicherster = min(empfehlungen, key=lambda e: e.confidence)
        self.assertGreaterEqual(
            sicherster.komponenten[config.K_UNCERTAINTY].beitrag,
            unsicherster.komponenten[config.K_UNCERTAINTY].beitrag)
