"""Meta.ordering - deterministische Reihenfolge.

Ohne ordering ueberlaesst Django die Reihenfolge dem Datenbankplan. Bei
paginierten Endpunkten ist das ein echter Fehler: eine Seite kann denselben
Eintrag zweimal zeigen und einen anderen gar nicht. Django warnt davor mit
UnorderedObjectListWarning.
"""

import warnings

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import (
    Exercise,
    Progression,
    UserExerciseProgression,
    UserProfile,
    WarmupChecklist,
    Workout,
)


class OrderingGesetztTest(TestCase):
    def test_die_drei_modelle_haben_eine_reihenfolge(self):
        for modell in (UserExerciseProgression, UserProfile, WarmupChecklist):
            with self.subTest(modell=modell.__name__):
                self.assertTrue(modell._meta.ordering,
                                f"{modell.__name__} hat kein Meta.ordering")


class ProgressionsReihenfolgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sortierer", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Bewusst in verkehrter Reihenfolge angelegt: die Ausgabe soll sich nach
        # Exercise.order richten, nicht nach der Einfuegereihenfolge.
        self.core = Exercise.objects.create(name="Planks", category="CORE", order=3)
        self.push = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        self.pull = Exercise.objects.create(name="Pull-ups", category="PULL", order=2)
        for uebung in (self.core, self.push, self.pull):
            prog = Progression.objects.create(
                exercise=uebung, level=1, name=f"{uebung.name} 1",
                target_type="reps", target_value=10)
            UserExerciseProgression.objects.create(
                user=self.user, exercise=uebung, current_progression=prog,
                training_days=[1, 2, 3, 4, 5])

    def test_ausgabe_folgt_der_uebungsreihenfolge(self):
        namen = [p.exercise.name for p in UserExerciseProgression.objects.filter(user=self.user)]

        self.assertEqual(namen, ["Push-ups", "Pull-ups", "Planks"])

    def test_endpunkt_warnt_nicht_mehr_vor_unsortierter_liste(self):
        """Der Endpunkt ist paginiert - ohne ordering warnte Django hier."""
        with warnings.catch_warnings(record=True) as gesammelt:
            warnings.simplefilter("always")
            antwort = self.client.get(reverse("user-progression-list"))

        self.assertEqual(antwort.status_code, 200)
        unsortiert = [w for w in gesammelt
                      if "UnorderedObjectList" in w.category.__name__]
        self.assertEqual(unsortiert, [], "Django warnt weiterhin vor unsortierter Liste")

    def test_reihenfolge_ist_ueber_mehrere_abfragen_stabil(self):
        erste = list(UserExerciseProgression.objects.filter(user=self.user).values_list("id", flat=True))
        zweite = list(UserExerciseProgression.objects.filter(user=self.user).values_list("id", flat=True))

        self.assertEqual(erste, zweite)


class WarmupUndProfilReihenfolgeTest(TestCase):
    def test_warmup_und_profil_sind_sortiert(self):
        import datetime as dt
        nutzer = [User.objects.create_user(username=f"n{i}", password="geheim1234")
                  for i in range(3)]
        for u in reversed(nutzer):
            UserProfile.objects.create(user=u, training_days=[1])
            w = Workout.objects.create(user=u, date=dt.date(2026, 1, 1))
            WarmupChecklist.objects.create(workout=w)

        self.assertEqual(
            [p.user_id for p in UserProfile.objects.all()],
            sorted(u.id for u in nutzer))
        self.assertEqual(
            [c.workout_id for c in WarmupChecklist.objects.all()],
            sorted(c.workout_id for c in WarmupChecklist.objects.all()))
