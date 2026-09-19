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
        from drafter.models import GameMode
        self.assertEqual(len(daten["brawler"]), 20)
        # So viele Modi, wie ein Zielprofil UND eine wählbare Map haben -
        # keine feste Zahl. Hot Zone kam am 2026-09-19 als Modus dazu,
        # seine Maps stammen aber aus der Beobachtung und fehlen im
        # reinen Demo-Datensatz; angeboten wird er dann nicht.
        erwartet = sum(1 for m in GameMode.objects.filter(is_active=True)
                       if m.maps.waehlbare().exists())
        self.assertEqual(len(daten["modi"]), erwartet)
        self.assertTrue(all(m["maps"] for m in daten["modi"]),
                        "jeder angebotene Modus braucht eine wählbare Map")
        self.assertFalse(daten["angemeldet"])
        self.assertTrue(all("initialen" in b for b in daten["brawler"]))

    def test_katalog_liefert_rollen_in_kanonischer_reihenfolge(self):
        from drafter import attributes as attr
        daten = self.client.get(reverse("drafter:api_katalog")).json()
        self.assertEqual([r["key"] for r in daten["rollen"]], list(attr.ROLLEN_KEYS))
        self.assertTrue(all("image_url" in k for m in daten["modi"] for k in m["maps"]))

    # --- Empfehlungen ---------------------------------------------------
    def test_empfehlung_liefert_begruendete_vorschlaege(self):
        antwort = self.post(reverse("drafter:api_recommend"), {
            "map": "hard-rock-mine", "enemy_picks": ["buster"],
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

    def test_scores_decken_den_ganzen_pool_ab(self):
        # Das Gitter zeigt alle verfuegbaren Brawler mit Score und sortiert
        # danach - die Spitze allein (acht Empfehlungen) reicht dafuer nicht.
        daten = self.post(reverse("drafter:api_recommend"), {
            "map": "hard-rock-mine", "bans": ["gale"], "enemy_picks": ["buster"],
        }).json()
        scores = daten["scores"]
        self.assertEqual(len(scores), 20 - 2, "gebannt und gepickt fehlen, sonst alle")
        self.assertNotIn("gale", scores)
        self.assertNotIn("buster", scores)
        # Die angezeigte Spitze ist dieselbe Rechnung, nicht eine zweite.
        for e in daten["empfehlungen"]:
            self.assertEqual(scores[e["slug"]], e["score"])
        spitze = [e["score"] for e in daten["empfehlungen"]]
        rest = [v for k, v in scores.items()
                if k not in {e["slug"] for e in daten["empfehlungen"]}]
        self.assertLessEqual(max(rest), min(spitze))

    def test_ban_empfehlungen_nur_vor_dem_ersten_pick(self):
        vorher = self.post(reverse("drafter:api_recommend"), {"map": "hard-rock-mine"}).json()
        self.assertIn("ban_empfehlungen", vorher)
        self.assertTrue(all(b["gruende"] for b in vorher["ban_empfehlungen"]))

        nachher = self.post(reverse("drafter:api_recommend"), {
            "map": "hard-rock-mine", "own_picks": ["gale"],
        }).json()
        self.assertNotIn("ban_empfehlungen", nachher)

    def test_endanalyse_braucht_eigene_picks(self):
        antwort = self.post(reverse("drafter:api_final_analysis"), {
            "map": "hard-rock-mine",
        })
        self.assertEqual(antwort.status_code, 400)
        self.assertIn("fehler", antwort.json())

    def test_endanalyse_liefert_den_matchplan(self):
        daten = self.post(reverse("drafter:api_final_analysis"), {
            "map": "hard-rock-mine",
            "own_picks": ["gale", "belle", "max"],
            "enemy_picks": ["buster", "gene", "tick"],
        }).json()
        self.assertEqual(len(daten["endanalyse"]["team"]), 3)
        self.assertTrue(daten["endanalyse"]["win_condition"])

    def test_endanalyse_enthaelt_alle_bausteine_des_coaches(self):
        """Die Liste der zugesagten Auskuenfte - Stueck fuer Stueck."""
        analyse = self.post(reverse("drafter:api_final_analysis"), {
            "map": "hard-rock-mine",
            "own_picks": ["gale", "belle", "max"],
            "enemy_picks": ["buster", "gene", "tick"],
        }).json()["endanalyse"]

        for schluessel in ("siegchance", "datenlage", "win_condition", "schwaechen",
                           "lanes", "matchups", "lane_tausch", "team"):
            self.assertIn(schluessel, analyse)

        for spieler in analyse["team"]:
            for schluessel in ("rolle", "hauptaufgabe", "bevorzugtes_matchup",
                               "zu_vermeidendes_matchup", "lane", "warnungen", "build"):
                self.assertIn(schluessel, spieler, msg=spieler["name"])
            self.assertTrue(spieler["rolle"])
            self.assertTrue(spieler["hauptaufgabe"])
            self.assertTrue(spieler["lane"])

        self.assertTrue(analyse["siegchance"]["ist_heuristik"])
        self.assertTrue(analyse["datenlage"]["nur_demo"])

    def test_jeder_spieler_bekommt_einen_eigenen_gegner_zugewiesen(self):
        """Team-Zuordnung und Spielerkarte duerfen sich nicht widersprechen."""
        analyse = self.post(reverse("drafter:api_final_analysis"), {
            "map": "hard-rock-mine",
            "own_picks": ["gale", "belle", "max"],
            "enemy_picks": ["buster", "gene", "tick"],
        }).json()["endanalyse"]

        aus_karten = {
            s["bevorzugtes_matchup"]["gegner"] for s in analyse["team"]
            if s["bevorzugtes_matchup"]
        }
        aus_teamplan = {m["gegner"] for m in analyse["matchups"]}
        self.assertEqual(len(aus_karten), 3, "Zwei Spieler auf denselben Gegner angesetzt")
        self.assertEqual(aus_karten, aus_teamplan)

    def test_jede_empfehlung_liefert_die_aufschluesselung(self):
        daten = self.post(reverse("drafter:api_recommend"), {
            "map": "hard-rock-mine", "own_picks": ["gale"], "enemy_picks": ["bull"],
        }).json()
        self.assertTrue(daten["empfehlungen"])
        for e in daten["empfehlungen"]:
            self.assertEqual(len(e["komponenten"]), 11, msg=e["name"])
            summe = sum(k["beitrag"] for k in e["komponenten"])
            self.assertAlmostEqual(50 + summe, e["score"], delta=1.0, msg=e["name"])
            self.assertTrue(e["groesster_treiber"])
            # Coach-Auskuenfte ebenfalls fuer jede angezeigte Empfehlung.
            self.assertIn("build", e)
            self.assertIn("warnungen", e)

    def test_detail_liefert_die_aufschluesselung(self):
        daten = self.post(reverse("drafter:api_detail"), {
            "map": "hard-rock-mine", "enemy_picks": ["bull"], "brawler": "gale",
        }).json()
        self.assertEqual(daten["slug"], "gale")
        self.assertTrue(daten["komponenten"])
        self.assertTrue(daten["aufgaben"])

    def test_detail_verweigert_gepickte_brawler(self):
        antwort = self.post(reverse("drafter:api_detail"), {
            "map": "hard-rock-mine", "own_picks": ["gale"], "brawler": "gale",
        })
        self.assertEqual(antwort.status_code, 400)

    # --- Abwehr ---------------------------------------------------------
    def test_ungueltige_eingaben_werden_abgewiesen(self):
        faelle = [
            {"map": "gibtsnicht"},
            {"map": "hard-rock-mine", "own_picks": "gale"},
            {"map": "hard-rock-mine", "own_picks": ["gale", "gale"]},
            {"map": "hard-rock-mine", "own_picks": ["gale", "belle", "max", "tick"]},
            {"map": "hard-rock-mine", "own_picks": ["gibtsnicht"]},
            {"map": "hard-rock-mine", "bans": [{"boese": True}]},
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
