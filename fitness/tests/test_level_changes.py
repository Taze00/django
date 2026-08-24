"""Tests fuer den Level-Wechsel beim Abschliessen eines Workouts.

Die Logik steht in WorkoutViewSet.complete (fitness/views.py) und wird
hier ueber den echten Endpunkt ausgeloest, damit auch das Zusammenspiel
mit UserExerciseProgression und LevelEvent mitgetestet wird.

Aufbau je Test: eine Uebung mit sieben Progressionen, ein Nutzer mit
einer Progression darauf, ein Workout von heute mit Satz 1 und Satz 2.

Diese Tests halten das BESTEHENDE Verhalten fest - auch dort, wo es
ueberraschend ist. Die auffaelligen Stellen sind im Code kommentiert.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import (
    Exercise,
    LevelEvent,
    Progression,
    UserExerciseProgression,
    Workout,
    WorkoutSet,
)


class LevelWechselBasis(TestCase):
    """Gemeinsamer Aufbau fuer alle Level-Wechsel-Tests."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="tester", password="geheim1234"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.uebung = Exercise.objects.create(
            name="Push-ups", category="PUSH", order=1
        )
        # Sieben Level, Zielwert steigt in Zehnerschritten: 10, 20, ... 70.
        self.progressionen = {
            level: Progression.objects.create(
                exercise=self.uebung,
                level=level,
                name=f"Stufe {level}",
                target_type="reps",
                target_value=level * 10,
                sets_required=2,
                sessions_required=3,
            )
            for level in range(1, 8)
        }

    def nutzer_auf_level(self, level, **kwargs):
        felder = {
            "sessions_at_target": 0,
            "is_first_session": False,
            "custom_target": None,
        }
        felder.update(kwargs)
        return UserExerciseProgression.objects.create(
            user=self.user,
            exercise=self.uebung,
            current_progression=self.progressionen[level],
            **felder,
        )

    def workout_mit_saetzen(self, uebung, progression, wert1, wert2,
                            feld="reps", nur_satz_eins=False):
        workout = Workout.objects.create(user=self.user)
        WorkoutSet.objects.create(
            workout=workout, exercise=uebung, progression=progression,
            set_number=1, is_drop_set=False, **{feld: wert1},
        )
        if not nur_satz_eins:
            WorkoutSet.objects.create(
                workout=workout, exercise=uebung, progression=progression,
                set_number=2, is_drop_set=False, **{feld: wert2},
            )
        return workout

    def abschliessen(self, workout):
        antwort = self.client.post(
            reverse("workout-complete", args=[workout.pk])
        )
        self.assertEqual(antwort.status_code, 200)
        return antwort.data


class AufstiegTest(LevelWechselBasis):
    """Ziel in beiden Saetzen erreicht, genug Sitzungen gesammelt."""

    def test_aufstieg_nach_der_geforderten_zahl_von_sitzungen(self):
        prog = self.nutzer_auf_level(3, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 30
        )

        daten = self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4)
        self.assertEqual(len(daten["upgrades"]), 1)
        self.assertEqual(daten["upgrades"][0]["from_level"], 3)
        self.assertEqual(daten["upgrades"][0]["to_level"], 4)

    def test_aufstieg_setzt_zaehler_und_marker_zurueck(self):
        prog = self.nutzer_auf_level(3, sessions_at_target=2, custom_target=25)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 30
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 0)
        self.assertIsNone(prog.custom_target)
        # Nach dem Aufstieg gilt die naechste Sitzung wieder als erste -
        # damit greift dort die Abstiegspruefung.
        self.assertTrue(prog.is_first_session)

    def test_aufstieg_schreibt_einen_level_event(self):
        self.nutzer_auf_level(3, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 30
        )

        self.abschliessen(workout)

        ereignis = LevelEvent.objects.get(
            user=self.user, event_type="level_up"
        )
        self.assertEqual(ereignis.from_level, 3)
        self.assertEqual(ereignis.to_level, 4)
        self.assertEqual(ereignis.progression_name, "Stufe 4")

    def test_noch_nicht_genug_sitzungen_zaehlt_nur_hoch(self):
        prog = self.nutzer_auf_level(3, sessions_at_target=0)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 30
        )

        daten = self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 1)
        self.assertEqual(prog.current_progression.level, 3)
        self.assertEqual(daten["upgrades"], [])

    def test_ziel_knapp_verfehlt_im_zweiten_satz_zaehlt_nicht(self):
        prog = self.nutzer_auf_level(3, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 29
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)
        self.assertEqual(prog.sessions_at_target, 0,
                         "eine verfehlte Sitzung setzt den Zaehler zurueck")

    def test_ueber_dem_ziel_zaehlt_wie_genau_am_ziel(self):
        prog = self.nutzer_auf_level(3, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 99, 99
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4)

    def test_eigenes_ziel_schlaegt_das_ziel_der_progression(self):
        """custom_target ersetzt target_value als Messlatte."""
        prog = self.nutzer_auf_level(3, sessions_at_target=2, custom_target=35)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 30
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        # 30 reicht fuer das Progressionsziel 30, nicht fuer das eigene 35.
        self.assertEqual(prog.current_progression.level, 3)


