"""Die JSON-Schnittstelle - inklusive der Faelle, die sie abwehren muss."""

import json

from django.contrib.auth.models import User
from django.urls import reverse

from drafter.models import UserBrawlerPreference
from drafter.services import personal
from drafter.tests.basis import DrafterTest


class ApiTest(DrafterTest):
    def post(self, pfad, rumpf):
        return self.client.post(
            pfad, data=json.dumps(rumpf), content_type="application/json"
        )

    # --- Katalog --------------------------------------------------------
    def test_katalog_liefert_alles_fuer_die_oberflaeche(self):
        daten = self.client.get(reverse("drafter:api_katalog")).json()
        self.assertEqual(len(daten["brawler"]), 20)
        self.assertEqual(len(daten["modi"]), 5)
        self.assertFalse(daten["angemeldet"])
        self.assertTrue(all("initialen" in b for b in daten["brawler"]))

    # --- Empfehlungen ---------------------------------------------------
    def test_empfehlung_liefert_begruendete_vorschlaege(self):
        antwort = self.post(reverse("drafter:api_recommend"), {
            "map": "hart-rock-mine", "enemy_picks": ["buster"],
            "own_team_first_pick": False,
        })
        self.assertEqual(antwort.status_code, 200)
        daten = antwort.json()
        self.assertTrue(daten["empfehlungen"])
        erster = daten["empfehlungen"][0]
        self.assertTrue(erster["pro"], "Eine Empfehlung ohne Begründung ist keine")
        self.assertIn("score", erster)
        self.assertIn("komponenten", erster)
        self.assertTrue(daten["datenlage"]["nur_demo"])

    def test_ban_empfehlungen_nur_vor_dem_ersten_pick(self):
        vorher = self.post(reverse("drafter:api_recommend"), {"map": "hart-rock-mine"}).json()
        self.assertIn("ban_empfehlungen", vorher)
        self.assertTrue(all(b["gruende"] for b in vorher["ban_empfehlungen"]))

        nachher = self.post(reverse("drafter:api_recommend"), {
            "map": "hart-rock-mine", "own_picks": ["gale"],
        }).json()
        self.assertNotIn("ban_empfehlungen", nachher)

    def test_endanalyse_braucht_eigene_picks(self):
        antwort = self.post(reverse("drafter:api_final_analysis"), {
            "map": "hart-rock-mine",
        })
        self.assertEqual(antwort.status_code, 400)
        self.assertIn("fehler", antwort.json())

    def test_endanalyse_liefert_den_matchplan(self):
        daten = self.post(reverse("drafter:api_final_analysis"), {
            "map": "hart-rock-mine",
            "own_picks": ["gale", "belle", "max"],
            "enemy_picks": ["buster", "gene", "tick"],
        }).json()
        self.assertEqual(len(daten["endanalyse"]["team"]), 3)
        self.assertTrue(daten["endanalyse"]["win_condition"])

    def test_detail_liefert_die_aufschluesselung(self):
        daten = self.post(reverse("drafter:api_detail"), {
            "map": "hart-rock-mine", "enemy_picks": ["bull"], "brawler": "gale",
        }).json()
        self.assertEqual(daten["slug"], "gale")
        self.assertTrue(daten["komponenten"])
        self.assertTrue(daten["aufgaben"])

    def test_detail_verweigert_gepickte_brawler(self):
        antwort = self.post(reverse("drafter:api_detail"), {
            "map": "hart-rock-mine", "own_picks": ["gale"], "brawler": "gale",
        })
        self.assertEqual(antwort.status_code, 400)

    # --- Abwehr ---------------------------------------------------------
    def test_ungueltige_eingaben_werden_abgewiesen(self):
        faelle = [
            {"map": "gibtsnicht"},
            {"map": "hart-rock-mine", "own_picks": "gale"},
            {"map": "hart-rock-mine", "own_picks": ["gale", "gale"]},
            {"map": "hart-rock-mine", "own_picks": ["gale", "belle", "max", "tick"]},
            {"map": "hart-rock-mine", "own_picks": ["gibtsnicht"]},
            {"map": "hart-rock-mine", "bans": [{"boese": True}]},
        ]
        for fall in faelle:
            antwort = self.post(reverse("drafter:api_recommend"), fall)
            self.assertEqual(antwort.status_code, 400, msg=str(fall))
            self.assertIn("fehler", antwort.json())

    def test_kaputtes_json_wird_abgefangen(self):
        antwort = self.client.post(
            reverse("drafter:api_recommend"), data="{kaputt", content_type="application/json"
        )
        self.assertEqual(antwort.status_code, 400)

    def test_get_auf_post_endpunkt_wird_abgewiesen(self):
        self.assertEqual(self.client.get(reverse("drafter:api_recommend")).status_code, 405)


