"""Grenzen fuer eingetragene Werte.

Die Oberflaeche ist die Bequemlichkeit, das Backend die Wahrheit: add_set nahm
jede Zahl an, die jemand schickte. 99999 Wiederholungen landeten in der
Datenbank und verfaelschten Statistik und Levellogik dauerhaft. Und 7.5 wurde
im Frontend still zu 7 - der Nutzer sah nie, dass sein Wert veraendert wurde.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import (
    Exercise,
    Progression,
    Workout,
    WorkoutSet,
    MAX_REPS,
    MAX_SECONDS,
)


class GrenzenBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="uebertreiber", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.uebung = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        self.stufe = Progression.objects.create(
            exercise=self.uebung, level=1, name="Stufe 1",
            target_type="reps", target_value=10)
        self.workout = Workout.objects.create(user=self.user)

    def eintragen(self, reps=None, seconds=None, nummer=1):
        return self.client.post(
            reverse("workout-add-set", args=[self.workout.pk]),
            {"exercise": self.uebung.id, "progression": self.stufe.id,
             "set_number": nummer, "reps": reps, "seconds": seconds,
             "is_drop_set": False, "drop_set_completed": False,
             "rest_time_seconds": 180},
            format="json")


class ObergrenzeTest(GrenzenBasis):
    def test_neunundneunzigtausend_wird_abgewiesen(self):
        antwort = self.eintragen(reps=99999)

        self.assertEqual(antwort.status_code, 400)
        self.assertIn(str(MAX_REPS), antwort.data["error"])
        self.assertEqual(WorkoutSet.objects.count(), 0)

    def test_genau_die_grenze_geht_noch(self):
        antwort = self.eintragen(reps=MAX_REPS)

        self.assertEqual(antwort.status_code, 201)
        self.assertEqual(WorkoutSet.objects.get().reps, MAX_REPS)

    def test_einer_ueber_der_grenze_nicht_mehr(self):
        self.assertEqual(self.eintragen(reps=MAX_REPS + 1).status_code, 400)

    def test_sekunden_haben_eine_eigene_grenze(self):
        self.assertEqual(self.eintragen(seconds=MAX_SECONDS).status_code, 201)
        self.assertEqual(self.eintragen(seconds=MAX_SECONDS + 1, nummer=2).status_code, 400)

    def test_negative_werte_werden_abgewiesen(self):
        antwort = self.eintragen(reps=-5)

        self.assertEqual(antwort.status_code, 400)
        self.assertIn("negativ", antwort.data["error"])


class NachkommastellenTest(GrenzenBasis):
    def test_sieben_komma_fuenf_wird_abgewiesen_statt_abgeschnitten(self):
        """Der gemeldete Fall: parseInt('7.5') ergibt still 7."""
        antwort = self.eintragen(reps=7.5)

        self.assertEqual(antwort.status_code, 400)
        self.assertIn("ganze Zahl", antwort.data["error"])
        self.assertEqual(WorkoutSet.objects.count(), 0)

    def test_ganze_zahl_als_kommazahl_geht_durch(self):
        """7.0 ist eine ganze Zahl - nur die Schreibweise ist anders."""
        antwort = self.eintragen(reps=7.0)

        self.assertEqual(antwort.status_code, 201)
        self.assertEqual(WorkoutSet.objects.get().reps, 7)

    def test_text_wird_abgewiesen(self):
        antwort = self.eintragen(reps="viele")

        self.assertEqual(antwort.status_code, 400)
        self.assertEqual(WorkoutSet.objects.count(), 0)

    def test_zahl_als_text_geht_durch(self):
        antwort = self.eintragen(reps="12")

        self.assertEqual(antwort.status_code, 201)
        self.assertEqual(WorkoutSet.objects.get().reps, 12)


class LeereWerteTest(GrenzenBasis):
    def test_null_bleibt_erlaubt(self):
        """Nicht jeder Satz hat beide Felder - eine Zeitstufe hat kein reps."""
        antwort = self.eintragen(reps=None, seconds=45)

        self.assertEqual(antwort.status_code, 201)
        satz = WorkoutSet.objects.get()
        self.assertIsNone(satz.reps)
        self.assertEqual(satz.seconds, 45)

    def test_null_wiederholungen_sind_ein_gueltiger_wert(self):
        """Wer keine einzige geschafft hat, traegt 0 ein - das ist kein Fehler."""
        antwort = self.eintragen(reps=0)

        self.assertEqual(antwort.status_code, 201)
        self.assertEqual(WorkoutSet.objects.get().reps, 0)
