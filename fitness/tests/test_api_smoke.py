"""Smoke-Tests fuer jeden API-Endpunkt.

Zweck: "der Endpunkt lebt und verlangt Auth" - Statuscode und die
Grundstruktur der Antwort. Bewusst KEINE Detailtests der Fachlogik;
die steht in test_calibration.py, test_streak.py und
test_level_changes.py.

Jeder geschuetzte Endpunkt wird zweimal angefasst:
  - ohne Anmeldung  -> 401 (JWTAuthentication setzt einen
                       WWW-Authenticate-Header, daher 401 und nicht 403)
  - mit Anmeldung   -> erwarteter Statuscode + erwartete Schluessel
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import (
    Exercise,
    LevelEvent,
    Progression,
    RestDay,
    UserExerciseProgression,
    UserProfile,
    Workout,
)


class ApiBasis(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="smoke", password="geheim1234", email="smoke@example.org"
        )
        self.anonym = APIClient()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.uebung = Exercise.objects.create(
            name="Push-ups", category="PUSH", order=1
        )
        self.prog1 = Progression.objects.create(
            exercise=self.uebung, level=1, name="Stufe 1",
            target_type="reps", target_value=10, sessions_required=3,
            user_starts_here=True,
        )
        self.prog2 = Progression.objects.create(
            exercise=self.uebung, level=2, name="Stufe 2",
            target_type="reps", target_value=20, sessions_required=3,
        )

    def nutzer_progression(self):
        return UserExerciseProgression.objects.create(
            user=self.user,
            exercise=self.uebung,
            current_progression=self.prog1,
            training_days=[1, 2, 3, 4, 5],
        )

    def workout_von_heute(self):
        return Workout.objects.create(user=self.user)


class OeffentlicheEndpunkteTest(ApiBasis):
    """permission_classes = [] - erreichbar ohne Anmeldung."""

    def test_exercises_liste_ist_oeffentlich(self):
        antwort = self.anonym.get(reverse("exercise-list"))
        self.assertEqual(antwort.status_code, 200)
        # Alle Listen sind paginiert: {count, next, previous, results}.
        self.assertEqual(
            set(antwort.data), {"count", "next", "previous", "results"}
        )
        # Keine absolute Zahl pruefen: seit
        # 0009_seed_exercises_and_progressions bringt die Migrationskette
        # die drei echten Uebungen schon mit. Geprueft wird ueber die ID,
        # nicht ueber den Namen - die geseedete Uebung heisst genauso.
        ids = [e["id"] for e in antwort.data["results"]]
        self.assertIn(self.uebung.pk, ids)
        self.assertIn("progressions", antwort.data["results"][0])

    def test_exercises_detail_ist_oeffentlich(self):
        antwort = self.anonym.get(
            reverse("exercise-detail", args=[self.uebung.pk])
        )
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["name"], "Push-ups")

    def test_community_stats_ist_oeffentlich(self):
        antwort = self.anonym.get(reverse("community-stats"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(
            set(antwort.data),
            {
                "total_athletes",
                "total_workouts",
                "push_reps",
                "pull_reps",
                "plank_minutes",
                "level_ups",
            },
        )

    def test_token_endpunkt_gibt_bei_richtigen_daten_zwei_token(self):
        antwort = self.anonym.post(
            reverse("token_obtain_pair"),
            {"username": "smoke", "password": "geheim1234"},
            format="json",
        )
        self.assertEqual(antwort.status_code, 200)
        self.assertIn("access", antwort.data)
        self.assertIn("refresh", antwort.data)

    def test_token_endpunkt_weist_falsches_passwort_ab(self):
        antwort = self.anonym.post(
            reverse("token_obtain_pair"),
            {"username": "smoke", "password": "falsch"},
            format="json",
        )
        self.assertEqual(antwort.status_code, 401)

    def test_register_verlangt_den_richtigen_schluessel(self):
        antwort = self.anonym.post(
            reverse("register"),
            {"username": "neu", "password": "x", "registration_key": "falsch"},
            format="json",
        )
        self.assertEqual(antwort.status_code, 403)


class AuthPflichtTest(ApiBasis):
    """Jeder geschuetzte Endpunkt muss ohne Anmeldung 401 liefern."""

    def test_alle_geschuetzten_endpunkte_verlangen_auth(self):
        workout = self.workout_von_heute()
        progression = self.nutzer_progression()

        faelle = [
            ("get", reverse("user-progression-list"), {}),
            ("post", reverse("user-progression-list"), {}),
            ("get", reverse("user-progression-detail",
                            args=[progression.pk]), {}),
            ("get", reverse("workout-list"), {}),
            ("post", reverse("workout-list"), {}),
            ("get", reverse("workout-detail", args=[workout.pk]), {}),
            ("get", reverse("workout-current"), {}),
            ("get", reverse("workout-last-performance"), {}),
            ("post", reverse("workout-add-set", args=[workout.pk]), {}),
            ("post", reverse("workout-complete", args=[workout.pk]), {}),
            ("post", reverse("workout-reset", args=[workout.pk]), {}),
            ("put", reverse("workout-warmup", args=[workout.pk]), {}),
            ("get", reverse("user-detail"), {}),
            ("put", reverse("upload-profile-picture"), {}),
            ("delete", reverse("delete-profile-picture"), {}),
            ("get", reverse("user-settings"), {}),
            ("put", reverse("user-settings"), {}),
            ("post", reverse("complete-onboarding"), {}),
            ("post", reverse("calibrate-onboarding"), {}),
            ("post", reverse("reset-onboarding"), {}),
            ("get", reverse("streak-status"), {}),
            ("get", reverse("timeline"), {}),
            ("get", reverse("weekly-review"), {}),
            ("post", reverse("mark-rest-day"), {}),
            ("delete", reverse("unmark-rest-day"), {}),
        ]

        for methode, pfad, daten in faelle:
            with self.subTest(methode=methode, pfad=pfad):
                antwort = getattr(self.anonym, methode)(
                    pfad, daten, format="json"
                )
                self.assertEqual(
                    antwort.status_code, 401,
                    f"{methode.upper()} {pfad} sollte 401 liefern",
                )


class WorkoutEndpunkteTest(ApiBasis):
    """Die Workout-Routen, angemeldet."""

    def test_workout_liste(self):
        self.workout_von_heute()
        antwort = self.client.get(reverse("workout-list"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["count"], 1)

    def test_workout_liste_zeigt_nur_eigene(self):
        fremd = User.objects.create_user(username="fremd", password="x")
        Workout.objects.create(user=fremd)
        antwort = self.client.get(reverse("workout-list"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["count"], 0)

    def test_workout_current_legt_heute_an(self):
        antwort = self.client.get(reverse("workout-current"))
        self.assertEqual(antwort.status_code, 201)
        self.assertIn("id", antwort.data)
        self.assertIn("sets", antwort.data)

    def test_workout_current_gibt_beim_zweiten_mal_200(self):
        self.client.get(reverse("workout-current"))
        antwort = self.client.get(reverse("workout-current"))
        self.assertEqual(antwort.status_code, 200)

    def test_workout_detail(self):
        workout = self.workout_von_heute()
        antwort = self.client.get(reverse("workout-detail", args=[workout.pk]))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["id"], workout.pk)

    def test_add_set_legt_einen_satz_an(self):
        workout = self.workout_von_heute()
        antwort = self.client.post(
            reverse("workout-add-set", args=[workout.pk]),
            {
                "exercise": self.uebung.pk,
                "progression": self.prog1.pk,
                "set_number": 1,
                "reps": 12,
            },
            format="json",
        )
        self.assertEqual(antwort.status_code, 201)
        self.assertEqual(antwort.data["reps"], 12)

    def test_add_set_weist_unbekannte_uebung_ab(self):
        workout = self.workout_von_heute()
        antwort = self.client.post(
            reverse("workout-add-set", args=[workout.pk]),
            {"exercise": 9999, "progression": 9999, "set_number": 1},
            format="json",
        )
        self.assertEqual(antwort.status_code, 400)

    def test_complete_liefert_auf_und_abstiege(self):
        workout = self.workout_von_heute()
        antwort = self.client.post(
            reverse("workout-complete", args=[workout.pk])
        )
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["status"], "completed")
        self.assertIn("upgrades", antwort.data)
        self.assertIn("downgrades", antwort.data)

    def test_reset_loescht_das_workout(self):
        workout = self.workout_von_heute()
        antwort = self.client.post(reverse("workout-reset", args=[workout.pk]))
        self.assertEqual(antwort.status_code, 200)
        self.assertFalse(Workout.objects.filter(pk=workout.pk).exists())

    def test_last_performance(self):
        antwort = self.client.get(reverse("workout-last-performance"))
        self.assertEqual(antwort.status_code, 200)

    def test_warmup_speichert_die_checkliste(self):
        workout = self.workout_von_heute()
        antwort = self.client.put(
            reverse("workout-warmup", args=[workout.pk]),
            {
                "wrists": True, "shoulders": True, "elbows": False,
                "back": False, "legs": False,
            },
            format="json",
        )
        self.assertEqual(antwort.status_code, 200)
        self.assertTrue(antwort.data["wrists"])


class ProfilUndEinstellungenTest(ApiBasis):
    def test_user_detail_liefert_die_grunddaten(self):
        antwort = self.client.get(reverse("user-detail"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["username"], "smoke")
        self.assertEqual(
            set(antwort.data),
            {
                "id", "username", "email", "first_name", "last_name",
                "profile_picture", "onboarding_completed",
            },
        )

    def test_settings_legt_das_profil_bei_bedarf_an(self):
        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())
        antwort = self.client.get(reverse("user-settings"))
        self.assertEqual(antwort.status_code, 200)
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_settings_speichert_trainingstage(self):
        antwort = self.client.put(
            reverse("user-settings"),
            {"training_days": [1, 3, 5]},
            format="json",
        )
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["training_days"], [1, 3, 5])

    def test_bildupload_ohne_datei_gibt_400(self):
        antwort = self.client.put(reverse("upload-profile-picture"))
        self.assertEqual(antwort.status_code, 400)
        self.assertIn("error", antwort.data)

    def test_bild_loeschen_ohne_profil_gibt_404(self):
        antwort = self.client.delete(reverse("delete-profile-picture"))
        self.assertEqual(antwort.status_code, 404)

    def test_bild_loeschen_mit_profil_gibt_200(self):
        UserProfile.objects.create(user=self.user)
        antwort = self.client.delete(reverse("delete-profile-picture"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["status"], "deleted")


class OnboardingEndpunkteTest(ApiBasis):
    def test_complete_onboarding_legt_progressionen_an(self):
        antwort = self.client.post(reverse("complete-onboarding"))
        self.assertEqual(antwort.status_code, 200)
        self.assertTrue(
            UserExerciseProgression.objects.filter(user=self.user).exists()
        )

    def test_calibrate_ohne_ergebnisse_gibt_400(self):
        antwort = self.client.post(
            reverse("calibrate-onboarding"), {"results": []}, format="json"
        )
        self.assertEqual(antwort.status_code, 400)

    def test_calibrate_speichert_das_ergebnis(self):
        antwort = self.client.post(
            reverse("calibrate-onboarding"),
            {
                "training_days": [1, 3, 5],
                "results": [
                    {
                        "exercise": self.uebung.pk,
                        "self_assessed_level": 1,
                        "test_result": 10,
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["status"], "calibrated")
        self.assertEqual(len(antwort.data["results"]), 1)
        self.assertEqual(antwort.data["results"][0]["calibrated_level"], 1)

    def test_calibrate_setzt_den_reisebeginn_in_die_zeitleiste(self):
        self.client.post(
            reverse("calibrate-onboarding"),
            {
                "results": [
                    {
                        "exercise": self.uebung.pk,
                        "self_assessed_level": 1,
                        "test_result": 10,
                    }
                ]
            },
            format="json",
        )
        self.assertTrue(
            LevelEvent.objects.filter(
                user=self.user, event_type="journey_start"
            ).exists()
        )

    def test_reset_onboarding_raeumt_auf(self):
        UserProfile.objects.create(user=self.user)
        self.nutzer_progression()
        self.workout_von_heute()
        antwort = self.client.post(reverse("reset-onboarding"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["status"], "onboarding_reset")
        self.assertFalse(Workout.objects.filter(user=self.user).exists())

    def test_reset_onboarding_scheitert_ohne_profil(self):
        """Bestehendes Verhalten, festgehalten - nicht gutgeheissen:

        reset_onboarding holt das Profil mit `UserProfile.objects.get()`
        statt get_or_create. Hat ein Nutzer noch keins, fliegt
        UserProfile.DoesNotExist, wird vom breiten `except Exception`
        gefangen und als 400 gemeldet. Der Reset ist fuer solche Nutzer
        also nicht durchfuehrbar."""
        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())
        antwort = self.client.post(reverse("reset-onboarding"))
        self.assertEqual(antwort.status_code, 400)
        self.assertIn("Failed to reset onboarding", antwort.data["error"])


class FortschrittEndpunkteTest(ApiBasis):
    def test_streak_status(self):
        antwort = self.client.get(reverse("streak-status"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(
            set(antwort.data),
            {
                "current", "longest", "trained_today", "rested_today",
                "is_training_day_today", "training_days",
            },
        )

    def test_timeline_ist_anfangs_leer(self):
        antwort = self.client.get(reverse("timeline"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["events"], [])

    def test_timeline_zeigt_eigene_ereignisse(self):
        LevelEvent.objects.create(
            user=self.user, event_type="journey_start", label="Los geht's"
        )
        antwort = self.client.get(reverse("timeline"))
        self.assertEqual(len(antwort.data["events"]), 1)
        self.assertEqual(antwort.data["events"][0]["type"], "journey_start")

    def test_weekly_review(self):
        antwort = self.client.get(reverse("weekly-review"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(
            set(antwort.data),
            {
                "week_start", "week_end", "trainings_done",
                "trainings_planned", "level_ups", "push_reps", "pull_reps",
                "plank_seconds", "streak", "is_weekend",
            },
        )

    def test_rest_day_markieren(self):
        antwort = self.client.post(reverse("mark-rest-day"), {}, format="json")
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["status"], "rest_day_marked")
        self.assertTrue(antwort.data["created"])
        self.assertTrue(RestDay.objects.filter(user=self.user).exists())

    def test_rest_day_mit_eigenem_datum(self):
        antwort = self.client.post(
            reverse("mark-rest-day"), {"date": "2026-08-19"}, format="json"
        )
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["date"], "2026-08-19")

    def test_rest_day_mit_kaputtem_datum_gibt_400(self):
        antwort = self.client.post(
            reverse("mark-rest-day"), {"date": "kein-datum"}, format="json"
        )
        self.assertEqual(antwort.status_code, 400)

    def test_rest_day_entfernen(self):
        self.client.post(reverse("mark-rest-day"), {}, format="json")
        antwort = self.client.delete(reverse("unmark-rest-day"))
        self.assertEqual(antwort.status_code, 200)
        self.assertFalse(RestDay.objects.filter(user=self.user).exists())


class ProgressionEndpunkteTest(ApiBasis):
    def test_liste_der_eigenen_progressionen(self):
        self.nutzer_progression()
        antwort = self.client.get(reverse("user-progression-list"))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.data["count"], 1)

    def test_liste_zeigt_keine_fremden_progressionen(self):
        fremd = User.objects.create_user(username="fremd2", password="x")
        UserExerciseProgression.objects.create(
            user=fremd, exercise=self.uebung, current_progression=self.prog1
        )
        antwort = self.client.get(reverse("user-progression-list"))
        self.assertEqual(antwort.data["count"], 0)

    def test_detail_einer_eigenen_progression(self):
        progression = self.nutzer_progression()
        antwort = self.client.get(
            reverse("user-progression-detail", args=[progression.pk])
        )
        self.assertEqual(antwort.status_code, 200)

    def test_fremde_progression_ist_nicht_erreichbar(self):
        fremd = User.objects.create_user(username="fremd3", password="x")
        fremde = UserExerciseProgression.objects.create(
            user=fremd, exercise=self.uebung, current_progression=self.prog1
        )
        antwort = self.client.get(
            reverse("user-progression-detail", args=[fremde.pk])
        )
        self.assertEqual(antwort.status_code, 404)
