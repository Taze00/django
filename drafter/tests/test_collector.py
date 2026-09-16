# -*- coding: utf-8 -*-
"""Der Collector - ohne Netz, mit einem Ersatz-Client.

Die Antworten stammen aus dem anonymisierten Battlelog-Fixture: echte
Struktur, echte IDs, erfundene Spieler. Geprueft wird vor allem, was der
Collector NICHT tut - tiefer graben als erlaubt, mehr abrufen als das
Budget, denselben Spieler doppelt holen, nach 403 weitermachen.
"""

import copy
import json
from datetime import datetime, timedelta, timezone as dt_timezone

from drafter.models import Brawler, Datenquelle
from drafter.models.collector import CollectorRun, TrackedPlayer
from drafter.models.matches import Match, RawPayload
from drafter.services.brawl_api_client import (
    PFAD_BRAWLER, AbrufStatistik, ApiAntwort, KeinKeyFehler, NichtGefundenFehler,
    RatenlimitFehler, ServerFehler, ZugriffVerweigertFehler, pfad_battlelog,
    pfad_rangliste_spieler,
)
from drafter.services.collector import Collector
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import katalog_aus_battlelog
from drafter.tests.test_offizieller_battlelog import lade, team_eintraege

JETZT = datetime(2026, 9, 16, 12, 0, tzinfo=dt_timezone.utc)
SAAT = "#TEST0001"


class ErsatzClient:
    """Gibt vorgegebene Antworten zurueck und merkt sich die Pfade."""

    def __init__(self, antworten, standard=None, einsatzbereit=True):
        self.antworten = dict(antworten)
        self.standard = standard
        self.einsatzbereit = einsatzbereit
        self.versuche = 4
        self.statistik = AbrufStatistik()
        self.aufrufe = []

    def abrufen(self, pfad, **parameter):
        self.aufrufe.append(pfad)
        self.statistik.anfragen += 1
        ergebnis = self.antworten.get(pfad, self.standard)
        if isinstance(ergebnis, Exception):
            self.statistik.status[getattr(ergebnis, "status", "fehler")] += 1
            raise ergebnis
        if ergebnis is None:
            self.statistik.status[404] += 1
            raise NichtGefundenFehler(f"404 bei /{pfad}: nicht gefunden.", status=404)
        self.statistik.status[200] += 1
        return ApiAntwort(pfad=f"/{pfad}", status=200,
                          header={"cache-control": "max-age=3"}, daten=ergebnis)

    @property
    def battlelog_aufrufe(self):
        return [p for p in self.aufrufe if p.endswith("/battlelog")]


