"""Der komplette Pull-up-Aufstieg und die Typwechsel darin.

Pull-ups wechseln zwischen den Stufen den Messtyp:

    L1 Dead Hang        Zeit
    L2 Scapular Shrugs  Wdh.      <- Wechsel
    L3 Active Hang      Zeit      <- Wechsel
    L4 Pull-up Negatives Wdh.     <- Wechsel
    L5 Band-Assisted    Wdh.
    L6 Standard         Wdh.
    L7 Chest-to-Bar     Wdh.

Die Levellogik las die Saetze frueher mit dem target_type der AKTUELLEN
Progression statt mit dem, unter dem sie aufgezeichnet wurden. Stimmten die
beiden nicht ueberein, schaute sie im leeren Feld nach, las None als 0 - und
stufte fuer eine bestandene Sitzung ab.
"""

import datetime as dt

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

# Die echten Pull-up-Stufen aus Migration 0009.
STUFEN = [
    (1, "Dead Hang", "time", 30),
    (2, "Scapular Shrugs", "reps", 10),
    (3, "Active Hang", "time", 20),
    (4, "Pull-up Negatives", "reps", 5),
    (5, "Band-Assisted Pull-ups", "reps", 8),
    (6, "Standard Pull-ups", "reps", 5),
    (7, "Chest-to-Bar", "reps", 5),
]


class PullBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="klimmzug", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.pull = Exercise.objects.create(name="Pull-ups", category="PULL", order=2)
        self.stufen = {
            level: Progression.objects.create(
                exercise=self.pull, level=level, name=name,
                target_type=typ, target_value=ziel,
                sets_required=2, sessions_required=3,
                user_starts_here=(level == 1),
            )
            for level, name, typ, ziel in STUFEN
        }
        self.tag = dt.date(2026, 1, 5)

    def nutzer_auf(self, level, **kwargs):
        felder = {"sessions_at_target": 0, "is_first_session": True, "custom_target": None}
        felder.update(kwargs)
        return UserExerciseProgression.objects.create(
            user=self.user, exercise=self.pull,
            current_progression=self.stufen[level],
            training_days=[1, 2, 3, 4, 5, 6, 7], **felder,
        )

    def workout_an_eigenem_tag(self):
        """Workout.date ist auto_now_add - fuer mehrere Sitzungen umgehen wir
        das ueber ein queryset-update (unique_together user+date)."""
        w = Workout.objects.create(user=self.user)
        Workout.objects.filter(pk=w.pk).update(date=self.tag)
        self.tag += dt.timedelta(days=1)
        w.refresh_from_db()
        return w

    def satz(self, workout, prog, nummer, wert):
        feld = "reps" if prog.target_type == "reps" else "seconds"
        return WorkoutSet.objects.create(
            workout=workout, exercise=self.pull, progression=prog,
            set_number=nummer, is_drop_set=False, **{feld: wert},
        )

    def sitzung(self, prog, wert1, wert2):
        w = self.workout_an_eigenem_tag()
        self.satz(w, prog, 1, wert1)
        self.satz(w, prog, 2, wert2)
        return self.abschliessen(w)

    def abschliessen(self, workout):
        antwort = self.client.post(reverse("workout-complete", args=[workout.pk]))
        self.assertEqual(antwort.status_code, 200)
        return antwort.data


class KompletterAufstiegTest(PullBasis):
    """L1 bis L7 am Stueck, ueber alle drei Typwechsel hinweg."""

    def test_aufstieg_ueber_alle_sieben_stufen(self):
        prog = self.nutzer_auf(1)

        for level in range(1, 7):
            stufe = self.stufen[level]
            for nummer in range(1, stufe.sessions_required + 1):
                daten = self.sitzung(stufe, stufe.target_value, stufe.target_value)
                self.assertEqual(
                    daten["downgrades"], [],
                    f"Abstieg auf Level {level}, Sitzung {nummer} - "
                    f"Zieltyp {stufe.target_type}",
                )
                prog.refresh_from_db()

            self.assertEqual(
                prog.current_progression.level, level + 1,
                f"Nach drei Sitzungen auf Level {level} ({stufe.target_type}) "
                f"haette Level {level + 1} stehen muessen",
            )

        self.assertEqual(prog.current_progression.name, "Chest-to-Bar")
        self.assertEqual(
            LevelEvent.objects.filter(user=self.user, event_type="level_up").count(), 6
        )

    def test_jeder_typwechsel_einzeln(self):
        """Die drei Kanten, an denen sich der Messtyp aendert."""
        for von in (1, 2, 3):
            with self.subTest(wechsel=f"L{von}->L{von + 1}"):
                UserExerciseProgression.objects.filter(user=self.user).delete()
                Workout.objects.filter(user=self.user).delete()
                stufe = self.stufen[von]
                prog = self.nutzer_auf(von, sessions_at_target=2)

                daten = self.sitzung(stufe, stufe.target_value, stufe.target_value)

                prog.refresh_from_db()
                self.assertEqual(prog.current_progression.level, von + 1)
                self.assertEqual(daten["downgrades"], [])
                self.assertNotEqual(
                    self.stufen[von].target_type, self.stufen[von + 1].target_type,
                    "Diese Kante sollte ein Typwechsel sein",
                )

    def test_auf_level_sieben_ist_schluss(self):
        prog = self.nutzer_auf(7, sessions_at_target=2)

        daten = self.sitzung(self.stufen[7], 5, 5)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 7)
        self.assertTrue(daten["upgrades"][0]["is_max_level"])


