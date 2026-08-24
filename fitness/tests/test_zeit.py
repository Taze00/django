"""Was CORVIS unter "heute" versteht.

Django rechnet projektweit in UTC. Fuer Kalendertage ist das falsch: 00:30
deutscher Zeit ist 22:30 UTC des Vortages. Diese Tests halten fest, dass
fitness/ den deutschen Tag benutzt - und dass das Workout-Datum mitzieht.
"""

import datetime as dt
from unittest import mock
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import Exercise, Progression, UserExerciseProgression, Workout
from fitness.zeit import heute, jetzt, zeitzone


def um(jahr, monat, tag, stunde, minute, tz='UTC'):
    return dt.datetime(jahr, monat, tag, stunde, minute, tzinfo=ZoneInfo(tz))


class ZeitquelleTest(TestCase):
    def test_zeitzone_kommt_aus_den_einstellungen(self):
        self.assertEqual(str(zeitzone()), 'Europe/Berlin')

    @override_settings(CORVIS_TIME_ZONE='UTC')
    def test_einstellung_laesst_sich_umstellen(self):
        self.assertEqual(str(zeitzone()), 'UTC')

    def test_halb_eins_nachts_gilt_als_der_neue_tag(self):
        """Der gemeldete Fall: 00:30 Berlin ist 22:30 UTC des Vortages."""
        with mock.patch('django.utils.timezone.now', return_value=um(2026, 8, 24, 22, 30)):
            self.assertEqual(heute(), dt.date(2026, 8, 25))

    def test_kurz_vor_mitternacht_gilt_noch_der_alte_tag(self):
        with mock.patch('django.utils.timezone.now', return_value=um(2026, 8, 24, 21, 30)):
            self.assertEqual(heute(), dt.date(2026, 8, 24))

    def test_im_winter_gilt_die_stunde_verschiebung(self):
        """Berlin ist im Winter UTC+1, im Sommer UTC+2 - zoneinfo regelt das."""
        with mock.patch('django.utils.timezone.now', return_value=um(2026, 1, 15, 23, 30)):
            self.assertEqual(heute(), dt.date(2026, 1, 16))
        with mock.patch('django.utils.timezone.now', return_value=um(2026, 1, 15, 22, 30)):
            self.assertEqual(heute(), dt.date(2026, 1, 15))

    def test_jetzt_ist_zeitzonenbewusst(self):
        self.assertIsNotNone(jetzt().tzinfo)


class WorkoutDatumTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="nachtschwaermer", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_neues_workout_bekommt_den_deutschen_tag(self):
        with mock.patch('django.utils.timezone.now', return_value=um(2026, 8, 24, 22, 30)):
            w = Workout.objects.create(user=self.user)
        self.assertEqual(w.date, dt.date(2026, 8, 25), "Workout auf dem UTC-Tag angelegt")

    def test_datum_laesst_sich_beim_anlegen_setzen(self):
        """Mit auto_now_add wurde ein gesetzter Wert verworfen - fuer Workouts
        an vergangenen Tagen brauchte es deshalb rohes SQL."""
        w = Workout.objects.create(user=self.user, date=dt.date(2020, 1, 1))
        self.assertEqual(w.date, dt.date(2020, 1, 1))

    def test_current_findet_nachts_das_eigene_workout_wieder(self):
        """Der Kern des Fehlers: get_or_create suchte nach dem einen Tag und
        legte eine Zeile mit dem anderen an - beim zweiten Aufruf lief das in
        unique_together (user, date)."""
        with mock.patch('django.utils.timezone.now', return_value=um(2026, 8, 24, 22, 30)):
            erste = self.client.get(reverse("workout-current"))
            zweite = self.client.get(reverse("workout-current"))

        self.assertEqual(erste.status_code, 201)
        self.assertEqual(zweite.status_code, 200, "beim zweiten Aufruf neu angelegt")
        self.assertEqual(erste.data["id"], zweite.data["id"])
        self.assertEqual(Workout.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Workout.objects.get(user=self.user).date, dt.date(2026, 8, 25))

    def test_sonntagabend_und_montagnacht_sind_zwei_tage(self):
        # Sonntag 23:00 Berlin = 21:00 UTC
        with mock.patch('django.utils.timezone.now', return_value=um(2026, 8, 23, 21, 0)):
            sonntag = self.client.get(reverse("workout-current"))
        # Montag 00:30 Berlin = Sonntag 22:30 UTC
        with mock.patch('django.utils.timezone.now', return_value=um(2026, 8, 23, 22, 30)):
            montag = self.client.get(reverse("workout-current"))

        self.assertNotEqual(sonntag.data["id"], montag.data["id"],
                            "beide schrieben in dieselbe Zeile")
        self.assertEqual(Workout.objects.filter(user=self.user).count(), 2)
        self.assertEqual(
            sorted(Workout.objects.filter(user=self.user).values_list("date", flat=True)),
            [dt.date(2026, 8, 23), dt.date(2026, 8, 24)])


class StreakZeitquelleTest(TestCase):
    def test_streak_verlangt_einen_ausdruecklichen_tag(self):
        """Frueher fiel streak.py auf die OS-Zeit zurueck, waehrend die Daten
        aus Django kamen - zwei Quellen fuer dieselbe Frage."""
        from fitness.streak import calculate_streak, longest_streak

        with self.assertRaises(TypeError):
            calculate_streak([1, 2, 3], set(), set())
        with self.assertRaises(TypeError):
            longest_streak([1, 2, 3], set(), set())

    def test_streak_status_rechnet_mit_dem_deutschen_tag(self):
        user = User.objects.create_user(username="serie", password="geheim1234")
        client = APIClient()
        client.force_authenticate(user=user)
        uebung = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        stufe = Progression.objects.create(
            exercise=uebung, level=1, name="Stufe 1", target_type="reps", target_value=10)
        UserExerciseProgression.objects.create(
            user=user, exercise=uebung, current_progression=stufe,
            training_days=[1, 2, 3, 4, 5, 6, 7])
        # Training am 25. deutscher Zeit eingetragen.
        Workout.objects.create(user=user, date=dt.date(2026, 8, 25), completed=True)

        # 00:30 am 25. deutscher Zeit = 22:30 UTC am 24.
        with mock.patch('django.utils.timezone.now', return_value=um(2026, 8, 24, 22, 30)):
            antwort = client.get(reverse("streak-status"))

        self.assertTrue(antwort.data["trained_today"],
                        "der Streak sah noch den UTC-Tag")
        self.assertEqual(antwort.data["current"], 1)
