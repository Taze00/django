"""Drop-Saetze speichern jetzt auch einen Zahlenwert.

Bisher stand in reps und seconds beides auf null - der Satz hielt nur fest,
WELCHE Variante erreicht wurde, nie wie viel davon. Er zaehlte damit nirgends
mit, obwohl es geleistete Arbeit war.

Unveraendert bleibt: ein Drop-Satz fuettert die Levellogik nicht.
"""

import datetime as dt

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


class DropWertBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ausbelaster", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.uebung = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        self.stufen = {
            n: Progression.objects.create(
                exercise=self.uebung, level=n, name=f"Stufe {n}",
                target_type="reps", target_value=10,
                sets_required=2, sessions_required=3)
            for n in (1, 2, 3)
        }
        self.workout = Workout.objects.create(user=self.user)

    def eintragen(self, nummer, level, reps=None, seconds=None,
                  is_drop_set=False, drop_set_completed=False):
        return self.client.post(
            reverse("workout-add-set", args=[self.workout.pk]),
            {"exercise": self.uebung.id, "progression": self.stufen[level].id,
             "set_number": nummer, "reps": reps, "seconds": seconds,
             "is_drop_set": is_drop_set, "drop_set_completed": drop_set_completed,
             "rest_time_seconds": 300},
            format="json")

    def abschliessen(self):
        antwort = self.client.post(reverse("workout-complete", args=[self.workout.pk]))
        self.assertEqual(antwort.status_code, 200)
        return antwort.data


class DropWertSpeichernTest(DropWertBasis):
    def test_zahl_landet_am_drop_satz(self):
        self.eintragen(3, level=1, reps=6, is_drop_set=True, drop_set_completed=True)

        satz = WorkoutSet.objects.get(is_drop_set=True)
        self.assertEqual(satz.reps, 6)
        self.assertEqual(satz.progression.level, 1, "erreichte Variante bleibt erhalten")

    def test_zahl_bleibt_freiwillig(self):
        """Wer beim Ausbelasten nicht mitzaehlt, kommt trotzdem weiter."""
        antwort = self.eintragen(3, level=1, reps=None, is_drop_set=True, drop_set_completed=True)

        self.assertEqual(antwort.status_code, 201)
        satz = WorkoutSet.objects.get(is_drop_set=True)
        self.assertIsNone(satz.reps)
        self.assertTrue(satz.drop_set_completed)

    def test_uebersprungener_drop_satz_hat_keine_zahl(self):
        self.eintragen(3, level=3, is_drop_set=True, drop_set_completed=False)

        satz = WorkoutSet.objects.get(is_drop_set=True)
        self.assertFalse(satz.drop_set_completed)
        self.assertIsNone(satz.reps)


class DropWertUndLevellogikTest(DropWertBasis):
    def test_drop_satz_bleibt_aus_der_levellogik_heraus(self):
        """Auch mit Zahl: gewertet werden nur Satz 1 und 2 ohne Drop-Kennzeichen."""
        prog = UserExerciseProgression.objects.create(
            user=self.user, exercise=self.uebung,
            current_progression=self.stufen[2], sessions_at_target=2,
            is_first_session=False, training_days=[1, 2, 3, 4, 5, 6, 7])
        self.eintragen(1, level=2, reps=12)
        self.eintragen(2, level=2, reps=12)
        # Ein schwacher Drop-Satz darf den Aufstieg nicht verhindern.
        self.eintragen(3, level=1, reps=1, is_drop_set=True, drop_set_completed=True)

        daten = self.abschliessen()

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)
        self.assertEqual(len(daten["upgrades"]), 1)


class DropWertInDerStatistikTest(DropWertBasis):
    def test_drop_wiederholungen_zaehlen_in_der_gesamtsumme(self):
        """Folge der Aenderung: geleistete Wiederholungen zaehlen jetzt mit,
        auch die aus dem Drop-Satz."""
        self.eintragen(1, level=2, reps=10)
        self.eintragen(2, level=2, reps=10)
        self.eintragen(3, level=1, reps=6, is_drop_set=True, drop_set_completed=True)
        self.abschliessen()

        antwort = self.client.get(reverse("stats-summary"))

        self.assertEqual(antwort.data["push_reps"], 26)

    def test_ohne_zahl_aendert_sich_nichts(self):
        self.eintragen(1, level=2, reps=10)
        self.eintragen(2, level=2, reps=10)
        self.eintragen(3, level=1, is_drop_set=True, drop_set_completed=True)
        self.abschliessen()

        antwort = self.client.get(reverse("stats-summary"))

        self.assertEqual(antwort.data["push_reps"], 20)
