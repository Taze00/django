"""Tests fuer fitness/calibration.py.

Reine Funktionstests ohne Datenbank - calibrate_level() braucht nur
Objekte mit .level und .target_value.

Diese Tests halten das BESTEHENDE Verhalten fest. Sie sind als Netz
fuer das Django-Upgrade gedacht, nicht als Urteil darueber, ob die
Schwellen richtig gewaehlt sind.
"""

from django.test import SimpleTestCase

from fitness.calibration import calibrate_level


class FakeProgression:
    """Minimal-Attrappe: calibrate_level liest nur .level und .target_value."""

    def __init__(self, level, target_value):
        self.level = level
        self.target_value = target_value


def sieben_level(target=10):
    """Sieben Progressionen mit gleichem Zielwert - so isoliert der Test
    die Verhaeltnis-Logik von der Frage, welches Level welches Ziel hat."""
    return [FakeProgression(level, target) for level in range(1, 8)]


class BandGrenzenTest(SimpleTestCase):
    """Die fuenf Baender aus _ADJUSTMENT_BANDS, jeweils an der Kante.

    ratio = test_result / target_value
        >= 3.0        -> +2
        2.0 .. < 3.0  -> +1
        0.85 .. < 2.0 ->  0
        0.5 .. < 0.85 -> -1
        < 0.5         -> -2
    """

    def setUp(self):
        self.progs = sieben_level(target=10)

    def test_ratio_genau_3_0_gibt_zwei_hoch(self):
        # 30/10 = 3.0 - untere Kante des obersten Bandes.
        ergebnis = calibrate_level(self.progs, 3, 30)
        self.assertEqual(ergebnis["delta"], 2)
        self.assertEqual(ergebnis["calibrated_level"], 5)
        self.assertEqual(ergebnis["reason"], "up")

    def test_ratio_knapp_unter_3_0_gibt_nur_eins_hoch(self):
        # 29/10 = 2.9 - noch im +1-Band.
        ergebnis = calibrate_level(self.progs, 3, 29)
        self.assertEqual(ergebnis["delta"], 1)
        self.assertEqual(ergebnis["calibrated_level"], 4)

    def test_ratio_genau_2_0_gibt_eins_hoch(self):
        ergebnis = calibrate_level(self.progs, 3, 20)
        self.assertEqual(ergebnis["delta"], 1)
        self.assertEqual(ergebnis["calibrated_level"], 4)

    def test_ratio_knapp_unter_2_0_bleibt(self):
        # 19/10 = 1.9 - obere Kante des Halte-Bandes.
        ergebnis = calibrate_level(self.progs, 3, 19)
        self.assertEqual(ergebnis["delta"], 0)
        self.assertEqual(ergebnis["reason"], "stay")

    def test_ratio_genau_0_85_bleibt(self):
        # 8.5/10 - die Toleranzkante, ueber die der Modulkommentar redet.
        ergebnis = calibrate_level(sieben_level(target=100), 3, 85)
        self.assertEqual(ergebnis["delta"], 0)
        self.assertEqual(ergebnis["reason"], "stay")

    def test_ratio_knapp_unter_0_85_gibt_eins_runter(self):
        ergebnis = calibrate_level(sieben_level(target=100), 3, 84)
        self.assertEqual(ergebnis["delta"], -1)
        self.assertEqual(ergebnis["calibrated_level"], 2)
        self.assertEqual(ergebnis["reason"], "down")

    def test_ratio_genau_0_5_gibt_eins_runter(self):
        ergebnis = calibrate_level(self.progs, 3, 5)
        self.assertEqual(ergebnis["delta"], -1)
        self.assertEqual(ergebnis["calibrated_level"], 2)

    def test_ratio_knapp_unter_0_5_gibt_zwei_runter(self):
        ergebnis = calibrate_level(sieben_level(target=100), 3, 49)
        self.assertEqual(ergebnis["delta"], -2)
        self.assertEqual(ergebnis["calibrated_level"], 1)

    def test_ziel_genau_getroffen_bleibt(self):
        ergebnis = calibrate_level(self.progs, 4, 10)
        self.assertEqual(ergebnis["delta"], 0)
        self.assertEqual(ergebnis["calibrated_level"], 4)


class RandfaelleTest(SimpleTestCase):
    """Ergebnis 0, Ergebnis weit ueber Ziel, erste und letzte Progression."""

    def setUp(self):
        self.progs = sieben_level(target=10)

    def test_ergebnis_null_gibt_zwei_runter(self):
        ergebnis = calibrate_level(self.progs, 5, 0)
        self.assertEqual(ergebnis["delta"], -2)
        self.assertEqual(ergebnis["calibrated_level"], 3)
        self.assertEqual(ergebnis["reason"], "down")

    def test_ergebnis_weit_ueber_ziel_gibt_zwei_hoch(self):
        # 200/10 = 20.0 - weit jenseits des obersten Bandes, trotzdem max +2.
        ergebnis = calibrate_level(self.progs, 2, 200)
        self.assertEqual(ergebnis["delta"], 2)
        self.assertEqual(ergebnis["calibrated_level"], 4)

    def test_erste_progression_kann_nicht_tiefer_und_meldet_stay(self):
        """Wichtiger Grenzfall: auf Level 1 wird ein katastrophales Ergebnis
        zu delta 0 und reason 'stay', weil nach unten geklemmt wird.

        Der Nutzer faellt also nicht durch - er bekommt aber auch keine
        Rueckmeldung, dass er das Ziel klar verfehlt hat."""
        ergebnis = calibrate_level(self.progs, 1, 0)
        self.assertEqual(ergebnis["calibrated_level"], 1)
        self.assertEqual(ergebnis["delta"], 0)
        self.assertEqual(ergebnis["reason"], "stay")

    def test_zweite_progression_faellt_nur_bis_level_eins(self):
        # Von Level 2 aus waeren es -2, geklemmt bleibt -1.
        ergebnis = calibrate_level(self.progs, 2, 0)
        self.assertEqual(ergebnis["calibrated_level"], 1)
        self.assertEqual(ergebnis["delta"], -1)
        self.assertEqual(ergebnis["reason"], "down")

    def test_letzte_progression_kann_nicht_hoeher_und_meldet_stay(self):
        ergebnis = calibrate_level(self.progs, 7, 500)
        self.assertEqual(ergebnis["calibrated_level"], 7)
        self.assertEqual(ergebnis["delta"], 0)
        self.assertEqual(ergebnis["reason"], "stay")

    def test_vorletzte_progression_steigt_nur_bis_zum_maximum(self):
        ergebnis = calibrate_level(self.progs, 6, 500)
        self.assertEqual(ergebnis["calibrated_level"], 7)
        self.assertEqual(ergebnis["delta"], 1)


