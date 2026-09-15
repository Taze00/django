# -*- coding: utf-8 -*-
"""Parser und Import des offiziellen Battlelogs - gegen eine echte Antwort.

Grundlage ist ein anonymisierter Mitschnitt von /players/{tag}/battlelog
(drafter/testdaten/offizieller_battlelog_anonymisiert.json). Kein Test
braucht das Netz.

Erwartete Zahlen (17 Partien, 8 Showdown) sind Eigenschaften genau dieser
Datei. Feldinhalte werden dagegen aus der Rohantwort selbst abgeleitet,
nicht auswendig hingeschrieben.
"""

import copy
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from drafter.models import Brawler, Datenquelle
from drafter.models.matches import Match, MatchPlayer, RawPayload
from drafter.services.ingest.importer import MatchImporter
from drafter.services.ingest.parser import (
    FORMAT_OFFIZIELLER_BATTLELOG, ParserFehler, parse_offizieller_battlelog, parser_fuer,
)
from drafter.services.providers.fixture import FixtureDataProvider
from drafter.services.providers.official_api import OfficialBrawlAPIProvider
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import FixtureMixin

FIXTURE = Path(settings.BASE_DIR) / "drafter" / "testdaten" / "offizieller_battlelog_anonymisiert.json"


def lade():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def team_eintraege(daten):
    return [e for e in daten["antwort"]["items"] if "teams" in e["battle"]]


class FixtureTest(SimpleTestCase):
    def test_fixture_ist_anonymisiert(self):
        daten = lade()
        self.assertTrue(daten["referenz"].startswith("#TEST"))
        for eintrag in daten["antwort"]["items"]:
            b = eintrag["battle"]
            alle = [s for t in b.get("teams", []) for s in t] + b.get("players", [])
            alle += [b["starPlayer"]] if "starPlayer" in b else []
            for s in alle:
                self.assertTrue(s["tag"].startswith("#TEST"), s["tag"])
                self.assertTrue(s["name"].startswith("Spieler "), s["name"])

    def test_keine_geheimnisse_in_der_datei(self):
        text = FIXTURE.read_text(encoding="utf-8").lower()
        self.assertNotIn("authorization", text)
        self.assertNotIn("bearer", text)