class MaximallevelTest(LevelWechselBasis):
    """Auf Level 7 ist Schluss - aber erst dort."""

    def test_von_level_sechs_wird_noch_aufgestiegen(self):
        """Die Grenze liegt bei 7, nicht darunter: Level 6 muss den
        letzten Schritt noch gehen duerfen."""
        prog = self.nutzer_auf_level(6, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[6], 60, 60
        )

        daten = self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 7)
        self.assertEqual(daten["upgrades"][0]["to_level"], 7)
        self.assertNotIn("is_max_level", daten["upgrades"][0])

    def test_auf_level_sieben_wird_nicht_weiter_aufgestiegen(self):
        prog = self.nutzer_auf_level(7, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[7], 70, 70
        )

        daten = self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 7)
        self.assertTrue(daten["upgrades"][0]["is_max_level"])

    def test_zaehler_wird_auf_level_sieben_zurueckgesetzt(self):
        prog = self.nutzer_auf_level(7, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[7], 70, 70
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 0)

    def test_kein_level_event_auf_dem_maximallevel(self):
        self.nutzer_auf_level(7, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[7], 70, 70
        )

        self.abschliessen(workout)

        self.assertFalse(
            LevelEvent.objects.filter(
                user=self.user, event_type="level_up"
            ).exists()
        )


