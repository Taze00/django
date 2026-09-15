# -*- coding: utf-8 -*-
"""Import: idempotent, dedupliziert, und nichts wird geraten."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from drafter.models import Datenquelle, Patch
from drafter.models.matches import Match, MatchPlayer, RawPayload
from drafter.services.ingest.importer import MatchImporter
from drafter.services.ingest.parser import FORMAT_OFFIZIELLER_SPIELER
from drafter.services.providers.fixture import FixtureDataProvider
from drafter.services.providers.official_api import OfficialBrawlAPIProvider
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import FixtureMixin, datei, partie


class IdempotenzTest(FixtureMixin, DrafterTest):
    def test_dieselbe_datei_zweimal_aendert_nichts(self):
        pfad = self.schreibe(datei([partie(), partie(minuten=10)]))
        erster = MatchImporter(FixtureDataProvider(pfad)).ausfuehren()
        zweiter = MatchImporter(FixtureDataProvider(pfad)).ausfuehren()

        self.assertEqual(erster.neu, 2)
        self.assertEqual(zweiter.neu, 0)
        self.assertEqual(zweiter.bereits_importiert, 1)
        self.assertEqual(Match.objects.count(), 2)
        self.assertEqual(RawPayload.objects.count(), 1)
        self.assertEqual(MatchPlayer.objects.count(), 12)

    def test_gleicher_inhalt_in_anderer_schreibweise_gilt_als_dieselbe_lieferung(self):
        inhalt = datei([partie()])
        self.schreibe(json.dumps(inhalt), name="kompakt.json")
        self.schreibe(json.dumps(inhalt, indent=4, sort_keys=True), name="huebsch.json")
        bericht = MatchImporter(FixtureDataProvider(self.verzeichnis)).ausfuehren()
        self.assertEqual(bericht.neu, 1)
        self.assertEqual(bericht.bereits_importiert, 1)

    def test_import_kommando_ist_idempotent(self):
        pfad = self.schreibe(datei([partie()]))
        call_command("import_brawl_fixture", str(pfad), verbosity=0, stdout=_Stumm())
        call_command("import_brawl_fixture", str(pfad), verbosity=0, stdout=_Stumm())
        self.assertEqual(Match.objects.count(), 1)

    def test_import_kommando_ohne_dateien_bricht_verstaendlich_ab(self):
        with self.assertRaises(CommandError):
            call_command("import_brawl_fixture", str(self.verzeichnis / "leer"), stdout=_Stumm())

    def test_trockenlauf_speichert_nichts(self):
        bericht = self.importiere(partie(), trockenlauf=True)
        self.assertEqual(bericht.neu, 1)
        self.assertEqual(Match.objects.count(), 0)
        self.assertEqual(RawPayload.objects.count(), 0)


class DeduplizierungTest(FixtureMixin, DrafterTest):
    def test_dieselbe_partie_aus_zwei_battlelogs_zaehlt_einmal(self):
        """Zweite Sichtung: andere Datei, andere Perspektive, 20 s spaeter."""
        self.importiere(partie(a=("gale", "belle", "max"), b=("buster", "gene", "tick"), sieger="a"))
        bericht = self.importiere(partie(
            a=("tick", "buster", "gene"), b=("max", "gale", "belle"), sieger="b", sekunden=20,
        ))

        self.assertEqual(bericht.neu, 0)
        self.assertEqual(bericht.duplikate, 1)
        self.assertEqual(bericht.konflikte, 0)
        match = Match.objects.get()
        self.assertEqual(match.gesehen, 2)
        self.assertFalse(match.has_conflict)

        # Gewonnen hat das Gale-Team - egal, aus welcher Sicht gespeichert.
        sieger = {s.brawler_name for s in match.players.filter(side=match.winner_side)}
        self.assertEqual(sieger, {"gale", "belle", "max"})

    def test_toleranz_greift_ueber_eine_minutengrenze(self):
        self.importiere(partie(sekunden=55))
        bericht = self.importiere(partie(minuten=1, sekunden=40))   # 45 s spaeter, anderer Eimer
        self.assertEqual(bericht.duplikate, 1)
        self.assertEqual(Match.objects.count(), 1)

    def test_ausserhalb_der_toleranz_sind_es_zwei_partien(self):
        self.importiere(partie())
        self.importiere(partie(minuten=5))
        self.assertEqual(Match.objects.count(), 2)

    def test_andere_teams_zur_selben_zeit_sind_zwei_partien(self):
        self.importiere(partie(a=("gale", "belle", "max")), partie(a=("gale", "belle", "piper")))
        self.assertEqual(Match.objects.count(), 2)

    def test_doppelter_eintrag_in_derselben_datei(self):
        bericht = self.importiere(partie(), partie())
        self.assertEqual(bericht.neu, 1)
        self.assertEqual(bericht.duplikate, 1)
        self.assertEqual(Match.objects.count(), 1)

    def test_spieler_tags_beeinflussen_die_erkennung_nicht(self):
        mit_tags = partie(a=[{"brawler": "gale", "player_tag": "#SYNTH1"}, "belle", "max"])
        self.importiere(mit_tags)
        self.importiere(partie())
        self.assertEqual(Match.objects.count(), 1)

    def test_eigene_partie_id_hat_vorrang(self):
        self.importiere(partie(external_id="synth-1"))
        # Andere Minute, aber gleiche ID - dieselbe Partie.
        bericht = self.importiere(partie(minuten=30, external_id="synth-1"))
        self.assertEqual(bericht.duplikate, 1)


class KonfliktTest(FixtureMixin, DrafterTest):
    def test_widerspruechliches_ergebnis_wird_markiert_und_nicht_gezaehlt(self):
        self.importiere(partie(sieger="a"))
        bericht = self.importiere(partie(sieger="b", sekunden=5))
        match = Match.objects.get()
        self.assertEqual(bericht.konflikte, 1)
        self.assertTrue(match.has_conflict)
        self.assertFalse(match.ist_zaehlbar)
        self.assertIn("Widersprüchliches", match.conflict_note)

    def test_unentschieden_ist_kein_zaehlbares_ergebnis(self):
        self.importiere(partie(sieger="draw"))
        self.assertFalse(Match.objects.get().ist_zaehlbar)

    def test_nachgeliefertes_ergebnis_wird_uebernommen(self):
        self.importiere(partie(sieger=None))
        self.importiere(partie(sieger="a", sekunden=5))
        match = Match.objects.get()
        self.assertEqual(match.winner_side, "a")
        self.assertFalse(match.has_conflict)


class NichtsWirdGeratenTest(FixtureMixin, DrafterTest):
    def test_unbekannte_brawler_und_maps_bleiben_mit_namen_erhalten(self):
        bericht = self.importiere(partie(a=("Kit", "belle", "max"), karte="Unbekannte Testmap"))
        self.assertIn("Kit", bericht.unbekannte_brawler)
        self.assertIn("Unbekannte Testmap", bericht.unbekannte_maps)
        match = Match.objects.get()
        self.assertIsNone(match.brawl_map)
        self.assertEqual(match.map_name, "Unbekannte Testmap")
        kit = match.players.get(brawler_name="Kit")
        self.assertIsNone(kit.brawler)

    def test_namen_werden_ueber_den_katalogschluessel_abgebildet(self):
        self.importiere(partie(a=("GALE", "Belle", "max"), karte="HARD ROCK MINE"))
        match = Match.objects.get()
        self.assertEqual(match.brawl_map.slug, "hard-rock-mine")
        self.assertEqual(match.players.filter(brawler__isnull=False).count(), 6)

    def test_fehlende_felder_bleiben_leer(self):
        self.importiere(partie())
        match = Match.objects.get()
        self.assertEqual(match.first_pick_side, "")
        self.assertFalse(match.bans.exists())
        self.assertTrue(all(s.pick_order is None and s.build is None for s in match.players.all()))

    def test_patch_zum_spielzeitpunkt(self):
        Patch.objects.all().delete()
        alt = Patch.objects.create(name="Alt", released_on=(_basis_datum(-30)))
        neu = Patch.objects.create(name="Neu", released_on=(_basis_datum(-3)))
        self.importiere(partie(tage_zurueck=10), partie(tage_zurueck=1))
        self.assertEqual(Match.objects.get(played_at__lt=_basis_zeit(-5)).patch, alt)
        self.assertEqual(Match.objects.get(played_at__gt=_basis_zeit(-5)).patch, neu)


class LieferungsfehlerTest(FixtureMixin, DrafterTest):
    def test_ungueltige_partie_wird_verworfen_der_rest_importiert(self):
        kaputt = partie(minuten=10)
        kaputt["winner"] = "vielleicht"
        bericht = self.importiere(partie(), kaputt)
        self.assertEqual(bericht.neu, 1)
        self.assertEqual(bericht.ungueltig, 1)

    def test_ohne_herkunft_wird_nichts_gespeichert(self):
        inhalt = datei([partie()])
        del inhalt["herkunft"]
        bericht = MatchImporter(FixtureDataProvider(self.schreibe(inhalt))).ausfuehren()
        self.assertEqual(bericht.fehlerhaft, 1)
        self.assertEqual(RawPayload.objects.count(), 0)

    def test_zeitpunkt_ohne_zeitzone_wird_abgelehnt(self):
        ohne_zone = partie()
        ohne_zone["played_at"] = "2026-09-01T18:30:00"
        bericht = self.importiere(ohne_zone)
        self.assertEqual(bericht.ungueltig, 1)
        self.assertEqual(Match.objects.count(), 0)

    def test_nicht_lesbare_datei(self):
        self.schreibe("{kein json", name="kaputt.json")
        bericht = MatchImporter(FixtureDataProvider(self.verzeichnis)).ausfuehren()
        self.assertEqual(bericht.fehlerhaft, 1)

    def test_synthetische_herkunft_wird_zur_quelle(self):
        self.importiere(partie(), herkunft="synthetisch")
        self.importiere(partie(minuten=10), herkunft="api-mitschnitt")
        quellen = set(Match.objects.values_list("source", flat=True))
        self.assertEqual(quellen, {Datenquelle.SYNTHETIC, Datenquelle.FIXTURE})

    def test_format_ohne_parser_wird_gespeichert_aber_nicht_ausgewertet(self):
        # Spieler-Mitschnitte enthalten keine Partien und haben keinen Parser.
        inhalt = {
            "format": FORMAT_OFFIZIELLER_SPIELER, "herkunft": "api-mitschnitt",
            "antwort": {"hinweis": "Platzhalter - keine echte API-Antwort"},
        }
        bericht = MatchImporter(FixtureDataProvider(self.schreibe(inhalt))).ausfuehren()
        self.assertEqual(bericht.nicht_unterstuetzt, 1)
        self.assertEqual(Match.objects.count(), 0)
        payload = RawPayload.objects.get()
        self.assertEqual(payload.parse_status, RawPayload.ParseStatus.UNSUPPORTED)
        self.assertEqual(payload.payload["antwort"]["hinweis"], inhalt["antwort"]["hinweis"])

    def test_leeres_verzeichnis_meldet_sich_als_nicht_verfuegbar(self):
        status = FixtureDataProvider(self.verzeichnis).status()
        self.assertFalse(status.verfuegbar)


class BeispieldateiTest(DrafterTest):
    def test_synthetische_beispieldatei(self):
        pfad = Path(settings.BASE_DIR) / "drafter" / "testdaten" / "synthetisch_ranked.json"
        bericht = MatchImporter(FixtureDataProvider(pfad)).ausfuehren()
        self.assertEqual(bericht.matches_gelesen, 8)
        self.assertEqual(bericht.neu, 6)
        self.assertEqual(bericht.duplikate, 2)
        self.assertEqual(bericht.konflikte, 1)
        self.assertEqual(bericht.unbekannte_brawler, {"Kit"})
        self.assertEqual(bericht.unbekannte_maps, {"Unbekannte Testmap"})
        self.assertTrue(all(m.source == Datenquelle.SYNTHETIC for m in Match.objects.all()))


class _FakeClient:
    """Ersatz fuer den API-Client - ohne Netz, ohne erfundene Antwortfelder."""

    def __init__(self, mit_key):
        self.einsatzbereit = mit_key
        self.aufrufe = []

    def battlelog(self, tag):
        if not self.einsatzbereit:
            raise AssertionError("Ohne Key darf nichts abgerufen werden")
        self.aufrufe.append(tag)
        return {"hinweis": "Platzhalter - keine echte API-Antwort"}

    def abrufen(self, pfad, **parameter):
        from drafter.services.brawl_api_client import ApiAntwort
        if not self.einsatzbereit:
            raise AssertionError("Ohne Key darf nichts abgerufen werden")
        self.aufrufe.append(pfad)
        return ApiAntwort(
            pfad=f"/{pfad}", status=200, header={"content-type": "application/json"},
            daten={"hinweis": "Platzhalter - keine echte API-Antwort"},
        )


class OffiziellerApiProviderTest(FixtureMixin, DrafterTest):
    @override_settings(BRAWL_STARS_API_KEY="")
    def test_ohne_key_nicht_verfuegbar_und_kein_absturz(self):
        provider = OfficialBrawlAPIProvider(spieler_tags=["#SYNTH01"])
        status = provider.status()
        self.assertFalse(status.verfuegbar)
        self.assertIn("BRAWL_STARS_API_KEY", status.grund)
        self.assertEqual(list(provider.lieferungen()), [])

    def test_ohne_key_ruft_der_import_nichts_ab(self):
        client = _FakeClient(mit_key=False)
        bericht = MatchImporter(
            OfficialBrawlAPIProvider(client=client, spieler_tags=["#SYNTH01"])
        ).ausfuehren()
        self.assertEqual(bericht.lieferungen, 0)
        self.assertEqual(client.aufrufe, [])

    def test_mit_key_wird_roh_gespeichert_aber_nichts_erfunden(self):
        client = _FakeClient(mit_key=True)
        provider = OfficialBrawlAPIProvider(client=client, spieler_tags=["#SYNTH01"])
        self.assertTrue(provider.status().verfuegbar)

        # Die Platzhalter-Antwort hat keine Liste 'items' - sie ist kein
        # Battlelog. Gespeichert wird sie trotzdem, ausgewertet nicht.
        bericht = MatchImporter(provider).ausfuehren()
        self.assertEqual(bericht.fehlerhaft, 1)
        self.assertEqual(Match.objects.count(), 0)
        payload = RawPayload.objects.get()
        self.assertEqual(payload.source, Datenquelle.API)
        self.assertEqual(payload.parse_status, RawPayload.ParseStatus.ERROR)
        self.assertEqual(payload.payload["antwort"], {"hinweis": "Platzhalter - keine echte API-Antwort"})

    def test_mitschnitt_laeuft_danach_ohne_netz_ueber_fixtures(self):
        provider = OfficialBrawlAPIProvider(client=_FakeClient(mit_key=True))
        pfad = provider.rohantwort_sichern("#SYNTH01", self.verzeichnis)
        inhalt = json.loads(pfad.read_text(encoding="utf-8"))
        self.assertEqual(set(inhalt), {
            "format", "herkunft", "referenz", "endpoint", "http_status",
            "antwort_header", "abgerufen_am", "antwort",
        })
        self.assertEqual(inhalt["http_status"], 200)
        self.assertNotIn("authorization", pfad.read_text(encoding="utf-8").lower())

        bericht = MatchImporter(FixtureDataProvider(pfad)).ausfuehren()
        self.assertEqual(bericht.fehlerhaft, 1, "Platzhalter ohne 'items' ist kein Battlelog")

    def test_mitschnitt_ohne_key_scheitert_laut(self):
        from drafter.services.brawl_api_client import KeinKeyFehler
        with self.assertRaises(KeinKeyFehler):
            OfficialBrawlAPIProvider(client=_FakeClient(mit_key=False)).rohantwort_sichern(
                "#SYNTH01", self.verzeichnis
            )


def _basis_datum(tage):
    from drafter.tests.fixture_helfer import BASIS
    from datetime import timedelta
    return (BASIS + timedelta(days=tage)).date()


def _basis_zeit(tage):
    from drafter.tests.fixture_helfer import BASIS
    from datetime import timedelta
    return BASIS + timedelta(days=tage)


class _Stumm:
    def write(self, *args, **kwargs):
        pass

    def flush(self):
        pass
