"""Draft-Phasen: dieselbe Lage, andere Gewichte."""

from drafter import config
from drafter.models import Datenquelle
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
    """Die gepflegten Draftwerte speisen das Scoring nicht mehr.

    Bis zum 2026-09-20 kam die Draft-Position aus sechs von Hand
    eingetragenen Zahlen (`blind_pick_value`, `counterability`, …), die
    nur die zwanzig Demo-Brawler hatten - und die damit genau diese
    zwanzig bevorzugten. Die gemessene Ableitung
    (`gegnerabhaengigkeit`) traegt jetzt allein; ohne sie ist die
    Komponente **nicht verfuegbar** statt geschaetzt.

    Die Phasenlogik selbst ist damit nicht verschwunden, sie haengt nur
    an der Messung - geprueft in
    `test_infrastruktur.test_gemessene_ableitung_dreht_mit_der_phase`.
    """

    def test_demo_draftwerte_tragen_die_komponente_nicht_mehr(self):
        mortis = self.brawler("mortis")   # blind 35, last 70, counter 85
        self.assertTrue(mortis.hat_draftwerte, "die Werte stehen weiter in der DB")
        self.assertIsNotNone(mortis.draftwert("blind_pick_value"))

        for ctx in (self.context(first_pick=True),
                    self.context(eigene=["belle", "max"], gegner=["bull", "tick"])):
            komp = draft_position.komponente(mortis, ctx)
            self.assertIsNotNone(komp, "immer eine Komponente, nie None")
            self.assertFalse(komp.verfuegbar,
                             "ohne belastbare Quelle gibt es keine Draft-Position")
            self.assertEqual(komp.beitrag, 0.0)

    def test_belastbare_quelle_traegt_weiterhin(self):
        """Nicht die Werte sind verboten, sondern ihre Herkunft.

        Derselbe Brawler mit `source=manual` statt `demo` bekommt seine
        Draft-Position zurueck - die Regel haengt an der Quelle, nicht
        an einem Sonderfall fuer einzelne Namen.
        """
        mortis = self.brawler("mortis")
        mortis.source = Datenquelle.MANUAL
        mortis.save(update_fields=["source"])

        erst = draft_position.komponente(mortis, self.context(first_pick=True))
        zuletzt = draft_position.komponente(
            mortis, self.context(eigene=["belle", "max"], gegner=["bull", "tick"]))
        self.assertTrue(erst.verfuegbar)
        self.assertGreater(zuletzt.wert, erst.wert,
                           "spaeter Pick nutzt seine Konterstaerke")

    def test_konterbarkeit_stoert_nur_solange_der_gegner_waehlen_darf(self):
        piper = self.brawler("piper")   # counterability 85
        piper.source = Datenquelle.MANUAL
        piper.save(update_fields=["source"])
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