class AbstiegTest(LevelWechselBasis):
    """Abstieg wird NUR in der ersten Sitzung auf einem Level geprueft."""

    def test_abstieg_bei_weniger_als_drei_wiederholungen(self):
        prog = self.nutzer_auf_level(3, is_first_session=True)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 2, 2
        )

        daten = self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)
        self.assertEqual(len(daten["downgrades"]), 1)
        self.assertEqual(daten["downgrades"][0]["from_level"], 3)
        self.assertEqual(daten["downgrades"][0]["to_level"], 2)

    def test_abstieg_allein_wegen_des_schwachen_ersten_satzes(self):
        """val1=2 reisst die Einzelbedingung (< 3), die Summe 2+10=12
        liegt klar ueber 5. Isoliert damit die erste der beiden
        Abstiegsbedingungen."""
        prog = self.nutzer_auf_level(3, is_first_session=True)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 2, 10
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)

    def test_abstieg_wenn_die_summe_unter_fuenf_liegt(self):
        """val1 ist mit 3 hoch genug, 3+1 = 4 reisst die zweite Bedingung."""
        prog = self.nutzer_auf_level(3, is_first_session=True)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 3, 1
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)
        # val1 ist weder 0, 1 noch 2 -> kein Zuschlag.
        self.assertEqual(prog.custom_target, 20)

    def test_zuschlag_auf_das_neue_ziel_je_nach_erstem_satz(self):
        """Je schwaecher der erste Satz, desto grosszuegiger das neue Ziel.
        Zielwert Level 2 ist 20."""
        for erster_satz, erwarteter_zuschlag in [(0, 6), (1, 4), (2, 2)]:
            with self.subTest(erster_satz=erster_satz):
                UserExerciseProgression.objects.filter(
                    user=self.user
                ).delete()
                Workout.objects.filter(user=self.user).delete()
                prog = self.nutzer_auf_level(3, is_first_session=True)
                workout = self.workout_mit_saetzen(
                    self.uebung, self.progressionen[3], erster_satz, 0
                )

                self.abschliessen(workout)

                prog.refresh_from_db()
                self.assertEqual(
                    prog.custom_target, 20 + erwarteter_zuschlag
                )

    def test_abstieg_setzt_zaehler_und_erstsitzungsmarker(self):
        prog = self.nutzer_auf_level(3, is_first_session=True,
                                     sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 0, 0
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 0)
        self.assertFalse(prog.is_first_session)

    def test_kein_abstieg_wenn_es_nicht_die_erste_sitzung_ist(self):
        """Dieselbe schwache Leistung, aber is_first_session=False:
        das Level bleibt stehen."""
        prog = self.nutzer_auf_level(3, is_first_session=False)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 0, 0
        )

        daten = self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)
        self.assertEqual(daten["downgrades"], [])

    def test_kein_abstieg_unter_level_eins(self):
        prog = self.nutzer_auf_level(1, is_first_session=True)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[1], 0, 0
        )

        daten = self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 1)
        self.assertEqual(daten["downgrades"], [])
        # Der Marker wird trotzdem geloescht.
        self.assertFalse(prog.is_first_session)

    def test_abstieg_schreibt_keinen_level_event(self):
        """Nur Aufstiege landen in der Zeitleiste - Abstiege nicht."""
        self.nutzer_auf_level(3, is_first_session=True)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 0, 0
        )

        self.abschliessen(workout)

        self.assertFalse(LevelEvent.objects.filter(user=self.user).exists())

    def test_gute_leistung_in_der_ersten_sitzung_steigt_normal_auf(self):
        """Die Abstiegspruefung laeuft zwar, greift aber nicht - danach
        wird ganz normal die Aufstiegspruefung erreicht."""
        prog = self.nutzer_auf_level(3, is_first_session=True,
                                     sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 30
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4)


class ZeitbasierteUebungTest(LevelWechselBasis):
    """Bei target_type='time' gelten andere Abstiegsschwellen."""

    def setUp(self):
        super().setUp()
        self.plank = Exercise.objects.create(
            name="Plank", category="CORE", order=3
        )
        self.plank_progs = {
            level: Progression.objects.create(
                exercise=self.plank,
                level=level,
                name=f"Plank {level}",
                target_type="time",
                target_value=level * 30,
                sets_required=2,
                sessions_required=3,
            )
            for level in range(1, 8)
        }

    def plank_nutzer(self, level, **kwargs):
        felder = {
            "sessions_at_target": 0,
            "is_first_session": False,
            "custom_target": None,
        }
        felder.update(kwargs)
        return UserExerciseProgression.objects.create(
            user=self.user,
            exercise=self.plank,
            current_progression=self.plank_progs[level],
            **felder,
        )

    def test_abstieg_wenn_unter_einem_drittel_des_ziels(self):
        # Level 2 -> Ziel 60s, ein Drittel sind 20s.
        prog = self.plank_nutzer(2, is_first_session=True)
        workout = self.workout_mit_saetzen(
            self.plank, self.plank_progs[2], 19, 19, feld="seconds"
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 1)

    def test_kein_abstieg_knapp_ueber_einem_drittel(self):
        # 20s ist nicht < 20; 20+50 = 70 ist nicht < 30.
        prog = self.plank_nutzer(2, is_first_session=True)
        workout = self.workout_mit_saetzen(
            self.plank, self.plank_progs[2], 20, 50, feld="seconds"
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)

    def test_abstieg_wenn_die_summe_unter_der_haelfte_liegt(self):
        # val1=25 ist ueber dem Drittel, 25+4 = 29 unter der Haelfte (30).
        prog = self.plank_nutzer(2, is_first_session=True)
        workout = self.workout_mit_saetzen(
            self.plank, self.plank_progs[2], 25, 4, feld="seconds"
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 1)

    def test_zeitzuschlag_je_nach_erstem_satz(self):
        """Zielwert Level 1 ist 30s. Zuschlaege: 0s->15, <6s->10, <11s->5."""
        for erster_satz, erwarteter_zuschlag in [(0, 15), (5, 10), (10, 5)]:
            with self.subTest(erster_satz=erster_satz):
                UserExerciseProgression.objects.filter(
                    user=self.user, exercise=self.plank
                ).delete()
                Workout.objects.filter(user=self.user).delete()
                prog = self.plank_nutzer(2, is_first_session=True)
                workout = self.workout_mit_saetzen(
                    self.plank, self.plank_progs[2], erster_satz, 0,
                    feld="seconds",
                )

                self.abschliessen(workout)

                prog.refresh_from_db()
                self.assertEqual(prog.custom_target, 30 + erwarteter_zuschlag)

    def test_aufstieg_bei_zeituebung(self):
        prog = self.plank_nutzer(2, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.plank, self.plank_progs[2], 60, 60, feld="seconds"
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)


