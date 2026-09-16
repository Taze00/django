# -*- coding: utf-8 -*-
"""Wiederholen und Warten - ohne Netz und ohne echte Pause.

Der Ersatz-Oeffner liefert eine FOLGE von Ergebnissen: erst der Fehler,
dann die Antwort. So laesst sich pruefen, dass wiederholt wird, wie lange
gewartet wird und welche Fehler gar nicht erst wiederholt werden.
"""

import io
import json
import socket
import urllib.error
from email.message import Message
from unittest import mock

from django.test import SimpleTestCase

from drafter import config
from drafter.services.brawl_api_client import (
    BrawlApiClient, NetzwerkFehler, NichtGefundenFehler, RatenlimitFehler, ServerFehler,
    UngueltigerKeyFehler, ZugriffVerweigertFehler,
)
from drafter.tests.test_api_client import TEST_KEY, _Antwort


def _http_fehler(status, header=None, koerper=None):
    kopf = Message()
    for name, wert in (header or {}).items():
        kopf[name] = wert
    return urllib.error.HTTPError(
        "https://api.brawlstars.com/v1/brawlers", status, "Fehler", kopf,
        io.BytesIO(json.dumps(koerper or {"reason": "beispielGrund"}).encode("utf-8")),
    )


class _Folge:
    """Ersatz fuer urlopen: gibt der Reihe nach zurueck, was vorgegeben ist."""

    def __init__(self, *ergebnisse):
        self.ergebnisse = list(ergebnisse)
        self.anfragen = []

    def __call__(self, anfrage, timeout=None):
        self.anfragen.append(anfrage)
        ergebnis = self.ergebnisse.pop(0)
        if isinstance(ergebnis, Exception):
            raise ergebnis
        return ergebnis


class WiederholungTest(SimpleTestCase):
    def ersatz_client(self, *ergebnisse, **optionen):
        self.pausen = []
        self.folge = _Folge(*ergebnisse)
        return BrawlApiClient(
            api_key=TEST_KEY, oeffner=self.folge, schlafen=self.pausen.append,
            mindestabstand=0, **optionen,
        )

    def test_429_wird_wiederholt_und_wartet_wie_angesagt(self):
        client = self.ersatz_client(_http_fehler(429, {"Retry-After": "3"}), _Antwort({"items": []}))
        antwort = client.abrufen("brawlers")
        self.assertEqual(antwort.status, 200)
        self.assertEqual(len(self.folge.anfragen), 2)
        self.assertEqual(self.pausen, [3.0])
        self.assertEqual(client.statistik.wiederholungen, 1)
        self.assertEqual(client.statistik.retry_after, [3])
        self.assertIn("retry-after", client.statistik.ratenlimit_header)

    def test_retry_after_wird_gedeckelt(self):
        with mock.patch.object(config, "API_RETRY_AFTER_MAX_SEKUNDEN", 10.0):
            client = self.ersatz_client(_http_fehler(429, {"Retry-After": "600"}), _Antwort({"ok": 1}))
            client.abrufen("brawlers")
        self.assertEqual(self.pausen, [10.0])

    def test_serverfehler_warten_exponentiell(self):
        client = self.ersatz_client(_http_fehler(503), _http_fehler(503), _Antwort({"ok": 1}))
        client.abrufen("brawlers")
        basis = config.API_BACKOFF_BASIS_SEKUNDEN
        self.assertEqual(self.pausen, [basis, basis * 2])
        self.assertEqual(client.statistik.status[503], 2)

    def test_zeitueberschreitung_wird_wiederholt(self):
        client = self.ersatz_client(socket.timeout("timed out"), _Antwort({"ok": 1}))
        self.assertEqual(client.abrufen("brawlers").status, 200)
        self.assertEqual(len(self.pausen), 1)
        self.assertEqual(client.statistik.status["zeitueberschreitung"], 1)

    def test_netzwerkfehler_wird_wiederholt_und_am_ende_gemeldet(self):
        client = self.ersatz_client(*[urllib.error.URLError("kein DNS")] * 4, versuche=4)
        with self.assertRaises(NetzwerkFehler):
            client.abrufen("brawlers")
        self.assertEqual(len(self.folge.anfragen), 4)
        self.assertEqual(len(self.pausen), 3)

    def test_nach_allen_versuchen_kommt_der_fehler(self):
        client = self.ersatz_client(*[_http_fehler(500)] * 4, versuche=4)
        with self.assertRaises(ServerFehler):
            client.abrufen("brawlers")
        self.assertEqual(len(self.folge.anfragen), 4)
        self.assertEqual(len(self.pausen), 3)
        self.assertEqual(client.statistik.anfragen, 4)

    def test_key_ip_und_tag_werden_nie_wiederholt(self):
        """401, 403 und 404 aendern sich beim zweiten Versuch nicht."""
        for status, typ in ((401, UngueltigerKeyFehler), (403, ZugriffVerweigertFehler),
                            (404, NichtGefundenFehler)):
            with self.subTest(status=status):
                client = self.ersatz_client(_http_fehler(status), _Antwort({"ok": 1}))
                with self.assertRaises(typ):
                    client.abrufen("brawlers")
                self.assertEqual(len(self.folge.anfragen), 1)
                self.assertEqual(self.pausen, [])

    def test_versuche_eins_heisst_kein_wiederholen(self):
        client = self.ersatz_client(_http_fehler(503), versuche=1)
        with self.assertRaises(ServerFehler):
            client.abrufen("brawlers")
        self.assertEqual(len(self.folge.anfragen), 1)

    def test_ratenlimit_traegt_retry_after_in_meldung_und_feld(self):
        client = self.ersatz_client(_http_fehler(429, {"Retry-After": "7"}), versuche=1)
        with self.assertRaises(RatenlimitFehler) as fehler:
            client.abrufen("brawlers")
        self.assertEqual(fehler.exception.retry_after, 7)
        self.assertIn("Retry-After: 7", str(fehler.exception))
        self.assertNotIn(TEST_KEY, str(fehler.exception))

    def test_ohne_rate_limit_header_bleibt_die_statistik_leer(self):
        client = self.ersatz_client(_Antwort({"ok": 1}, header={"Cache-Control": "max-age=3"}))
        client.abrufen("brawlers")
        self.assertEqual(client.statistik.ratenlimit_header, set())
        self.assertEqual(client.statistik.wiederholungen, 0)
