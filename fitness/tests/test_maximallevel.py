"""Das Maximallevel kommt aus den Daten, nicht aus einer festen 7.

Die Zahl stand an drei unabhaengigen Stellen: in der Levellogik
(level < 7), im Frontend (MAX_LEVEL = 7) und in den geseedeten
Progressionen. Keine wusste von den anderen.
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


class MaximallevelBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="gipfel", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.uebung = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)

    def stufen_anlegen(self, level_liste):
        self.stufen = {
            n: Progression.objects.create(
                exercise=self.uebung, level=n, name=f"Stufe {n}",
                target_type="reps", target_value=10,
                sets_required=2, sessions_required=3)
            for n in level_liste
        }

    def nutzer_auf(self, level, **kwargs):
        felder = {"sessions_at_target": 2, "is_first_session": False, "custom_target": None}
        felder.update(kwargs)
        return UserExerciseProgression.objects.create(
            user=self.user, exercise=self.uebung,
            current_progression=self.stufen[level],
            training_days=[1, 2, 3, 4, 5, 6, 7], **felder)

    def sitzung(self, level, wert=12):
        w = Workout.objects.create(user=self.user)
        for nr in (1, 2):
            WorkoutSet.objects.create(
                workout=w, exercise=self.uebung, progression=self.stufen[level],
                set_number=nr, is_drop_set=False, reps=wert)
        antwort = self.client.post(reverse("workout-complete", args=[w.pk]))
        self.assertEqual(antwort.status_code, 200)
        return antwort.data


class WenigerAlsSiebenStufenTest(MaximallevelBasis):
    """Eine Uebung mit nur drei Stufen - Stufe 3 ist dort das Maximum."""

    def test_auf_der_hoechsten_stufe_kommt_die_maximalmeldung(self):
        self.stufen_anlegen([1, 2, 3])
        prog = self.nutzer_auf(3)

        daten = self.sitzung(3)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)
        self.assertTrue(daten["upgrades"][0]["is_max_level"])

    def test_zaehler_wird_auf_der_hoechsten_stufe_zurueckgesetzt(self):
        """Frueher hing dieser Zweig an level < 7: bei drei Stufen passierte
        auf Stufe 3 gar nichts, und sessions_at_target wuchs unbegrenzt."""
        self.stufen_anlegen([1, 2, 3])
        prog = self.nutzer_auf(3)

        self.sitzung(3)

        prog.refresh_from_db()
        self.assertEqual(prog.sessions_at_target, 0)

    def test_kein_level_event_auf_der_hoechsten_stufe(self):
        self.stufen_anlegen([1, 2, 3])
        self.nutzer_auf(3)

        self.sitzung(3)

        self.assertEqual(LevelEvent.objects.filter(event_type="level_up").count(), 0)

    def test_darunter_wird_normal_aufgestiegen(self):
        self.stufen_anlegen([1, 2, 3])
        prog = self.nutzer_auf(2)

        self.sitzung(2)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)


class MehrAlsSiebenStufenTest(MaximallevelBasis):
    """Eine achte Stufe muss erreichbar sein, ohne dass Code sich aendert."""

    def test_von_sieben_auf_acht(self):
        self.stufen_anlegen([1, 2, 3, 4, 5, 6, 7, 8])
        prog = self.nutzer_auf(7)

        daten = self.sitzung(7)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 8)
        self.assertEqual(daten["upgrades"][0]["to_level"], 8)

    def test_acht_ist_dann_das_maximum(self):
        self.stufen_anlegen([1, 2, 3, 4, 5, 6, 7, 8])
        self.nutzer_auf(8)

        daten = self.sitzung(8)

        self.assertTrue(daten["upgrades"][0]["is_max_level"])


class LueckeInDerNummerierungTest(MaximallevelBasis):
    def test_ueber_eine_luecke_hinweg_wird_aufgestiegen(self):
        """level__gt statt level+1: bei 1, 2, 4 haengt der Aufstieg sonst auf
        Stufe 2 fest, ohne Meldung."""
        self.stufen_anlegen([1, 2, 4])
        prog = self.nutzer_auf(2)

        daten = self.sitzung(2)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4)
        self.assertEqual(daten["upgrades"][0]["to_level"], 4)