class ClampingUndEingabenTest(SimpleTestCase):
    """Selbsteinschaetzung ausserhalb der Spanne, negative und krumme Werte."""

    def setUp(self):
        self.progs = sieben_level(target=10)

    def test_selbsteinschaetzung_ueber_maximum_wird_geklemmt(self):
        ergebnis = calibrate_level(self.progs, 99, 10)
        self.assertEqual(ergebnis["self_assessed_level"], 7)
        self.assertEqual(ergebnis["calibrated_level"], 7)

    def test_selbsteinschaetzung_unter_minimum_wird_geklemmt(self):
        ergebnis = calibrate_level(self.progs, -5, 10)
        self.assertEqual(ergebnis["self_assessed_level"], 1)

    def test_negatives_ergebnis_wird_auf_null_geklemmt(self):
        ergebnis = calibrate_level(self.progs, 4, -20)
        self.assertEqual(ergebnis["test_result"], 0)
        self.assertEqual(ergebnis["delta"], -2)

    def test_krummes_ergebnis_wird_abgeschnitten_nicht_gerundet(self):
        # int(19.9) == 19 -> ratio 1.99 -> bleibt. Waere gerundet worden,
        # ergaebe 20 ein ratio von 2.0 und damit einen Aufstieg.
        ergebnis = calibrate_level(self.progs, 3, 19.9)
        self.assertEqual(ergebnis["test_result"], 19)
        self.assertEqual(ergebnis["delta"], 0)

    def test_zielwert_null_wird_als_eins_behandelt(self):
        # `target_value or 1` - ohne das gaebe es eine Division durch Null.
        progs = [FakeProgression(level, 0) for level in range(1, 8)]
        ergebnis = calibrate_level(progs, 3, 5)
        self.assertEqual(ergebnis["target_value"], 1)
        self.assertEqual(ergebnis["delta"], 2)

    def test_zielwert_none_wird_als_eins_behandelt(self):
        progs = [FakeProgression(level, None) for level in range(1, 8)]
        ergebnis = calibrate_level(progs, 3, 0)
        self.assertEqual(ergebnis["target_value"], 1)

    def test_ohne_progressionen_wird_value_error_geworfen(self):
        with self.assertRaises(ValueError):
            calibrate_level([], 3, 10)

    def test_unsortierte_eingabe_wird_sortiert(self):
        progs = list(reversed(sieben_level(target=10)))
        ergebnis = calibrate_level(progs, 7, 500)
        self.assertEqual(ergebnis["calibrated_level"], 7)

    def test_luecke_in_den_levels_faellt_auf_naechstes_zurueck(self):
        # Level 3 fehlt: die Selbsteinschaetzung 3 liegt in der Spanne 1..5,
        # wird also nicht geklemmt, findet aber keine eigene Progression.
        progs = [FakeProgression(lvl, 10) for lvl in (1, 2, 4, 5)]
        ergebnis = calibrate_level(progs, 3, 10)
        self.assertEqual(ergebnis["self_assessed_level"], 2)
        self.assertEqual(ergebnis["calibrated_level"], 2)


class RueckgabeformTest(SimpleTestCase):
    """Die Antwort wird direkt in die API-Antwort von /onboarding/calibrate/
    durchgereicht - ihre Form ist Teil des Vertrags."""

    def test_alle_schluessel_vorhanden(self):
        ergebnis = calibrate_level(sieben_level(), 3, 10)
        self.assertEqual(
            set(ergebnis),
            {
                "calibrated_level",
                "self_assessed_level",
                "delta",
                "target_value",
                "test_result",
                "reason",
            },
        )

    def test_zielwert_stammt_vom_selbsteingeschaetzten_level(self):
        # Nicht vom kalibrierten - der Vergleich findet gegen das Ziel
        # statt, das der Nutzer sich selbst zugetraut hat.
        progs = [FakeProgression(lvl, lvl * 10) for lvl in range(1, 8)]
        ergebnis = calibrate_level(progs, 4, 40)
        self.assertEqual(ergebnis["target_value"], 40)
        self.assertEqual(ergebnis["calibrated_level"], 4)

    def test_reason_ist_immer_einer_der_drei_werte(self):
        for test_result in (0, 5, 10, 20, 100):
            with self.subTest(test_result=test_result):
                ergebnis = calibrate_level(sieben_level(), 4, test_result)
                self.assertIn(ergebnis["reason"], {"up", "down", "stay"})