class TypwechselOhneAbstiegTest(PullBasis):
    """Saetze und aktuelle Stufe passen nicht zusammen."""

    def test_zeitsaetze_unter_einer_wiederholungsstufe_stufen_nicht_ab(self):
        """Der gemeldete Fehler: Saetze auf L1 (Zeit) aufgezeichnet, der Nutzer
        steht inzwischen auf L2 (Wdh.). Frueher las die Logik set1.reps = None
        als 0 und stufte ab."""
        prog = self.nutzer_auf(2, sessions_at_target=1)
        w = self.workout_an_eigenem_tag()
        self.satz(w, self.stufen[1], 1, 31)
        self.satz(w, self.stufen[1], 2, 31)

        daten = self.abschliessen(w)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2, "kein Abstieg")
        self.assertEqual(daten["downgrades"], [])
        self.assertEqual(daten["upgrades"], [], "aber auch kein geschenkter Aufstieg")
        self.assertEqual(prog.sessions_at_target, 1, "Zaehler unberuehrt")
        self.assertIsNone(prog.custom_target)

    def test_wiederholungssaetze_unter_einer_zeitstufe_stufen_nicht_ab(self):
        """Die Gegenrichtung: Wdh. aufgezeichnet, aktuell eine Zeitstufe."""
        prog = self.nutzer_auf(3, sessions_at_target=1)
        w = self.workout_an_eigenem_tag()
        self.satz(w, self.stufen[2], 1, 12)
        self.satz(w, self.stufen[2], 2, 12)

        daten = self.abschliessen(w)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 3)
        self.assertEqual(daten["downgrades"], [])
        self.assertEqual(prog.sessions_at_target, 1)

    def test_progression_mitten_im_workout_gewechselt(self):
        """Satz 1 auf L1, Satz 2 auf L2 - die beiden sind nicht vergleichbar."""
        prog = self.nutzer_auf(2, sessions_at_target=2)
        w = self.workout_an_eigenem_tag()
        self.satz(w, self.stufen[1], 1, 45)
        self.satz(w, self.stufen[2], 2, 12)

        daten = self.abschliessen(w)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)
        self.assertEqual(daten["upgrades"], [])
        self.assertEqual(daten["downgrades"], [])
        self.assertEqual(prog.sessions_at_target, 2)

    def test_passende_stufe_wird_normal_gewertet(self):
        """Gegenprobe: stimmen Satz und Stufe ueberein, laeuft alles wie immer."""
        prog = self.nutzer_auf(1, sessions_at_target=2)

        daten = self.sitzung(self.stufen[1], 30, 30)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)
        self.assertEqual(len(daten["upgrades"]), 1)


class SatzwertLesenTest(PullBasis):
    """Wie ein einzelner Satz gelesen wird."""

    def test_zeitstufe_liest_sekunden(self):
        prog = self.nutzer_auf(1, sessions_at_target=2)

        self.sitzung(self.stufen[1], 30, 30)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)

    def test_leeres_feld_zaehlt_als_null_und_stuft_ab(self):
        """Zeitstufe, aber seconds ist None: 0 Sekunden sind ein echter
        Abstiegsgrund - das darf die Korrektur nicht wegnehmen."""
        prog = self.nutzer_auf(3, is_first_session=True)
        w = self.workout_an_eigenem_tag()
        for nummer in (1, 2):
            WorkoutSet.objects.create(
                workout=w, exercise=self.pull, progression=self.stufen[3],
                set_number=nummer, is_drop_set=False, reps=None, seconds=None,
            )

        self.abschliessen(w)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 2)

    def test_gefuelltes_feld_gewinnt_gegen_das_leere(self):
        """Zeitstufe, aber der Wert steht aus Altbestand in reps: die
        aufgezeichnete Zahl gilt, nicht das leere Schemafeld."""
        prog = self.nutzer_auf(3, sessions_at_target=2)
        w = self.workout_an_eigenem_tag()
        for nummer in (1, 2):
            WorkoutSet.objects.create(
                workout=w, exercise=self.pull, progression=self.stufen[3],
                set_number=nummer, is_drop_set=False, reps=25, seconds=None,
            )

        self.abschliessen(w)

        prog.refresh_from_db()
        self.assertEqual(prog.current_progression.level, 4, "25 >= Ziel 20")
