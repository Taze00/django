"""Was nach dem Abschluss eines Workouts noch passieren darf.

Ein abgeschlossenes Workout ist Historie. Es darf die Levellogik nicht ein
zweites Mal ausloesen und keine neuen Saetze mehr aufnehmen - sonst
widersprechen sich Zaehler und Verlauf dauerhaft.
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


class AbschlussBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="doppelt", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.uebung = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        self.stufen = {
            level: Progression.objects.create(
                exercise=self.uebung, level=level, name=f"Stufe {level}",
                target_type="reps", target_value=10,
                sets_required=2, sessions_required=3,
            )
            for level in range(1, 8)
        }

    def nutzer_auf(self, level, **kwargs):
        felder = {"sessions_at_target": 0, "is_first_session": False, "custom_target": None}
        felder.update(kwargs)
        return UserExerciseProgression.objects.create(
            user=self.user, exercise=self.uebung,
            current_progression=self.stufen[level],
            training_days=[1, 2, 3, 4, 5, 6, 7], **felder,
        )

    def workout_mit_zwei_saetzen(self, level, wert=10):
        w = Workout.objects.create(user=self.user)
        for nr in (1, 2):
            WorkoutSet.objects.create(
                workout=w, exercise=self.uebung, progression=self.stufen[level],
                set_number=nr, is_drop_set=False, reps=wert,
            )
        return w

    def abschliessen(self, workout):
        antwort = self.client.post(reverse("workout-complete", args=[workout.pk]))
        self.assertEqual(antwort.status_code, 200)
        return antwort.data


class CompleteIstIdempotentTest(AbschlussBasis):
    def test_zweiter_aufruf_zaehlt_die_sitzung_nicht_noch_einmal(self):
        prog = self.nutzer_auf(3)
        w = self.workout_mit_zwei_saetzen(3)

        self.abschliessen(w)
        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 1)

        self.abschliessen(w)

        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 1, "zweiter Aufruf hat mitgezaehlt")

    def test_dreimal_abschliessen_schenkt_keinen_aufstieg(self):
        """Der gemeldete Fall: dreimal aufgerufen = geschenkter Aufstieg."""
        prog = self.nutzer_auf(3)
        w = self.workout_mit_zwei_saetzen(3)

        for _ in range(3):
            self.abschliessen(w)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3, "kein geschenkter Aufstieg")
        self.assertEqual(prog.sessions_at_target, 1)
        self.assertEqual(
            LevelEvent.objects.filter(user=self.user, event_type="level_up").count(), 0
        )

    def test_zweiter_aufruf_meldet_sich_als_bereits_abgeschlossen(self):
        self.nutzer_auf(3)
        w = self.workout_mit_zwei_saetzen(3)

        self.abschliessen(w)
        daten = self.abschliessen(w)

        self.assertEqual(daten["status"], "already_completed")
        self.assertEqual(daten["upgrades"], [])
        self.assertEqual(daten["downgrades"], [])

    def test_abschlusszeit_bleibt_die_des_ersten_aufrufs(self):
        self.nutzer_auf(3)
        w = self.workout_mit_zwei_saetzen(3)

        self.abschliessen(w)
        w.refresh_from_db()
        zuerst = w.completed_at

        self.abschliessen(w)

        w.refresh_from_db()
        self.assertEqual(w.completed_at, zuerst)

    def test_der_erste_aufruf_wertet_ganz_normal(self):
        """Gegenprobe: die Idempotenz darf den regulaeren Abschluss nicht
        entschaerfen."""
        prog = self.nutzer_auf(3, sessions_at_target=2)
        w = self.workout_mit_zwei_saetzen(3)

        daten = self.abschliessen(w)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4)
        self.assertEqual(daten["status"], "completed")
        self.assertEqual(len(daten["upgrades"]), 1)

    def test_wiederholtes_abschliessen_stuft_auch_nicht_ab(self):
        """Nach einem Aufstieg passt die Progression am Satz nicht mehr zur
        aktuellen - frueher wurde das beim zweiten Aufruf als 0 gelesen."""
        prog = self.nutzer_auf(3, sessions_at_target=2, is_first_session=True)
        w = self.workout_mit_zwei_saetzen(3)

        self.abschliessen(w)
        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4)

        daten = self.abschliessen(w)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4, "Abstieg beim zweiten Aufruf")
        self.assertEqual(daten["downgrades"], [])
        self.assertIsNone(prog.custom_target)
