"""Workout.duration_seconds - wie lange das Training gedauert hat.

Das Feld gab es seit jeher im Modell und im Serializer, befuellt wurde es nie.
"""

import datetime as dt
from unittest import mock
from zoneinfo import ZoneInfo

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


def um(*args):
    return dt.datetime(*args, tzinfo=ZoneInfo('UTC'))


class DauerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="zeitnehmer", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.uebung = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        self.stufe = Progression.objects.create(
            exercise=self.uebung, level=1, name="Stufe 1",
            target_type="reps", target_value=10)
        UserExerciseProgression.objects.create(
            user=self.user, exercise=self.uebung, current_progression=self.stufe,
            training_days=[1, 2, 3, 4, 5, 6, 7])
        self.workout = Workout.objects.create(user=self.user)

    def satz(self, nummer, reps, wann):
        s = WorkoutSet.objects.create(
            workout=self.workout, exercise=self.uebung, progression=self.stufe,
            set_number=nummer, is_drop_set=False, reps=reps)
        # created_at ist auto_now_add - per queryset-update umgehen.
        WorkoutSet.objects.filter(pk=s.pk).update(created_at=wann)
        return s

    def abschliessen(self, wann):
        with mock.patch('django.utils.timezone.now', return_value=wann):
            antwort = self.client.post(reverse("workout-complete", args=[self.workout.pk]))
        self.assertEqual(antwort.status_code, 200)
        self.workout.refresh_from_db()

    def test_dauer_laeuft_vom_ersten_satz_bis_zum_abschluss(self):
        self.satz(1, 12, um(2026, 5, 1, 18, 0, 0))
        self.satz(2, 10, um(2026, 5, 1, 18, 5, 0))

        self.abschliessen(um(2026, 5, 1, 18, 32, 0))

        self.assertEqual(self.workout.duration_seconds, 32 * 60)

    def test_der_frueheste_satz_zaehlt_nicht_der_zuerst_angelegte(self):
        self.satz(2, 10, um(2026, 5, 1, 18, 10, 0))
        self.satz(1, 12, um(2026, 5, 1, 18, 0, 0))

        self.abschliessen(um(2026, 5, 1, 18, 20, 0))

        self.assertEqual(self.workout.duration_seconds, 20 * 60)

    def test_ohne_saetze_bleibt_die_dauer_leer(self):
        self.abschliessen(um(2026, 5, 1, 18, 0, 0))

        self.assertIsNone(self.workout.duration_seconds)

    def test_dauer_wird_nicht_negativ(self):
        """Sicherheitsnetz: eine Uhr, die zurueckspringt, darf keine negative
        Dauer erzeugen."""
        self.satz(1, 12, um(2026, 5, 1, 18, 30, 0))

        self.abschliessen(um(2026, 5, 1, 18, 0, 0))

        self.assertEqual(self.workout.duration_seconds, 0)

    def test_dauer_steht_im_serializer(self):
        self.satz(1, 12, um(2026, 5, 1, 18, 0, 0))
        self.satz(2, 10, um(2026, 5, 1, 18, 1, 0))
        self.abschliessen(um(2026, 5, 1, 18, 15, 0))

        antwort = self.client.get(reverse("workout-detail", args=[self.workout.pk]))

        self.assertEqual(antwort.data["duration_seconds"], 15 * 60)

    def test_wiederholtes_abschliessen_aendert_die_dauer_nicht(self):
        """complete ist idempotent - auch fuer die Dauer."""
        self.satz(1, 12, um(2026, 5, 1, 18, 0, 0))
        self.abschliessen(um(2026, 5, 1, 18, 20, 0))
        zuerst = self.workout.duration_seconds

        self.abschliessen(um(2026, 5, 1, 19, 0, 0))

        self.assertEqual(self.workout.duration_seconds, zuerst)
