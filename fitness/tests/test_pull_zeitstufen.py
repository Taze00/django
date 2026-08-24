"""Tests fuer die Auswertung zeitbasierter Pull-Stufen.

Pull-ups haben zwei Stufen, die in Sekunden gemessen werden: L1 Dead Hang
(das Startlevel) und L3 Active Hang. Wer nur Wiederholungen zaehlt, macht
genau die Stufe unsichtbar, auf der jeder neue Nutzer anfaengt.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import (
    Exercise,
    Progression,
    UserExerciseProgression,
    Workout,
    WorkoutSet,
)


class PullZeitstufenBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="hanger", password="geheim1234"
        )
        self.anonym = APIClient()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.pull = Exercise.objects.create(name="Pull-ups", category="PULL", order=2)
        self.hang = Progression.objects.create(
            exercise=self.pull, level=1, name="Dead Hang",
            target_type="time", target_value=30, user_starts_here=True,
        )
        self.wdh = Progression.objects.create(
            exercise=self.pull, level=6, name="Standard Pull-ups",
            target_type="reps", target_value=5,
        )
        UserExerciseProgression.objects.create(
            user=self.user, exercise=self.pull,
            current_progression=self.hang, training_days=[1, 2, 3, 4, 5, 6, 7],
        )

    def workout_mit(self, *saetze):
        """saetze: (progression, set_number, reps, seconds)"""
        w = Workout.objects.create(user=self.user)
        w.completed = True
        w.save()
        for prog, nr, reps, sek in saetze:
            WorkoutSet.objects.create(
                workout=w, exercise=self.pull, progression=prog,
                set_number=nr, is_drop_set=False, reps=reps, seconds=sek,
            )
        return w


class CommunityStatsPullTest(PullZeitstufenBasis):
    def test_hang_sekunden_erscheinen_als_minuten(self):
        self.workout_mit((self.hang, 1, None, 90), (self.hang, 2, None, 60))

        antwort = self.anonym.get(reverse("community-stats"))

        self.assertEqual(antwort.data["pull_reps"], 0)
        self.assertEqual(antwort.data["pull_hang_minutes"], 2)

    def test_wiederholungen_und_hang_zaehlen_getrennt(self):
        self.workout_mit(
            (self.wdh, 1, 7, None),
            (self.hang, 2, None, 120),
        )

        antwort = self.anonym.get(reverse("community-stats"))

        self.assertEqual(antwort.data["pull_reps"], 7)
        self.assertEqual(antwort.data["pull_hang_minutes"], 2)

    def test_ohne_zeitstufen_bleibt_die_hang_zeit_null(self):
        self.workout_mit((self.wdh, 1, 5, None), (self.wdh, 2, 5, None))

        antwort = self.anonym.get(reverse("community-stats"))

        self.assertEqual(antwort.data["pull_reps"], 10)
        self.assertEqual(antwort.data["pull_hang_minutes"], 0)


class WeeklyReviewPullTest(PullZeitstufenBasis):
    def test_hang_sekunden_der_woche_werden_gezaehlt(self):
        self.workout_mit((self.hang, 1, None, 31), (self.hang, 2, None, 29))

        antwort = self.client.get(reverse("weekly-review"))

        self.assertEqual(antwort.data["pull_reps"], 0)
        self.assertEqual(antwort.data["pull_seconds"], 60)

    def test_beide_typen_nebeneinander(self):
        self.workout_mit(
            (self.wdh, 1, 6, None),
            (self.hang, 2, None, 45),
        )

        antwort = self.client.get(reverse("weekly-review"))

        self.assertEqual(antwort.data["pull_reps"], 6)
        self.assertEqual(antwort.data["pull_seconds"], 45)

    def test_nur_abgeschlossene_workouts_zaehlen(self):
        w = self.workout_mit((self.hang, 1, None, 60))
        w.completed = False
        w.save()

        antwort = self.client.get(reverse("weekly-review"))

        self.assertEqual(antwort.data["pull_seconds"], 0)