class UnvollstaendigeDatenTest(LevelWechselBasis):
    """Was passiert, wenn Saetze fehlen oder leer sind."""

    def test_ohne_zweiten_satz_passiert_nichts(self):
        prog = self.nutzer_auf_level(3, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 0, nur_satz_eins=True
        )

        daten = self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)
        self.assertEqual(prog.sessions_at_target, 2)
        self.assertEqual(daten["upgrades"], [])
        self.assertEqual(daten["downgrades"], [])

    def test_ohne_progression_des_nutzers_passiert_nichts(self):
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 30
        )

        daten = self.abschliessen(workout)

        self.assertEqual(daten["upgrades"], [])
        self.assertEqual(daten["downgrades"], [])

    def test_leere_wiederholungen_zaehlen_als_null(self):
        prog = self.nutzer_auf_level(3, is_first_session=True)
        workout = Workout.objects.create(user=self.user)
        for satz in (1, 2):
            WorkoutSet.objects.create(
                workout=workout, exercise=self.uebung,
                progression=self.progressionen[3],
                set_number=satz, is_drop_set=False, reps=None,
            )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)

    def test_drop_set_wird_nicht_gewertet(self):
        """Satz 3 als Drop-Set: die Pruefung liest nur Satz 1 und 2."""
        prog = self.nutzer_auf_level(3, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 30
        )
        WorkoutSet.objects.create(
            workout=workout, exercise=self.uebung,
            progression=self.progressionen[3],
            set_number=3, is_drop_set=True, reps=1,
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4)


class ZaehlerVerhaltenTest(LevelWechselBasis):
    """Wie sich sessions_at_target ueber mehrere Sitzungen verhaelt."""

    def test_verfehltes_ziel_setzt_den_zaehler_zurueck(self):
        """Der Zaehler heisst sessions_at_target - er zaehlt Sitzungen AM
        ZIEL, nicht Sitzungen ueberhaupt. Wer zweimal trifft und dann
        verfehlt, faengt wieder bei null an.

        Frueher ueberlebte der Zaehler die schwache Sitzung, "3 Sitzungen am
        Ziel" hiess also in Wahrheit "3 jemals" - der Aufstieg kam irgendwann
        unabhaengig von Bestaendigkeit."""
        prog = self.nutzer_auf_level(3, sessions_at_target=2)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 5, 5
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 0)
        self.assertEqual(prog.current_progression.level, 3)

    def test_verfehltes_ziel_loescht_den_erstsitzungsmarker(self):
        prog = self.nutzer_auf_level(3, is_first_session=False)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 5, 5
        )

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertFalse(prog.is_first_session)

    def test_workout_wird_als_abgeschlossen_markiert(self):
        self.nutzer_auf_level(3)
        workout = self.workout_mit_saetzen(
            self.uebung, self.progressionen[3], 30, 30
        )

        self.abschliessen(workout)

        workout.refresh_from_db()
        self.assertTrue(workout.completed)
        self.assertIsNotNone(workout.completed_at)


