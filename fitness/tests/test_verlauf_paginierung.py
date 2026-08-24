"""Verlaufsliste: seitenweise laden statt abgeschnitten anzeigen."""

import datetime as dt

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import Workout


class VerlaufBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="blaetterer", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tag = dt.date(2026, 1, 1)

    def workouts(self, anzahl, completed=True):
        for _ in range(anzahl):
            Workout.objects.create(user=self.user, date=self.tag, completed=completed)
            self.tag += dt.timedelta(days=1)

    def seite(self, **params):
        antwort = self.client.get(reverse("workout-list"), params)
        self.assertEqual(antwort.status_code, 200)
        return antwort.data


class SeitenweiseLadenTest(VerlaufBasis):
    def test_erste_seite_meldet_eine_zweite(self):
        self.workouts(28)

        daten = self.seite()

        self.assertEqual(daten["count"], 28)
        self.assertEqual(len(daten["results"]), 20)
        self.assertIsNotNone(daten["next"])

    def test_zweite_seite_liefert_den_rest(self):
        self.workouts(28)

        daten = self.seite(page=2)

        self.assertEqual(len(daten["results"]), 8)
        self.assertIsNone(daten["next"])

    def test_beide_seiten_zusammen_sind_ueberschneidungsfrei(self):
        self.workouts(28)

        eins = {w["id"] for w in self.seite()["results"]}
        zwei = {w["id"] for w in self.seite(page=2)["results"]}

        self.assertEqual(len(eins | zwei), 28)
        self.assertEqual(eins & zwei, set())

    def test_ohne_zweite_seite_kein_next(self):
        self.workouts(5)

        self.assertIsNone(self.seite()["next"])


class CompletedFilterTest(VerlaufBasis):
    def test_filter_grenzt_auf_abgeschlossene_ein(self):
        self.workouts(3, completed=True)
        self.workouts(2, completed=False)

        self.assertEqual(self.seite(completed="true")["count"], 3)
        self.assertEqual(self.seite(completed="false")["count"], 2)
        self.assertEqual(self.seite()["count"], 5)

    def test_zaehlung_passt_zur_angezeigten_liste(self):
        """Ohne den Filter zaehlte count auch die leeren Zeilen mit, die
        workouts/current/ beim Betreten des Trainingsschirms anlegt - der Knopf
        haette 'Weitere 3 von 25' gesagt und dann nichts Neues gebracht."""
        self.workouts(22, completed=True)
        self.workouts(4, completed=False)

        daten = self.seite(completed="true")

        self.assertEqual(daten["count"], 22)
        self.assertTrue(all(w["completed"] for w in daten["results"]))

    def test_fremde_workouts_bleiben_aussen_vor(self):
        fremd = User.objects.create_user(username="anderer", password="geheim1234")
        Workout.objects.create(user=fremd, date=dt.date(2026, 5, 1), completed=True)
        self.workouts(2)

        self.assertEqual(self.seite(completed="true")["count"], 2)
