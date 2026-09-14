"""Der Coach: Rollen, Aufgaben, Warnungen, Matchplan."""

from drafter.services import coach
from drafter.tests.basis import DrafterTest


class RollenTest(DrafterTest):
    def test_rolle_beschreibt_die_aufgabe_im_team(self):
        engine = self.engine(eigene=["belle"], gegner=["bull", "frank"])
        rolle = coach.rolle_im_team(self.brawler("gale"), engine.eigene_analyse)
        self.assertIn("Controller", rolle)
        self.assertIn("/", rolle)

    def test_dieselbe_figur_bekommt_je_nach_team_eine_andere_rolle(self):
        gegen_tanks = coach.rolle_im_team(
            self.brawler("gale"),
            self.engine(eigene=["belle"], gegner=["bull", "frank"]).eigene_analyse,
        )
        gegen_reichweite = coach.rolle_im_team(
            self.brawler("gale"),
            self.engine(eigene=["bull"], gegner=["piper", "brock"]).eigene_analyse,
        )
        self.assertNotEqual(gegen_tanks, gegen_reichweite)


class AufgabenTest(DrafterTest):
    def test_aufgaben_nennen_das_bevorzugte_matchup(self):
        engine = self.engine(eigene=["belle"], gegner=["bull"])
        aufgaben = coach.aufgaben(
            self.brawler("gale"), engine.ctx, engine.eigene_analyse, engine.raum
        )
        self.assertTrue(any("Bull" in a for a in aufgaben))

    def test_schutzauftrag_fuer_empfindliche_mitspieler(self):
        engine = self.engine(eigene=["piper"], gegner=["mortis"])
        aufgaben = coach.aufgaben(
            self.brawler("gale"), engine.ctx, engine.eigene_analyse, engine.raum
        )
        self.assertTrue(any("Piper" in a for a in aufgaben))

    def test_vermeiden_nennt_das_schlechte_matchup(self):
        engine = self.engine(gegner=["gale"])
        saetze = coach.vermeiden(self.brawler("mortis"), engine.ctx, engine.raum)
        self.assertTrue(any("Gale" in s for s in saetze))

    def test_warnungen_werden_erzeugt(self):
        engine = self.engine(eigene=["piper"], gegner=["mortis", "stu"])
        warnungen = coach.warnungen(self.brawler("piper"), engine.ctx, engine.raum)
        self.assertTrue(warnungen)

    def test_ohne_gegner_keine_erfundenen_warnungen(self):
        engine = self.engine()
        self.assertEqual(coach.warnungen(self.brawler("piper"), engine.ctx, engine.raum), [])


class MatchplanTest(DrafterTest):
    def test_zuordnung_maximiert_die_summe_nicht_das_einzelmatchup(self):
        engine = self.engine(
            eigene=["gale", "belle", "max"], gegner=["bull", "piper", "tick"]
        )
        zuordnung = coach.matchup_zuordnung(
            list(engine.ctx.own_picks), list(engine.ctx.enemy_picks), engine.raum
        )
        self.assertEqual(len(zuordnung), 3)
        # Jeder genau einmal - keine Doppelbelegung.
        self.assertEqual(len({z["unser"] for z in zuordnung}), 3)
        self.assertEqual(len({z["gegner"] for z in zuordnung}), 3)

    def test_endanalyse_ist_vollstaendig(self):
        analyse = self.engine(
            eigene=["gale", "belle", "max"], gegner=["buster", "gene", "tick"]
        ).endanalyse()
        self.assertEqual(len(analyse["team"]), 3)
        self.assertTrue(analyse["win_condition"])
        self.assertEqual(len(analyse["lanes"]), 3)
        self.assertTrue(analyse["matchups"])
        for spieler in analyse["team"]:
            self.assertTrue(spieler["rolle"])
            self.assertTrue(spieler["aufgaben"])

    def test_lane_tausch_plan_entsteht_bei_klaren_unterschieden(self):
        plan = self.engine(
            eigene=["gale", "piper", "max"], gegner=["mortis", "bull", "tick"]
        ).endanalyse()["lane_tausch"]
        self.assertTrue(plan)
        self.assertIn("wenn", plan[0])
        self.assertIn("dann", plan[0])
