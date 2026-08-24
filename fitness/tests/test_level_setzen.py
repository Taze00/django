"""Level von Hand setzen (Profil -> Level anpassen).

Der Endpunkt adressiert die UserExerciseProgression, nicht die Uebung. Und er
muss pruefen, dass die gewaehlte Stufe ueberhaupt zu dieser Uebung gehoert -
sonst laesst sich ein Push-up-Level an den Pull-ups setzen.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fitness.models import Exercise, Progression, UserExerciseProgression


class LevelSetzenBasis(TestCase):
    def setUp(self):
        # Ein Vornutzer, damit Uebungs-IDs und Progressions-IDs
        # auseinanderlaufen - genau die Lage, in der der Fehler auffiel.
        self.vorher = User.objects.create_user(username="erster", password="geheim1234")
        self.user = User.objects.create_user(username="zweiter", password="geheim1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.push = Exercise.objects.create(name="Push-ups", category="PUSH", order=1)
        self.pull = Exercise.objects.create(name="Pull-ups", category="PULL", order=2)
        self.push_stufen = {
            n: Progression.objects.create(
                exercise=self.push, level=n, name=f"Push {n}",
                target_type="reps", target_value=10)
            for n in (1, 2, 3)
        }
        self.pull_stufen = {
            n: Progression.objects.create(
                exercise=self.pull, level=n, name=f"Pull {n}",
                target_type="time", target_value=30)
            for n in (1, 2, 3)
        }
        for u in (self.vorher, self.user):
            UserExerciseProgression.objects.create(
                user=u, exercise=self.push, current_progression=self.push_stufen[1],
                training_days=[1, 2, 3, 4, 5])
            UserExerciseProgression.objects.create(
                user=u, exercise=self.pull, current_progression=self.pull_stufen[1],
                training_days=[1, 2, 3, 4, 5])

        self.eintrag = UserExerciseProgression.objects.get(user=self.user, exercise=self.push)

    def setzen(self, pk, progression_id):
        return self.client.patch(
            reverse("user-progression-detail", args=[pk]),
            {"current_progression": progression_id}, format="json")


class RichtigeAdressierungTest(LevelSetzenBasis):
    def test_uebungs_id_und_eintrags_id_laufen_auseinander(self):
        """Die Voraussetzung des Fehlers: nur bei Nutzer 1 stimmen beide
        zufaellig ueberein."""
        self.assertNotEqual(self.eintrag.id, self.push.id)

    def test_setzen_ueber_die_eintrags_id_funktioniert(self):
        antwort = self.setzen(self.eintrag.id, self.push_stufen[3].id)

        self.assertEqual(antwort.status_code, 200)
        self.eintrag.refresh_from_db()
        self.assertEqual(self.eintrag.current_progression.level, 3)

    def test_fremder_eintrag_ist_nicht_erreichbar(self):
        fremd = UserExerciseProgression.objects.get(user=self.vorher, exercise=self.push)

        antwort = self.setzen(fremd.id, self.push_stufen[3].id)

        self.assertEqual(antwort.status_code, 404)
        fremd.refresh_from_db()
        self.assertEqual(fremd.current_progression.level, 1)


class ZugehoerigkeitTest(LevelSetzenBasis):
    def test_stufe_einer_fremden_uebung_wird_abgewiesen(self):
        pull_eintrag = UserExerciseProgression.objects.get(user=self.user, exercise=self.pull)

        antwort = self.setzen(pull_eintrag.id, self.push_stufen[3].id)

        self.assertEqual(antwort.status_code, 400)
        self.assertIn("Pull-ups", antwort.data["error"])
        pull_eintrag.refresh_from_db()
        self.assertEqual(pull_eintrag.current_progression.level, 1, "Stufe wurde gesetzt")

    def test_eigene_stufe_wird_angenommen(self):
        pull_eintrag = UserExerciseProgression.objects.get(user=self.user, exercise=self.pull)

        antwort = self.setzen(pull_eintrag.id, self.pull_stufen[2].id)

        self.assertEqual(antwort.status_code, 200)
        pull_eintrag.refresh_from_db()
        self.assertEqual(pull_eintrag.current_progression.level, 2)

    def test_unbekannte_stufe_gibt_400(self):
        antwort = self.setzen(self.eintrag.id, 99999)

        self.assertEqual(antwort.status_code, 400)
        self.eintrag.refresh_from_db()
        self.assertEqual(self.eintrag.current_progression.level, 1)
