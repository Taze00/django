"""Tests fuer fitness/streak.py.

Reine Funktionstests ohne Datenbank. `today` wird immer explizit
uebergeben, damit die Tests nicht vom Kalender der Testmaschine
abhaengen.

Fester Bezugsrahmen fuer alle Tests dieser Datei:

    Mo 17.08.2026   Di 18.   Mi 19.   Do 20.   Fr 21.   Sa 22.   So 23.
    (Vorwoche: Mo 10.08. bis So 16.08.)

Trainingstage sind, wo nicht anders gesagt, Mo-Fr = [1,2,3,4,5].
"""

import datetime

from django.test import SimpleTestCase

from fitness.streak import calculate_streak, longest_streak

MO = datetime.date(2026, 8, 17)
DI = datetime.date(2026, 8, 18)
MI = datetime.date(2026, 8, 19)
DO = datetime.date(2026, 8, 20)
FR = datetime.date(2026, 8, 21)
SA = datetime.date(2026, 8, 22)
SO = datetime.date(2026, 8, 23)

VORWOCHE_FR = datetime.date(2026, 8, 14)
VORWOCHE_DO = datetime.date(2026, 8, 13)

MO_BIS_FR = [1, 2, 3, 4, 5]


class ZaehltGeplanteTrainingstageTest(SimpleTestCase):
    """Grundregel: nur Tage aus training_days zaehlen."""

    def test_volle_woche_trainiert_gibt_fuenf(self):
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, MI, DO, FR}, set(), today=FR
        )
        self.assertEqual(ergebnis["current"], 5)

    def test_wochenende_unterbricht_nicht(self):
        """Am Sonntag steht die Serie der Vorwoche unveraendert - Sa und So
        sind keine Trainingstage und werden vollstaendig uebersprungen."""
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, MI, DO, FR}, set(), today=SO
        )
        self.assertEqual(ergebnis["current"], 5)
        self.assertFalse(ergebnis["is_training_day_today"])

    def test_training_an_einem_nicht_trainingstag_zaehlt_nicht(self):
        """Wer am Samstag trainiert, obwohl Sa kein Trainingstag ist,
        bekommt dafuer keinen Punkt."""
        ergebnis = calculate_streak(
            MO_BIS_FR, {SA}, set(), today=SO
        )
        self.assertEqual(ergebnis["current"], 0)

    def test_ohne_trainingstage_ist_die_serie_null(self):
        ergebnis = calculate_streak([], {MO, DI, MI}, set(), today=FR)
        self.assertEqual(ergebnis["current"], 0)

    def test_nur_zwei_trainingstage_pro_woche(self):
        # Mo + Do. Die Vorwoche ist ebenfalls voll trainiert.
        nur_mo_do = [1, 4]
        trainiert = {MO, DO, VORWOCHE_DO, datetime.date(2026, 8, 10)}
        ergebnis = calculate_streak(nur_mo_do, trainiert, set(), today=DO)
        self.assertEqual(ergebnis["current"], 4)

    def test_letzter_trainingstag_wird_gemeldet(self):
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, MI}, set(), today=MI
        )
        self.assertEqual(ergebnis["last_trained"], MI)

    def test_ohne_training_ist_last_trained_none(self):
        ergebnis = calculate_streak(MO_BIS_FR, set(), set(), today=FR)
        self.assertIsNone(ergebnis["last_trained"])
        self.assertEqual(ergebnis["current"], 0)


