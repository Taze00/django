"""Korrektur eines bereits eingetragenen Satzes.

Die Korrektur laeuft ueber denselben Endpunkt wie das erste Eintragen:
add_set ist ein update_or_create auf (Workout, Uebung, Satznummer, Drop). Der
alte Wert wird also ersetzt, nicht ergaenzt - und complete() liest Satz 1 und 2
frisch aus der Datenbank. Diese Tests halten fest, dass der alte Wert damit
wirklich nicht mehr in die Levellogik faellt.
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


class KorrekturBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tipper", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.uebung = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        self.stufen = {
            level: Progression.objects.create(
                exercise=self.uebung, level=level, name=f"Stufe {level}",
                target_type="reps", target_value=10,
                sets_required=2, sessions_required=3,
            )
            for level in range(1, 8)
        }
        self.workout = Workout.objects.create(user=self.user)

    def nutzer_auf(self, level, **kwargs):
        felder = {"sessions_at_target": 0, "is_first_session": False, "custom_target": None}
        felder.update(kwargs)
        return UserExerciseProgression.objects.create(
            user=self.user, exercise=self.uebung,
            current_progression=self.stufen[level],
            training_days=[1, 2, 3, 4, 5, 6, 7], **felder,
        )

    def eintragen(self, nummer, reps=None, seconds=None, level=3,
                 is_drop_set=False, drop_set_completed=False):
        return self.client.post(
            reverse("workout-add-set", args=[self.workout.pk]),
            {
                "exercise": self.uebung.id,
                "progression": self.stufen[level].id,
                "set_number": nummer,
                "reps": reps,
                "seconds": seconds,
                "is_drop_set": is_drop_set,
                "drop_set_completed": drop_set_completed,
                "rest_time_seconds": 180,
            },
            format="json",
        )

    def abschliessen(self):
        antwort = self.client.post(reverse("workout-complete", args=[self.workout.pk]))
        self.assertEqual(antwort.status_code, 200)
        return antwort.data


class KorrekturVorDemAbschlussTest(KorrekturBasis):
    def test_korrigierter_wert_ersetzt_den_alten(self):
        self.nutzer_auf(3)
        self.eintragen(1, reps=1)

        antwort = self.eintragen(1, reps=12)

        self.assertEqual(antwort.status_code, 200, "Update, kein neuer Satz")
        saetze = WorkoutSet.objects.filter(
            workout=self.workout, exercise=self.uebung, set_number=1, is_drop_set=False)
        self.assertEqual(saetze.count(), 1, "der alte Satz steht noch daneben")
        self.assertEqual(saetze.first().reps, 12)

    def test_korrektur_entscheidet_ueber_den_aufstieg(self):
        """Tippfehler 1 statt 12: ohne Korrektur kein Aufstieg, mit Korrektur
        schon. Der alte Wert darf nicht zaehlen."""
        prog = self.nutzer_auf(3, sessions_at_target=2)
        self.eintragen(1, reps=1)
        self.eintragen(2, reps=12)

        self.eintragen(1, reps=12)
        daten = self.abschliessen()

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4)
        self.assertEqual(len(daten["upgrades"]), 1)

    def test_ohne_korrektur_bleibt_es_beim_tippfehler(self):
        """Gegenprobe: derselbe Ablauf ohne Korrektur steigt nicht auf."""
        prog = self.nutzer_auf(3, sessions_at_target=2)
        self.eintragen(1, reps=1)
        self.eintragen(2, reps=12)

        daten = self.abschliessen()

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)
        self.assertEqual(daten["upgrades"], [])

    def test_korrektur_nach_unten_verhindert_den_aufstieg(self):
        """Auch andersherum: wer sich zu gut eingetragen hat und das korrigiert,
        steigt nicht auf."""
        prog = self.nutzer_auf(3, sessions_at_target=2)
        self.eintragen(1, reps=12)
        self.eintragen(2, reps=12)

        self.eintragen(1, reps=4)
        daten = self.abschliessen()

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)
        self.assertEqual(daten["upgrades"], [])

    def test_zeitwert_laesst_sich_als_zahl_korrigieren(self):
        # Eigene Zeituebung, damit die Push-Stufen unberuehrt bleiben.
        pull = Exercise.objects.create(name="Pull-ups", category="PULL", order=2)
        hang = Progression.objects.create(
            exercise=pull, level=1, name="Dead Hang",
            target_type="time", target_value=30, sessions_required=3,
        )
        Progression.objects.create(
            exercise=pull, level=2, name="Scapular Shrugs",
            target_type="reps", target_value=10, sessions_required=3,
        )
        UserExerciseProgression.objects.create(
            user=self.user, exercise=pull, current_progression=hang,
            sessions_at_target=2, is_first_session=False,
            training_days=[1, 2, 3, 4, 5, 6, 7],
        )
        for nummer, wert in ((1, 3), (2, 31)):
            self.client.post(
                reverse("workout-add-set", args=[self.workout.pk]),
                {"exercise": pull.id, "progression": hang.id, "set_number": nummer,
                 "reps": None, "seconds": wert, "is_drop_set": False,
                 "drop_set_completed": False, "rest_time_seconds": 180},
                format="json")

        # 3 statt 31 vertippt - als Zahl korrigieren, ohne den Timer neu laufen zu lassen.
        self.client.post(
            reverse("workout-add-set", args=[self.workout.pk]),
            {"exercise": pull.id, "progression": hang.id, "set_number": 1,
             "reps": None, "seconds": 31, "is_drop_set": False,
             "drop_set_completed": False, "rest_time_seconds": 180},
            format="json")

        self.abschliessen()

        prog = UserExerciseProgression.objects.get(user=self.user, exercise=pull)
        self.assertEqual(prog.current_progression.level, 2, "Aufstieg nach der Korrektur")
        self.assertEqual(
            WorkoutSet.objects.filter(workout=self.workout, exercise=pull,
                                      set_number=1, is_drop_set=False).count(), 1)

    def test_drop_set_variante_laesst_sich_neu_waehlen(self):
        self.nutzer_auf(3)
        self.eintragen(3, level=3, is_drop_set=True, drop_set_completed=True)

        antwort = self.eintragen(3, level=1, is_drop_set=True, drop_set_completed=True)

        self.assertEqual(antwort.status_code, 200)
        saetze = WorkoutSet.objects.filter(
            workout=self.workout, exercise=self.uebung, set_number=3, is_drop_set=True)
        self.assertEqual(saetze.count(), 1)
        self.assertEqual(saetze.first().progression.level, 1)


class KorrekturNachDemAbschlussTest(KorrekturBasis):
    def test_nach_dem_abschluss_ist_keine_korrektur_mehr_moeglich(self):
        """Der Schutz aus Runde 1 gilt auch fuer Korrekturen - sonst liefen
        Levellogik und Historie wieder auseinander."""
        self.nutzer_auf(3)
        self.eintragen(1, reps=1)
        self.eintragen(2, reps=12)
        self.abschliessen()

        antwort = self.eintragen(1, reps=12)

        self.assertEqual(antwort.status_code, 409)
        satz = WorkoutSet.objects.get(
            workout=self.workout, exercise=self.uebung, set_number=1, is_drop_set=False)
        self.assertEqual(satz.reps, 1, "der Wert wurde nachtraeglich veraendert")
