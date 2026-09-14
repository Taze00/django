"""Siegchance: Grenzen einhalten, Vorteile abbilden, austauschbar bleiben."""

from drafter import config
from drafter.services import win_probability
from drafter.services.win_probability import (
    HeuristicWinProbabilityProvider, WinProbabilityProvider, hole_provider, setze_provider,
)
from drafter.tests.basis import DrafterTest


class GrenzenTest(DrafterTest):
    def test_wahrscheinlichkeit_bleibt_im_erlaubten_bereich(self):
        lagen = [
            {},
            dict(gegner=["bull"]),
            dict(eigene=["gale", "belle", "max"], gegner=["mortis", "stu", "piper"]),
            dict(eigene=["piper", "brock", "tick"], gegner=["gale", "sandy", "max"]),
        ]
        for lage in lagen:
            wert = self.engine(**lage).siegchance()["prozent"] / 100
            self.assertGreaterEqual(wert, config.WIN_UNTERGRENZE)
            self.assertLessEqual(wert, config.WIN_OBERGRENZE)

    def test_leerer_draft_ist_ausgeglichen(self):
        self.assertAlmostEqual(self.engine().siegchance()["prozent"], 50.0, places=1)

    def test_besserer_draft_erhoeht_die_chance(self):
        # Piper und Brock ohne Frontlinie gegen ein Team, das sie jagt.
        schlecht = self.engine(
            eigene=["piper", "brock"], gegner=["mortis", "stu"]
        ).siegchance()["prozent"]
        gut = self.engine(
            eigene=["gale", "rosa"], gegner=["mortis", "stu"]
        ).siegchance()["prozent"]
        self.assertGreater(gut, schlecht)

    def test_heuristik_wird_als_solche_ausgewiesen(self):
        siegchance = self.engine(gegner=["bull"]).siegchance()
        self.assertTrue(siegchance["ist_heuristik"])
        self.assertIn("heuristisch", siegchance["hinweis"].lower())


class ProviderTest(DrafterTest):
    def tearDown(self):
        setze_provider(HeuristicWinProbabilityProvider())

    def test_provider_ist_austauschbar(self):
        """Die Architekturzusage aus der Aufgabenstellung, als Test.

        Ein spaeteres ML-Modell muss die Heuristik ersetzen koennen,
        ohne dass Engine, Views oder Templates sich aendern.
        """
        class FestesModell(WinProbabilityProvider):
            ist_heuristik = False
            name = "test"

            def vorhersage(self, ctx, raum, eigene_analyse=None, gegner_analyse=None):
                return 0.73, 0.9

        setze_provider(FestesModell())
        siegchance = self.engine(gegner=["bull"]).siegchance()
        self.assertEqual(siegchance["prozent"], 73.0)
        self.assertFalse(siegchance["ist_heuristik"])
        self.assertEqual(siegchance["hinweis"], "")

    def test_standardprovider_ist_die_heuristik(self):
        setze_provider(None)
        self.assertIsInstance(hole_provider(), HeuristicWinProbabilityProvider)


class EmpfehlungsWahrscheinlichkeitTest(DrafterTest):
    def test_jede_empfehlung_traegt_eine_gueltige_wahrscheinlichkeit(self):
        for empfehlung in self.engine(eigene=["gale"], gegner=["bull"]).empfehlungen():
            self.assertGreaterEqual(empfehlung.win_probability, 0.0)
            self.assertLessEqual(empfehlung.win_probability, 1.0)

    def test_score_bleibt_in_seiner_skala(self):
        for empfehlung in self.engine(gegner=["bull"]).empfehlungen(anzahl=50):
            self.assertGreaterEqual(empfehlung.score, -1.0)
            self.assertLessEqual(empfehlung.score, 1.0)
            self.assertGreaterEqual(empfehlung.anzeige_score, 0)
            self.assertLessEqual(empfehlung.anzeige_score, 100)
