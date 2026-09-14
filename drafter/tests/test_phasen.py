"""Draft-Phasen: dieselbe Lage, andere Gewichte."""

from drafter import config
from drafter.services import draft_position
from drafter.tests.basis import DrafterTest


class PhasenerkennungTest(DrafterTest):
    def test_leerer_draft_mit_first_pick_ist_first_pick(self):
        self.assertEqual(self.context(first_pick=True).phase, config.PHASE_FIRST_PICK)

    def test_letzter_eigener_pick_ist_last_pick(self):
        ctx = self.context(eigene=["gale", "belle"], gegner=["bull", "tick"])
        self.assertEqual(ctx.phase, config.PHASE_LAST)

    def test_zweiter_pick_des_drafts_ist_noch_fruehe_phase(self):
        ctx = self.context(gegner=["bull"], first_pick=False)
        self.assertEqual(ctx.phase, config.PHASE_EARLY)


class GewichteTest(DrafterTest):
    def test_last_pick_gewichtet_counter_hoeher_als_first_pick(self):
        erst = config.gewichte_fuer(config.PHASE_FIRST_PICK)
        zuletzt = config.gewichte_fuer(config.PHASE_LAST)
        self.assertGreater(zuletzt[config.K_COUNTER], erst[config.K_COUNTER] * 5)
        self.assertGreater(zuletzt[config.K_TEAM_NEED], erst[config.K_TEAM_NEED])
        self.assertLess(zuletzt[config.K_FLEXIBILITY], erst[config.K_FLEXIBILITY])

    def test_bewertungsgewichte_ergeben_je_phase_eins(self):
        for phase in config.PHASEN_GEWICHTE:
            gewichte = config.gewichte_fuer(phase)
            summe = sum(
                w for k, w in gewichte.items() if k not in config.STRAF_KOMPONENTEN
            )
            self.assertAlmostEqual(summe, 1.0, places=6, msg=f"Phase {phase}")

    def test_strafgewichte_sind_betraege(self):
        # Wert UND Gewicht negativ wuerde aus jeder Strafe einen Bonus
        # machen - der Fehler faellt beim Lesen nicht auf.
        for phase, gewichte in config.PHASEN_GEWICHTE.items():
            for key in config.STRAF_KOMPONENTEN:
                self.assertGreater(gewichte[key], 0, msg=f"{phase}/{key}")


class PickReihenfolgeTest(DrafterTest):
    def test_blind_pick_wert_zaehlt_nur_am_anfang(self):
        mortis = self.brawler("mortis")   # blind 35, last 70, counter 85
        gale = self.brawler("gale")       # blind 72

        erst = self.context(first_pick=True)
        zuletzt = self.context(eigene=["belle", "max"], gegner=["bull", "tick"])

        mortis_erst = draft_position.komponente(mortis, erst).wert
        mortis_zuletzt = draft_position.komponente(mortis, zuletzt).wert
        self.assertGreater(mortis_zuletzt, mortis_erst)

        gale_erst = draft_position.komponente(gale, erst).wert
        self.assertGreater(gale_erst, mortis_erst)

    def test_konterbarkeit_stoert_nur_solange_der_gegner_waehlen_darf(self):
        piper = self.brawler("piper")   # counterability 85
        offen = self.context(gegner=["bull"])
        geschlossen = self.context(
            eigene=["gale", "belle"], gegner=["bull", "tick", "gene"]
        )
        self.assertGreater(
            draft_position.komponente(piper, geschlossen).wert,
            draft_position.komponente(piper, offen).wert,
        )


class StrafenGreifenTest(DrafterTest):
    def test_strafkomponenten_senken_den_score(self):
        # Ein dritter Tank hat negative Straf-Beitraege; ihre Summe muss
        # sich im Gesamtscore wiederfinden.
        engine = self.engine(eigene=["bull", "frank"], gegner=["belle"])
        for e in engine.empfehlungen(anzahl=50):
            if e.brawler.slug != "rosa":
                continue
            strafen = sum(
                e.komponenten[k].beitrag for k in config.STRAF_KOMPONENTEN
            )
            self.assertLess(strafen, 0)
            ohne_strafen = e.score - strafen
            self.assertGreater(ohne_strafen, e.score)
            return
        self.fail("Rosa nicht in den Empfehlungen")