class ConfidenceApiTest(DrafterTest):
    def post(self, rumpf):
        return self.client.post(
            reverse("drafter:api_confidence"), data=json.dumps(rumpf),
            content_type="application/json",
        )

    def test_gast_speichert_in_der_session(self):
        antwort = self.post({"brawler": "gale", "confidence": 80})
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.json()["gespeichert"], "session")
        self.assertEqual(
            self.client.session[personal.SESSION_SCHLUESSEL]["gale"], 80
        )
        self.assertFalse(UserBrawlerPreference.objects.exists())

    def test_angemeldeter_nutzer_speichert_im_konto(self):
        User.objects.create_user("tester", password="geheim1234")
        self.client.login(username="tester", password="geheim1234")
        antwort = self.post({"brawler": "gale", "confidence": 90})
        self.assertEqual(antwort.json()["gespeichert"], "konto")
        eintrag = UserBrawlerPreference.objects.get()
        self.assertEqual(eintrag.confidence, 90)
        self.assertEqual(eintrag.user.username, "tester")

    def test_werte_werden_auf_0_bis_100_begrenzt(self):
        self.post({"brawler": "gale", "confidence": 5000})
        self.assertEqual(self.client.session[personal.SESSION_SCHLUESSEL]["gale"], 100)

    def test_nutzer_kann_nur_eigene_werte_aendern(self):
        """Der Nutzer kommt aus der Session, nie aus dem Request."""
        fremder = User.objects.create_user("fremder", password="geheim1234")
        User.objects.create_user("ich", password="geheim1234")
        self.client.login(username="ich", password="geheim1234")
        self.post({"brawler": "gale", "confidence": 10, "user": fremder.id})
        self.assertFalse(UserBrawlerPreference.objects.filter(user=fremder).exists())
        self.assertTrue(UserBrawlerPreference.objects.filter(user__username="ich").exists())

    def test_unsinnige_werte_werden_abgewiesen(self):
        self.assertEqual(self.post({"brawler": "gale", "confidence": "viel"}).status_code, 400)
        self.assertEqual(self.post({"brawler": "gibtsnicht", "confidence": 50}).status_code, 400)


class SeitenTest(DrafterTest):
    def test_draftseite_ist_oeffentlich(self):
        antwort = self.client.get(reverse("drafter:draft"))
        self.assertEqual(antwort.status_code, 200)
        self.assertContains(antwort, "Demo-Daten")

    def test_meine_brawler_verlangt_anmeldung(self):
        antwort = self.client.get(reverse("drafter:meine_brawler"))
        self.assertEqual(antwort.status_code, 302)
        self.assertIn("/draft/login/", antwort["Location"])

    def test_meine_brawler_zeigt_alle_brawler(self):
        User.objects.create_user("tester", password="geheim1234")
        self.client.login(username="tester", password="geheim1234")
        antwort = self.client.get(reverse("drafter:meine_brawler"))
        self.assertEqual(antwort.status_code, 200)
        # Auf das Attribut pruefen, nicht auf den Klassennamen: der
        # steht auch im Skript der Seite als CSS-Selektor.
        self.assertContains(antwort, 'class="confidence-zeile"', count=20)

    def test_loginseite_erreichbar(self):
        self.assertEqual(self.client.get(reverse("drafter:login")).status_code, 200)
