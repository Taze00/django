"""last_performance - die Grundlage fuer "Letztes Mal" im Training."""

import datetime as dt

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import Exercise, Progression, Workout, WorkoutSet


class LetztesMalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="erinnerer", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.push = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        self.pull = Exercise.objects.create(name="Pull-ups", category="PULL", order=2)
        self.p_push = Progression.objects.create(
            exercise=self.push, level=3, name="Knee", target_type="reps", target_value=8)
        self.p_hang = Progression.objects.create(
            exercise=self.pull, level=1, name="Dead Hang", target_type="time", target_value=30)

    def vortag(self):
        return Workout.objects.create(
            user=self.user, date=dt.date(2020, 1, 1), completed=True)

    def satz(self, w, uebung, prog, nummer, reps=None, seconds=None,
             is_drop_set=False, drop_set_completed=False):
        return WorkoutSet.objects.create(
            workout=w, exercise=uebung, progression=prog, set_number=nummer,
            reps=reps, seconds=seconds, is_drop_set=is_drop_set,
            drop_set_completed=drop_set_completed)

    def hol(self):
        antwort = self.client.get(reverse("workout-last-performance"))
        self.assertEqual(antwort.status_code, 200)
        return antwort.data

    def test_ablage_erfolgt_nach_uebungs_id(self):
        """Das Frontend suchte frueher nach dem Uebungsnamen."""
        w = self.vortag()
        self.satz(w, self.push, self.p_push, 1, reps=12)

        daten = self.hol()

        self.assertIn(str(self.push.id), daten)
        self.assertNotIn("Push-ups", daten)

    def test_beide_saetze_werden_geliefert(self):
        """Ohne set2 kann "Letztes Mal" bei Satz 2 nichts zeigen."""
        w = self.vortag()
        self.satz(w, self.push, self.p_push, 1, reps=12)
        self.satz(w, self.push, self.p_push, 2, reps=9)

        eintrag = self.hol()[str(self.push.id)]

        self.assertEqual(eintrag["set1_reps"], 12)
        self.assertEqual(eintrag["set2_reps"], 9)

    def test_zeitwerte_stehen_im_sekundenfeld(self):
        w = self.vortag()
        self.satz(w, self.pull, self.p_hang, 1, seconds=31)
        self.satz(w, self.pull, self.p_hang, 2, seconds=28)

        eintrag = self.hol()[str(self.pull.id)]

        self.assertIsNone(eintrag["set1_reps"])
        self.assertEqual(eintrag["set1_seconds"], 31)
        self.assertEqual(eintrag["set2_seconds"], 28)

    def test_uebung_nur_mit_zweitem_satz_erscheint_trotzdem(self):
        w = self.vortag()
        self.satz(w, self.push, self.p_push, 2, reps=9)

        eintrag = self.hol()[str(self.push.id)]

        self.assertIsNone(eintrag["set1_reps"])
        self.assertEqual(eintrag["set2_reps"], 9)

    def test_heutiges_workout_zaehlt_nicht_als_letztes_mal(self):
        heute_w = Workout.objects.create(user=self.user, completed=True)
        self.satz(heute_w, self.push, self.p_push, 1, reps=99)

        self.assertEqual(self.hol(), {})

    def test_ohne_vorgeschichte_kommt_nichts(self):
        self.assertEqual(self.hol(), {})
