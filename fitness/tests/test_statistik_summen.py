"""Gesamtsummen der Statistik.

Frueher summierte die Ansicht die Workout-Liste im Frontend. Die ist
paginiert (PAGE_SIZE 20) - ab dem 21. Training fiel die Gesamtsumme, ohne
dass irgendwo stand warum. Diese Tests halten fest, dass der Endpunkt ueber
ALLE abgeschlossenen Workouts rechnet.
"""

import datetime as dt

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import Exercise, Progression, Workout, WorkoutSet


class SummenBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="rechner", password="geheim1234")
        self.andere = User.objects.create_user(username="fremd", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.push = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        self.pull = Exercise.objects.create(name="Pull-ups", category="PULL", order=2)
        self.core = Exercise.objects.create(name="Planks", category="CORE", order=3)
        self.p_push = Progression.objects.create(
            exercise=self.push, level=1, name="Push", target_type="reps", target_value=10)
        self.p_hang = Progression.objects.create(
            exercise=self.pull, level=1, name="Dead Hang", target_type="time", target_value=30)
        self.p_pull = Progression.objects.create(
            exercise=self.pull, level=6, name="Standard", target_type="reps", target_value=5)
        self.p_core = Progression.objects.create(
            exercise=self.core, level=1, name="Plank", target_type="time", target_value=60)
        self.tag = dt.date(2026, 1, 1)

    def workout(self, user=None, completed=True):
        w = Workout.objects.create(user=user or self.user, date=self.tag, completed=completed)
        self.tag += dt.timedelta(days=1)
        return w

    def satz(self, w, uebung, prog, nummer=1, reps=None, seconds=None):
        return WorkoutSet.objects.create(
            workout=w, exercise=uebung, progression=prog, set_number=nummer,
            is_drop_set=False, reps=reps, seconds=seconds)

    def summen(self):
        antwort = self.client.get(reverse("stats-summary"))
        self.assertEqual(antwort.status_code, 200)
        return antwort.data


class SummenTest(SummenBasis):
    def test_felder_des_endpunkts(self):
        self.assertEqual(
            set(self.summen()),
            {"total_workouts", "push_reps", "pull_reps", "pull_seconds", "plank_seconds"})

    def test_leere_historie_gibt_nullen(self):
        daten = self.summen()
        self.assertEqual(daten["total_workouts"], 0)
        self.assertEqual(daten["push_reps"], 0)

    def test_beide_pull_typen_werden_gezaehlt(self):
        w = self.workout()
        self.satz(w, self.pull, self.p_pull, 1, reps=7)
        self.satz(w, self.pull, self.p_hang, 2, seconds=45)

        daten = self.summen()

        self.assertEqual(daten["pull_reps"], 7)
        self.assertEqual(daten["pull_seconds"], 45)

    def test_ueber_zwanzig_workouts_faellt_die_summe_nicht(self):
        """Der gemeldete Fall: PAGE_SIZE ist 20."""
        for _ in range(25):
            w = self.workout()
            self.satz(w, self.push, self.p_push, 1, reps=10)

        daten = self.summen()

        self.assertEqual(daten["total_workouts"], 25)
        self.assertEqual(daten["push_reps"], 250,
                         "die Summe endet bei der ersten Seite")

    def test_die_workout_liste_zeigt_wirklich_nur_zwanzig(self):
        """Gegenprobe: die Paginierung, an der das Frontend haengenblieb."""
        for _ in range(25):
            self.workout()

        antwort = self.client.get(reverse("workout-list"))

        self.assertEqual(antwort.data["count"], 25)
        self.assertEqual(len(antwort.data["results"]), 20)

    def test_nur_abgeschlossene_workouts_zaehlen(self):
        offen = self.workout(completed=False)
        self.satz(offen, self.push, self.p_push, 1, reps=99)
        fertig = self.workout()
        self.satz(fertig, self.push, self.p_push, 1, reps=10)

        daten = self.summen()

        self.assertEqual(daten["push_reps"], 10)
        self.assertEqual(daten["total_workouts"], 1)

    def test_fremde_workouts_zaehlen_nicht(self):
        fremd = self.workout(user=self.andere)
        self.satz(fremd, self.push, self.p_push, 1, reps=99)

        daten = self.summen()

        self.assertEqual(daten["push_reps"], 0)
        self.assertEqual(daten["total_workouts"], 0)

    def test_endpunkt_verlangt_anmeldung(self):
        antwort = APIClient().get(reverse("stats-summary"))
        self.assertEqual(antwort.status_code, 401)
