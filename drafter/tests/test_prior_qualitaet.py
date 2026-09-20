# -*- coding: utf-8 -*-
"""Ein Prior ist so viel wert wie seine Herkunft.

Der Audit vom 2026-09-19 hat gezeigt: alle zwanzig Profile tragen
`source="demo"`, ihre `draft_values` stehen unveraendert so im Seed, und
die Fachquelle hat sie nie angefasst. Es sind Setzungen aus der
Aufbauphase - hilfreich, aber keine geprueften Aussagen.

Geprueft wird die Statik: ein geprueftes Profil darf ohne Messung mehr
behaupten als ein Demo-Wert, und mit wachsender Messung verschwinden
beide.
"""

from drafter import config
from drafter.models import Brawler, BrawlerStat, Datenquelle
from drafter.services import draft_position
from drafter.tests.basis import DrafterTest


class VerlaesslichkeitTest(DrafterTest):
    def brawler_mit(self, name, quelle):
        return Brawler.objects.create(
            name=name, slug=name.lower(), external_id=f"97{abs(hash(name)) % 10000:04d}",
            is_active=True, source=quelle,
            draft_values={"flexibility_value": 80, "blind_pick_value": 75,
                          "last_pick_value": 60, "counterability": 50,
                          "early_pick_value": 60, "counter_pick_value": 55},
        )

    # --- A bis E --------------------------------------------------------
    def test_a_demo_prior_ohne_messung(self):
        b = self.brawler_mit("DEMOA", Datenquelle.DEMO)
        self.assertEqual(draft_position.prior_verlaesslichkeit(b),
                         config.PRIOR_VERLAESSLICHKEIT["demo"])
        self.assertLess(draft_position.prior_verlaesslichkeit(b), 1.0,
                        "ein Demo-Wert ist kein geprueftes Wissen")

    def test_b_expert_prior_wirkt_staerker_als_demo(self):
        demo = self.brawler_mit("DEMOB", Datenquelle.DEMO)
        expert = self.brawler_mit("EXPERTB", Datenquelle.MANUAL)
        self.assertGreater(draft_position.prior_verlaesslichkeit(expert),
                           draft_position.prior_verlaesslichkeit(demo))
        # Gleicher Prior-Wert, verschiedene Wirkung.
        prior = 0.8
        self.assertGreater(prior * draft_position.prior_verlaesslichkeit(expert),
                           prior * draft_position.prior_verlaesslichkeit(demo))

    def test_c_und_d_messung_verdraengt_den_prior(self):
        wenig = draft_position.evidenzgewicht(50, config.DRAFTLAGE_EVIDENZ_K)
        viel = draft_position.evidenzgewicht(500, config.DRAFTLAGE_EVIDENZ_K)
        self.assertLess(wenig, viel)
        self.assertLess(wenig, 0.1, "50 Partien verdraengen kaum etwas")
        self.assertGreater(viel, 0.25)

    def test_e_mit_viel_messung_zaehlt_die_herkunft_kaum_noch(self):
        """Der Unterschied Demo/Expert schrumpft mit der Evidenz."""
        demo = config.PRIOR_VERLAESSLICHKEIT["demo"]
        expert = config.PRIOR_VERLAESSLICHKEIT["manual"]
        prior, gemessen = 0.8, -0.4
        def wert(r, n):
            w = draft_position.evidenzgewicht(n, config.DRAFTLAGE_EVIDENZ_K)
            return w * gemessen + (1 - w) * prior * r
        ohne_messung = abs(wert(expert, 0) - wert(demo, 0))
        viel_messung = abs(wert(expert, 3000) - wert(demo, 3000))
        self.assertGreater(ohne_messung, viel_messung)
        self.assertLess(viel_messung, ohne_messung * 0.5)

    # --- Struktur -------------------------------------------------------
    def test_demo_prior_schrumpft_richtung_neutral(self):
        """Der Wert verschwindet nicht, er behauptet nur weniger."""
        r = config.PRIOR_VERLAESSLICHKEIT["demo"]
        self.assertGreater(r, 0.0, "Demo-Wissen bleibt nutzbar")
        self.assertLess(r, 1.0, "aber nicht als gesicherte Wahrheit")

    def test_unbekannte_herkunft_zaehlt_am_wenigsten(self):
        b = self.brawler_mit("FREMD", "irgendwas")
        self.assertEqual(draft_position.prior_verlaesslichkeit(b),
                         config.PRIOR_VERLAESSLICHKEIT_UNBEKANNT)
        self.assertLessEqual(config.PRIOR_VERLAESSLICHKEIT_UNBEKANNT,
                             config.PRIOR_VERLAESSLICHKEIT["demo"])

    def test_ohne_profil_bleibt_der_prior_neutral(self):
        ohne = Brawler.objects.create(name="LEER", slug="leer", external_id="97999",
                                      is_active=True, source=Datenquelle.DEMO)
        self.assertFalse(ohne.hat_draftwerte)

    def test_komponente_weist_verlaesslichkeit_aus(self):
        """Wo ein Prior mitrechnet, muss seine Verlaesslichkeit dabeistehen.

        Seit dem 2026-09-20 ist der Prior der Flexibilitaet weg: er
        bestand aus den Demo-Draftwerten, die nicht mehr ins Scoring
        gehen. Die Komponente ist dann entweder rein gemessen oder gar
        nicht verfuegbar - ein Prior ohne Verlaesslichkeitsangabe darf
        es aber weiterhin nirgends geben.
        """
        from drafter.services.draft_engine import DraftEngine
        e = self.empfehlung(DraftEngine(self.context()).empfehlungen(anzahl=300), "gale")
        eintrag = next(k for k in e.als_dict()["komponenten"]
                       if k["key"] == config.K_FLEXIBILITY)
        if eintrag["prior_weight"]:
            self.assertIsNotNone(eintrag["prior_reliability"])
            self.assertAlmostEqual(
                eintrag["measured_weight"] + eintrag["prior_weight"], 1.0, places=6)
        else:
            self.assertIn(eintrag["quelle"], ("Measured", "Unknown"))

    def test_alle_gepflegten_profile_stammen_aus_dem_seed(self):
        """Haelt den Audit-Befund fest - faellt, sobald jemand pflegt."""
        quellen = {b.source for b in Brawler.objects.all() if b.hat_profil}
        self.assertEqual(quellen, {Datenquelle.DEMO},
                         "Sobald ein Profil geprueft gepflegt ist, gehoert es auf "
                         "source=manual - dann traegt es auch wieder voll.")