class ParserTest(SimpleTestCase):
    def test_parser_ist_registriert(self):
        self.assertIs(parser_fuer(FORMAT_OFFIZIELLER_BATTLELOG), parse_offizieller_battlelog)

    def test_partien_und_showdown(self):
        ergebnis = parse_offizieller_battlelog(lade())
        self.assertEqual(len(ergebnis.matches), 17)
        self.assertEqual(len(ergebnis.uebersprungen), 8)
        self.assertEqual(ergebnis.fehler, [])
        self.assertTrue(all("soloShowdown" in grund for grund in ergebnis.uebersprungen))

    def test_felder_kommen_unveraendert_aus_der_antwort(self):
        daten = lade()
        ergebnis = parse_offizieller_battlelog(daten)
        for record, roh in zip(ergebnis.matches, team_eintraege(daten)):
            b, e = roh["battle"], roh["event"]
            self.assertEqual(record.played_at, datetime.strptime(
                roh["battleTime"], "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=timezone.utc))
            self.assertEqual(record.mode, b["mode"])
            self.assertEqual(record.map, e["map"])
            self.assertEqual(record.external_map_id, str(e["id"]))
            self.assertEqual(record.external_mode_id, str(e["modeId"]))
            self.assertEqual(record.battle_type, b["type"])
            self.assertEqual(record.duration_seconds, b.get("duration"))
            for seite, team in zip(("a", "b"), b["teams"]):
                for spieler, roh_spieler in zip(record.teams[seite], team):
                    self.assertEqual(spieler.player_tag, roh_spieler["tag"])
                    self.assertEqual(spieler.external_brawler_id, str(roh_spieler["brawler"]["id"]))
                    self.assertEqual(spieler.brawler, roh_spieler["brawler"]["name"])
                    self.assertEqual(spieler.power, roh_spieler["brawler"]["power"])
                    self.assertEqual(spieler.trophies, roh_spieler["brawler"]["trophies"])

    def test_nichts_erfunden_was_die_antwort_nicht_hat(self):
        for record in parse_offizieller_battlelog(lade()).matches:
            self.assertIsNone(record.external_id, "Die Antwort hat keine Partie-ID")
            self.assertEqual(record.bans, [])
            self.assertIsNone(record.first_pick)
            self.assertEqual(record.rank_pool, "alle")
            for spieler in record.teams["a"] + record.teams["b"]:
                self.assertIsNone(spieler.pick_order)
                self.assertIsNone(spieler.build)

    def test_ranked_nur_fuer_solo_ranked(self):
        daten = lade()
        for record, roh in zip(parse_offizieller_battlelog(daten).matches, team_eintraege(daten)):
            self.assertEqual(record.ranked, roh["battle"]["type"] == "soloRanked")
        self.assertEqual(sum(r.ranked for r in parse_offizieller_battlelog(daten).matches), 4)

    def test_ergebnis_wird_aus_sicht_des_abgefragten_spielers_umgerechnet(self):
        daten = lade()
        zweites_team = 0
        for record, roh in zip(parse_offizieller_battlelog(daten).matches, team_eintraege(daten)):
            index = next(i for i, t in enumerate(roh["battle"]["teams"])
                         if any(s["tag"] == daten["referenz"] for s in t))
            eigene = "ab"[index]
            erwartet = eigene if roh["battle"]["result"] == "victory" else "ab"[1 - index]
            self.assertEqual(record.winner, erwartet)
            zweites_team += index == 1
        self.assertGreater(zweites_team, 0, "Fixture muss den Fall 'eigenes Team = teams[1]' enthalten")

    def test_unbekanntes_ergebnis_ergibt_keinen_sieger(self):
        daten = lade()
        for eintrag in team_eintraege(daten):
            eintrag["battle"]["result"] = "draw"
        self.assertTrue(all(r.winner is None for r in parse_offizieller_battlelog(daten).matches))

    def test_ohne_perspektive_kein_sieger(self):
        daten = lade()
        daten["referenz"] = "#GIBTSNICHT"
        self.assertTrue(all(r.winner is None for r in parse_offizieller_battlelog(daten).matches))

    def test_unbekannte_zusatzfelder_stoeren_nicht(self):
        daten = lade()
        erweitert = copy.deepcopy(daten)
        erweitert["neuesHuellenfeld"] = 1
        erweitert["antwort"]["neuesFeld"] = {"x": 1}
        for eintrag in erweitert["antwort"]["items"]:
            eintrag["neuesFeld"] = [1, 2]
            eintrag["event"]["neuesFeld"] = "x"
            eintrag["battle"]["neuesFeld"] = True
            for team in eintrag["battle"].get("teams", []):
                for s in team:
                    s["neuesFeld"] = None
                    s["brawler"]["neuesFeld"] = {"tief": 1}
        vorher = [asdict(r) for r in parse_offizieller_battlelog(daten).matches]
        nachher = [asdict(r) for r in parse_offizieller_battlelog(erweitert).matches]
        self.assertEqual(vorher, nachher)

    def test_fehlende_optionale_felder(self):
        daten = lade()
        eintrag = team_eintraege(daten)[0]
        for feld in ("duration", "result", "starPlayer", "trophyChange", "type"):
            eintrag["battle"].pop(feld, None)
        eintrag["event"].pop("id")
        eintrag["event"].pop("modeId")
        record = parse_offizieller_battlelog(daten).matches[0]
        self.assertIsNone(record.duration_seconds)
        self.assertIsNone(record.winner)
        self.assertIsNone(record.external_map_id)
        self.assertIsNone(record.battle_type)
        self.assertFalse(record.ranked)

    def test_kaputter_eintrag_verwirft_nicht_die_datei(self):
        daten = lade()
        team_eintraege(daten)[0]["battleTime"] = "gestern"
        ergebnis = parse_offizieller_battlelog(daten)
        self.assertEqual(len(ergebnis.fehler), 1)
        self.assertEqual(len(ergebnis.matches), 16)

    def test_ohne_items_nicht_auswertbar(self):
        daten = lade()
        daten["antwort"] = {"hinweis": "kein Battlelog"}
        with self.assertRaises(ParserFehler):
            parse_offizieller_battlelog(daten)


class ImportTest(FixtureMixin, DrafterTest):
    def importiere_datei(self, pfad=FIXTURE):
        return MatchImporter(FixtureDataProvider(pfad)).ausfuehren()

    def test_dieselbe_antwort_zweimal_ist_idempotent(self):
        erster = self.importiere_datei()
        zweiter = self.importiere_datei()
        self.assertEqual(erster.neu, 17)
        self.assertEqual(erster.uebersprungen, 8)
        self.assertEqual(erster.ungueltig, 0)
        self.assertEqual(zweiter.bereits_importiert, 1)
        self.assertEqual(Match.objects.count(), 17)
        self.assertEqual(MatchPlayer.objects.count(), 17 * 6)
        self.assertEqual(RawPayload.objects.count(), 1)

    def test_rohantwort_bleibt_unveraendert_gespeichert(self):
        self.importiere_datei()
        payload = RawPayload.objects.get()
        self.assertEqual(payload.payload, lade())
        self.assertEqual(payload.source, Datenquelle.FIXTURE)
        self.assertIn("ÜBERSPRUNGEN", payload.parse_message)

    def test_beobachtete_felder_werden_gespeichert(self):
        self.importiere_datei()
        self.assertEqual(set(Match.objects.values_list("battle_type", flat=True)), {"ranked", "soloRanked"})
        self.assertEqual(Match.objects.filter(is_ranked=True).count(), 4)
        self.assertFalse(MatchPlayer.objects.filter(power__isnull=True).exists())
        self.assertFalse(MatchPlayer.objects.filter(trophies__isnull=True).exists())
        self.assertTrue(all(m.external_id == "" and m.reconstructed_fingerprint for m in Match.objects.all()))

    def test_id_vor_name(self):
        daten = lade()
        katalog_namen = {b.name.upper(): b for b in Brawler.objects.all()}
        roh_brawler = next(
            (s["brawler"] for e in team_eintraege(daten) for t in e["battle"]["teams"] for s in t
             if s["brawler"]["name"].upper() in katalog_namen),
            None,
        )
        self.assertIsNotNone(roh_brawler, "Kein Brawler der Antwort steht im Demo-Katalog")
        katalog = katalog_namen[roh_brawler["name"].upper()]
        katalog.external_id = str(roh_brawler["id"])
        katalog.save()
        # Name absichtlich falsch - zugeordnet werden muss trotzdem ueber die ID.
        for eintrag in team_eintraege(daten):
            for team in eintrag["battle"]["teams"]:
                for s in team:
                    if s["brawler"]["id"] == roh_brawler["id"]:
                        s["brawler"]["name"] = "FALSCHER NAME"
        bericht = MatchImporter(FixtureDataProvider(self.schreibe(daten))).ausfuehren()
        self.assertGreater(bericht.zuordnung_per_id, 0)
        self.assertFalse(MatchPlayer.objects.filter(brawler_name="FALSCHER NAME", brawler__isnull=True).exists())
        self.assertTrue(MatchPlayer.objects.filter(brawler_name="FALSCHER NAME", brawler=katalog).exists())

    def test_modusname_in_camelcase_findet_den_katalogmodus(self):
        self.importiere_datei()
        brawl_ball = Match.objects.filter(mode_name="brawlBall")
        self.assertTrue(brawl_ball.exists())
        self.assertEqual({m.game_mode.slug for m in brawl_ball}, {"brawl-ball"})

    def test_andere_perspektive_ist_dublette_ohne_konflikt(self):
        """Dieselbe Partie aus dem Battlelog eines Gegners: Seiten und Ergebnis gespiegelt."""
        self.importiere_datei()
        daten = lade()
        eintrag = team_eintraege(daten)[0]
        gegner_tag = eintrag["battle"]["teams"][1][0]["tag"]
        if any(s["tag"] == daten["referenz"] for s in eintrag["battle"]["teams"][1]):
            gegner_tag = eintrag["battle"]["teams"][0][0]["tag"]
        eintrag["battle"]["result"] = {"victory": "defeat", "defeat": "victory"}[eintrag["battle"]["result"]]
        eintrag["battle"]["teams"].reverse()
        daten["referenz"] = gegner_tag
        daten["antwort"]["items"] = [eintrag]

        bericht = MatchImporter(FixtureDataProvider(self.schreibe(daten))).ausfuehren()
        self.assertEqual(bericht.duplikate, 1)
        self.assertEqual(bericht.konflikte, 0)
        self.assertEqual(Match.objects.count(), 17)

    def test_offizieller_provider_liefert_partien(self):
        daten = lade()

        class Client:
            einsatzbereit = True

            def battlelog(self, tag):
                return daten["antwort"]

        provider = OfficialBrawlAPIProvider(client=Client(), spieler_tags=[daten["referenz"]])
        lieferung = next(provider.lieferungen())
        self.assertEqual(len(lieferung.matches), 17)
        self.assertEqual(len(lieferung.uebersprungen), 8)