class HeuteNichtPausiertTest(SimpleTestCase):
    """RestDay = 'Heute nicht': entschuldigt, zaehlt nicht, bricht nicht."""

    def test_ein_ruhetag_bricht_die_serie_nicht(self):
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, DO, FR}, {MI}, today=FR
        )
        self.assertEqual(ergebnis["current"], 4)

    def test_ruhetag_zaehlt_selbst_nicht_mit(self):
        """Vier trainierte Tage plus ein Ruhetag ergeben 4, nicht 5."""
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, DO, FR}, {MI}, today=FR
        )
        self.assertNotEqual(ergebnis["current"], 5)

    def test_mehrere_ruhetage_hintereinander_brechen_nicht(self):
        """Di, Mi und Do am Stueck pausiert - Mo und Fr bleiben verbunden."""
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, FR}, {DI, MI, DO}, today=FR
        )
        self.assertEqual(ergebnis["current"], 2)

    def test_eine_ganze_woche_ruhetage_haelt_die_serie_der_vorwoche(self):
        trainiert = {VORWOCHE_FR, VORWOCHE_DO}
        ruhe = {MO, DI, MI, DO, FR}
        ergebnis = calculate_streak(MO_BIS_FR, trainiert, ruhe, today=FR)
        self.assertEqual(ergebnis["current"], 2)

    def test_nur_ruhetage_ohne_training_ergibt_null(self):
        ergebnis = calculate_streak(
            MO_BIS_FR, set(), {MO, DI, MI, DO, FR}, today=FR
        )
        self.assertEqual(ergebnis["current"], 0)

    def test_ruhetag_heute_wird_gemeldet(self):
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, MI, DO}, {FR}, today=FR
        )
        self.assertTrue(ergebnis["rested_today"])
        self.assertEqual(ergebnis["current"], 4)

    def test_training_und_ruhetag_am_selben_tag_zaehlt_als_training(self):
        """Beide Mengen enthalten den Tag - die Trainings-Pruefung steht
        zuerst, der Tag zaehlt also mit."""
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI}, {DI}, today=DI
        )
        self.assertEqual(ergebnis["current"], 2)
        self.assertTrue(ergebnis["trained_today"])
        self.assertTrue(ergebnis["rested_today"])


class EchterAbbruchTest(SimpleTestCase):
    """Ein geplanter Trainingstag ohne Workout und ohne Ruhetag bricht."""

    def test_verpasster_tag_bricht_die_serie(self):
        # Mi verpasst: nur Do und Fr zaehlen noch.
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, DO, FR}, set(), today=FR
        )
        self.assertEqual(ergebnis["current"], 2)

    def test_serie_endet_am_abbruch_und_zaehlt_nicht_darueber_hinaus(self):
        """Auch wenn davor eine lange Serie lag - der Bruch beendet sie."""
        lange_serie = {
            datetime.date(2026, 8, 3) + datetime.timedelta(days=n)
            for n in range(12)
        }
        trainiert = (lange_serie | {DO, FR}) - {MI}
        ergebnis = calculate_streak(MO_BIS_FR, trainiert, set(), today=FR)
        self.assertEqual(ergebnis["current"], 2)

    def test_gestern_verpasst_ergibt_null(self):
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, MI}, set(), today=FR
        )
        self.assertEqual(ergebnis["current"], 0)

    def test_abbruch_setzt_last_trained_nicht(self):
        """Wird die Serie sofort gebrochen, bleibt last_trained None -
        auch wenn frueher durchaus trainiert wurde."""
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI}, set(), today=FR
        )
        self.assertEqual(ergebnis["current"], 0)
        self.assertIsNone(ergebnis["last_trained"])


class HeuteIstSonderfallTest(SimpleTestCase):
    """Heute bricht nie - der Tag ist noch nicht vorbei."""

    def test_heute_noch_nicht_trainiert_bricht_nicht(self):
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, MI, DO}, set(), today=FR
        )
        self.assertEqual(ergebnis["current"], 4)
        self.assertFalse(ergebnis["trained_today"])

    def test_heute_trainiert_zaehlt_sofort_mit(self):
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, MI, DO, FR}, set(), today=FR
        )
        self.assertEqual(ergebnis["current"], 5)
        self.assertTrue(ergebnis["trained_today"])

    def test_flags_an_einem_freien_tag(self):
        ergebnis = calculate_streak(MO_BIS_FR, set(), set(), today=SA)
        self.assertFalse(ergebnis["is_training_day_today"])
        self.assertFalse(ergebnis["trained_today"])
        self.assertFalse(ergebnis["rested_today"])