class ZaehlerZuruecksetzenTest(LevelWechselBasis):
    """sessions_at_target zaehlt Sitzungen AM ZIEL - nicht Sitzungen ueberhaupt."""

    def test_treffen_verfehlen_treffen_steigt_nicht_auf(self):
        """Der gemeldete Fall: frueher reichten drei Treffer irgendwann, egal
        was dazwischen lag."""
        prog = self.nutzer_auf_level(3, sessions_at_target=2)

        workout = self.workout_mit_saetzen(self.uebung, self.progressionen[3], 5, 5)
        self.abschliessen(workout)
        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 0)

        workout.delete()
        workout = self.workout_mit_saetzen(self.uebung, self.progressionen[3], 30, 30)
        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3, "geschenkter Aufstieg")
        self.assertEqual(prog.sessions_at_target, 1)

    def test_drei_treffer_am_stueck_steigen_auf(self):
        """Gegenprobe: Bestaendigkeit fuehrt weiterhin zum Aufstieg."""
        prog = self.nutzer_auf_level(3)

        for erwartet in (1, 2, 3):
            workout = self.workout_mit_saetzen(
                self.uebung, self.progressionen[3], 30, 30)
            self.abschliessen(workout)
            prog.refresh_from_db()
            if erwartet < 3:
                self.assertEqual(prog.sessions_at_target, erwartet)
            workout.delete()

        self.assertEqual(prog.current_progression.level, 4)

    def test_nur_der_erste_satz_verfehlt_setzt_auch_zurueck(self):
        prog = self.nutzer_auf_level(3, sessions_at_target=2)
        workout = self.workout_mit_saetzen(self.uebung, self.progressionen[3], 29, 30)

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 0)


class ErstsitzungsmarkerTest(LevelWechselBasis):
    """is_first_session gilt fuer die erste Sitzung auf einer Stufe - danach
    ist bewiesen, dass die Stufe tragbar ist."""

    def test_marker_faellt_auch_bei_erfolg(self):
        prog = self.nutzer_auf_level(3, is_first_session=True)
        workout = self.workout_mit_saetzen(self.uebung, self.progressionen[3], 30, 30)

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertFalse(prog.is_first_session,
                         "Marker bleibt scharf, obwohl die Stufe getragen hat")

    def test_schwacher_tag_nach_erfolgreicher_erstsitzung_stuft_nicht_ab(self):
        """Der gemeldete Fall: der Marker blieb bei Erfolg auf True, die
        Abstiegspruefung damit dauerhaft scharf."""
        prog = self.nutzer_auf_level(3, is_first_session=True)

        gut = self.workout_mit_saetzen(self.uebung, self.progressionen[3], 30, 30)
        self.abschliessen(gut)
        gut.delete()

        schwach = self.workout_mit_saetzen(self.uebung, self.progressionen[3], 1, 1)
        daten = self.abschliessen(schwach)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3, "Abstieg nach schwachem Tag")
        self.assertEqual(daten["downgrades"], [])

    def test_die_echte_erstsitzung_stuft_weiterhin_ab(self):
        """Gegenprobe: der Schutz vor einer zu schweren Stufe bleibt."""
        prog = self.nutzer_auf_level(3, is_first_session=True)
        workout = self.workout_mit_saetzen(self.uebung, self.progressionen[3], 1, 1)

        daten = self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)
        self.assertEqual(len(daten["downgrades"]), 1)

    def test_nach_dem_aufstieg_ist_es_wieder_eine_erstsitzung(self):
        prog = self.nutzer_auf_level(3, sessions_at_target=2, is_first_session=False)
        workout = self.workout_mit_saetzen(self.uebung, self.progressionen[3], 30, 30)

        self.abschliessen(workout)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4)
        self.assertTrue(prog.is_first_session, "die neue Stufe ist ungeprueft")