class CollectorTest(DrafterTest):
    def setUp(self):
        super().setUp()
        self.daten = lade()
        self.battlelog = self.daten["antwort"]
        self.katalog = {"items": katalog_aus_battlelog(self.daten)}

    # --- Werkzeuge ------------------------------------------------------
    # `ersatz_client`, nicht `client`: `self.client` ist der Django-Testclient.
    def rangliste(self, *tags):
        return {
            "items": [
                {"tag": tag, "name": f"Spieler {i}", "rank": i, "trophies": 300000 - i}
                for i, tag in enumerate(tags, 1)
            ],
            "paging": {"cursors": {}},
        }

    def ersatz_client(self, battlelogs=None, standard=None, tags=(SAAT,), **extra):
        antworten = {
            PFAD_BRAWLER: self.katalog,
            pfad_rangliste_spieler("global"): self.rangliste(*tags),
            pfad_battlelog(SAAT): self.battlelog,
        }
        antworten.update(battlelogs or {})
        antworten.update(extra)
        return ErsatzClient(antworten, standard=standard)

    def sammle(self, client, **optionen):
        optionen.setdefault("jetzt", lambda: JETZT)
        return Collector(client=client, **optionen).ausfuehren()

    def tags_aus(self, typ):
        tags = set()
        for eintrag in team_eintraege(self.daten):
            if eintrag["battle"]["type"] != typ:
                continue
            tags |= {s["tag"] for team in eintrag["battle"]["teams"] for s in team}
        return tags - {SAAT}

    def ohne_ergebnis(self):
        """Derselbe Battlelog ohne `result` - aus fremder Sicht ist es unbekannt."""
        kopie = copy.deepcopy(self.battlelog)
        for eintrag in kopie["items"]:
            eintrag["battle"].pop("result", None)
        return kopie

    # --- Der gute Fall --------------------------------------------------
    def test_saat_wird_abgefragt_und_importiert(self):
        client = self.ersatz_client()
        bericht = self.sammle(client, max_spieler=1)

        self.assertEqual(bericht.abbruch, "")
        self.assertEqual(client.battlelog_aufrufe, [pfad_battlelog(SAAT)])
        self.assertEqual(bericht.neu, 17)
        self.assertEqual(bericht.neu_nach_typ["soloRanked"], 4)
        self.assertEqual(bericht.neu_nach_typ["ranked"], 13)
        self.assertEqual(bericht.uebersprungen, 8)
        self.assertEqual(bericht.ungueltig, 0)
        self.assertEqual(bericht.id_widersprueche, [])
        self.assertEqual(Match.objects.filter(source=Datenquelle.API).count(), 17)

        saat = TrackedPlayer.objects.get(tag=SAAT)
        self.assertEqual(saat.last_fetched_at, JETZT)
        self.assertEqual(saat.fetch_count, 1)
        self.assertEqual(saat.last_status, "200")
        self.assertEqual(saat.last_battle_count, 25)
        self.assertEqual(saat.last_solo_ranked_count, 4)
        self.assertEqual(saat.origin, TrackedPlayer.Origin.RANKING)
        self.assertEqual(saat.ranking_position, 1)

    def test_entdeckt_nur_aus_soloranked(self):
        self.sammle(self.ersatz_client(), max_spieler=1)
        entdeckt = set(TrackedPlayer.objects.filter(
            origin=TrackedPlayer.Origin.DISCOVERED).values_list("tag", flat=True))
        self.assertEqual(entdeckt, self.tags_aus("soloRanked"))

        nur_trophaeen = self.tags_aus("ranked") - self.tags_aus("soloRanked")
        self.assertTrue(nur_trophaeen, "Das Fixture enthält reine Trophäen-Mitspieler")
        self.assertEqual(TrackedPlayer.objects.filter(tag__in=nur_trophaeen).count(), 0)
        for spieler in TrackedPlayer.objects.filter(origin=TrackedPlayer.Origin.DISCOVERED):
            self.assertEqual(spieler.depth, 1)
            self.assertEqual(spieler.discovered_from, SAAT)

    def test_keine_rekursion_ueber_die_tiefengrenze(self):
        client = self.ersatz_client(standard=self.ohne_ergebnis())
        bericht = self.sammle(client, max_spieler=6, max_tiefe=1)

        self.assertEqual(len(client.battlelog_aufrufe), 6)
        self.assertEqual(TrackedPlayer.objects.filter(depth__gte=2).count(), 0)
        self.assertEqual(Match.objects.count(), 17, "Dieselben Partien, nur andere Sicht")
        self.assertEqual(bericht.neu, 17)
        self.assertEqual(bericht.duplikate, 17 * 5)
        self.assertEqual(bericht.konflikte, 0)

    def test_abstand_verhindert_den_sofortigen_zweitabruf(self):
        erster = self.ersatz_client()
        self.sammle(erster, max_spieler=1)

        zweiter = self.ersatz_client(standard=self.ohne_ergebnis())
        self.sammle(zweiter, max_spieler=1)
        self.assertEqual(len(zweiter.battlelog_aufrufe), 1)
        self.assertNotEqual(zweiter.battlelog_aufrufe, [pfad_battlelog(SAAT)])

        spaeter = self.ersatz_client(standard=self.ohne_ergebnis())
        self.sammle(spaeter, max_spieler=1, jetzt=lambda: JETZT + timedelta(hours=7))
        self.assertEqual(spaeter.battlelog_aufrufe, [pfad_battlelog(SAAT)])

    # --- Fehler ---------------------------------------------------------
    def test_404_markiert_den_spieler_und_der_lauf_geht_weiter(self):
        fehlt = "#TESTFEHLT"
        client = self.ersatz_client(tags=(fehlt, SAAT), battlelogs={pfad_battlelog(fehlt): None})
        bericht = self.sammle(client, max_spieler=2)

        self.assertEqual(bericht.abbruch, "")
        self.assertEqual(bericht.fehler["404"], 1)
        self.assertEqual(bericht.battlelogs_ok, 1)
        spieler = TrackedPlayer.objects.get(tag=fehlt)
        self.assertEqual(spieler.last_status, "404")
        self.assertEqual(spieler.next_fetch_after, JETZT + timedelta(days=7))
        self.assertEqual(spieler.fetch_count, 0)

    def test_403_bricht_den_lauf_ab(self):
        client = self.ersatz_client()
        client.antworten[PFAD_BRAWLER] = ZugriffVerweigertFehler(
            "403 bei /brawlers: Zugriff verweigert.", status=403)
        bericht = self.sammle(client)

        self.assertIn("403", bericht.abbruch)
        self.assertEqual(client.battlelog_aufrufe, [])
        self.assertEqual(CollectorRun.objects.get().status, CollectorRun.Status.ABORTED)

    def test_429_bricht_ab_und_laesst_den_spieler_offen(self):
        client = self.ersatz_client(battlelogs={
            pfad_battlelog(SAAT): RatenlimitFehler("429: Ratenlimit erreicht.", status=429),
        })
        bericht = self.sammle(client, max_spieler=3)

        self.assertIn("Ratenlimit", bericht.abbruch)
        self.assertEqual(bericht.fehler["429"], 1)
        self.assertEqual(len(client.battlelog_aufrufe), 1)
        self.assertIsNone(TrackedPlayer.objects.get(tag=SAAT).last_fetched_at)

    def test_serverfehler_in_folge_beenden_den_lauf(self):
        tags = ("#TESTA01", "#TESTA02", "#TESTA03", "#TESTA04")
        client = self.ersatz_client(tags=tags, standard=ServerFehler("503: Wartung.", status=503))
        client.antworten.pop(pfad_battlelog(SAAT))
        bericht = self.sammle(client, max_spieler=4)

        self.assertIn("in Folge", bericht.abbruch)
        self.assertEqual(len(client.battlelog_aufrufe), 3)
        self.assertEqual(bericht.fehler["503"], 3)
        spieler = TrackedPlayer.objects.get(tag=tags[0])
        self.assertEqual(spieler.error_streak, 1)
        self.assertEqual(spieler.next_fetch_after, JETZT + timedelta(hours=1))
        self.assertIsNone(spieler.last_fetched_at)

    # --- Rohdaten, Katalog, Protokoll -----------------------------------
    def test_rohantworten_werden_gespeichert_ohne_geheimnisse(self):
        self.sammle(self.ersatz_client(), max_spieler=1)
        formate = set(RawPayload.objects.values_list("format", flat=True))
        self.assertEqual(formate, {
            "brawlstars.brawlers.raw", "brawlstars.rankings.raw", "brawlstars.battlelog.raw",
        })
        for payload in RawPayload.objects.all():
            text = json.dumps(payload.payload).lower()
            self.assertNotIn("authorization", text)
            self.assertNotIn("bearer", text)

    def test_unbekannte_brawler_ziehen_den_katalog_nach(self):
        client = self.ersatz_client()
        self.sammle(client, max_spieler=1, katalog=False)
        self.assertEqual(client.aufrufe.count(PFAD_BRAWLER), 1)
        self.assertTrue(Brawler.objects.filter(slug="gale").exclude(external_id=None).exists())

    def test_lauf_wird_protokolliert(self):
        self.sammle(self.ersatz_client(), max_spieler=1)
        lauf = CollectorRun.objects.get()
        self.assertEqual(lauf.status, CollectorRun.Status.FINISHED)
        self.assertEqual(lauf.report["neu"], 17)
        self.assertEqual(lauf.report["neu_nach_typ"]["soloRanked"], 4)
        self.assertEqual(lauf.parameters["max_spieler"], 1)
        self.assertEqual(lauf.parameters["max_tiefe"], 1)
        self.assertIsNotNone(lauf.finished_at)

    # --- Grenzen --------------------------------------------------------
    def test_tiefe_ausserhalb_der_grenze_ist_ein_fehler(self):
        with self.assertRaises(ValueError):
            Collector(client=self.ersatz_client(), max_tiefe=5)

    def test_ohne_key_wird_nichts_abgerufen(self):
        client = ErsatzClient({}, einsatzbereit=False)
        with self.assertRaises(KeinKeyFehler):
            Collector(client=client).ausfuehren()
        self.assertEqual(client.aufrufe, [])
        self.assertEqual(CollectorRun.objects.count(), 0)