class DatumsgrenzenTest(SimpleTestCase):
    """Die Berechnung arbeitet auf datetime.date und rechnet selbst KEINE
    Zeitzone um. Beide Seiten - `today` und die trainierten Tage - muessen
    im selben Bezugssystem stehen; darum kuemmert sich der Aufrufer."""

    def test_gleicher_eingabetag_gibt_immer_dasselbe_ergebnis(self):
        args = (MO_BIS_FR, {MO, DI, MI, DO, FR}, set())
        self.assertEqual(
            calculate_streak(*args, today=FR),
            calculate_streak(*args, today=FR),
        )

    def test_ein_tag_versatz_aendert_das_ergebnis(self):
        """Faellt ein Workout durch die Datumsgrenze auf den Vortag, sieht
        die Serie anders aus. Das haelt fest, wie empfindlich die Rechnung
        auf die Tageszuordnung reagiert."""
        auf_freitag = calculate_streak(
            MO_BIS_FR, {MO, DI, MI, DO, FR}, set(), today=FR
        )
        auf_donnerstag = calculate_streak(
            MO_BIS_FR, {MO, DI, MI, DO}, set(), today=FR
        )
        self.assertEqual(auf_freitag["current"], 5)
        self.assertEqual(auf_donnerstag["current"], 4)

    def test_datetime_statt_date_wuerde_nicht_greifen(self):
        """Die Mengen werden per Gleichheit geprueft. Ein datetime ist
        nie gleich einem date - wer versehentlich datetime-Objekte
        einspeist, bekommt lautlos eine Serie von 0."""
        als_datetime = {datetime.datetime(2026, 8, 21, 18, 0)}
        ergebnis = calculate_streak(MO_BIS_FR, als_datetime, set(), today=FR)
        self.assertEqual(ergebnis["current"], 0)

    def test_monatsgrenze_wird_korrekt_ueberschritten(self):
        # Di 01.09.2026 zurueck ueber den Monatswechsel nach Mo 31.08.
        di_september = datetime.date(2026, 9, 1)
        mo_august = datetime.date(2026, 8, 31)
        ergebnis = calculate_streak(
            MO_BIS_FR, {mo_august, di_september}, set(), today=di_september
        )
        self.assertEqual(ergebnis["current"], 2)

    def test_jahreswechsel_wird_korrekt_ueberschritten(self):
        do_neujahr = datetime.date(2027, 1, 1)  # Freitag
        mi_silvester = datetime.date(2026, 12, 31)  # Donnerstag
        ergebnis = calculate_streak(
            MO_BIS_FR, {mi_silvester, do_neujahr}, set(), today=do_neujahr
        )
        self.assertEqual(ergebnis["current"], 2)

    def test_max_lookback_begrenzt_die_suche(self):
        """Mit max_lookback=1 wird nur heute betrachtet."""
        ergebnis = calculate_streak(
            MO_BIS_FR, {MO, DI, MI, DO, FR}, set(), today=FR, max_lookback=1
        )
        self.assertEqual(ergebnis["current"], 1)


class LongestStreakTest(SimpleTestCase):
    """longest_streak laeuft vorwaerts durch dasselbe Fenster."""

    def test_ununterbrochene_woche(self):
        self.assertEqual(
            longest_streak(MO_BIS_FR, {MO, DI, MI, DO, FR}, set(), today=FR),
            5,
        )

    def test_laengster_lauf_wird_gefunden_nicht_der_letzte(self):
        """Drei am Stueck in der Vorwoche, danach ein Bruch, dann zwei."""
        trainiert = {
            datetime.date(2026, 8, 10),
            datetime.date(2026, 8, 11),
            datetime.date(2026, 8, 12),
            # 13.08. verpasst -> Bruch
            DO,
            FR,
        }
        self.assertEqual(
            longest_streak(MO_BIS_FR, trainiert, set(), today=FR), 3
        )

    def test_ruhetage_verbinden_auch_hier(self):
        self.assertEqual(
            longest_streak(MO_BIS_FR, {MO, DI, DO, FR}, {MI}, today=FR),
            4,
        )

    def test_ohne_training_ist_der_laengste_lauf_null(self):
        self.assertEqual(longest_streak(MO_BIS_FR, set(), set(), today=FR), 0)

    def test_heute_ungetraint_beendet_den_lauf_nicht(self):
        self.assertEqual(
            longest_streak(MO_BIS_FR, {MO, DI, MI, DO}, set(), today=FR),
            4,
        )

    def test_laengster_lauf_ist_nie_kleiner_als_der_aktuelle(self):
        faelle = [
            ({MO, DI, MI, DO, FR}, set()),
            ({MO, DI, DO, FR}, {MI}),
            ({MO, FR}, {DI, MI, DO}),
            ({MO, DI}, set()),
        ]
        for trainiert, ruhe in faelle:
            with self.subTest(trainiert=sorted(trainiert)):
                aktuell = calculate_streak(
                    MO_BIS_FR, trainiert, ruhe, today=FR
                )["current"]
                laengster = longest_streak(
                    MO_BIS_FR, trainiert, ruhe, today=FR
                )
                self.assertGreaterEqual(laengster, aktuell)
