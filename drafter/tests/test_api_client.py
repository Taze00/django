# -*- coding: utf-8 -*-
"""Der API-Client - ohne Netz, mit einem ersetzten urlopen.

Kein Test hier stellt eine echte Verbindung her. Der "Oeffner" wird
ersetzt und liefert vorgefertigte Antworten oder HTTP-Fehler.
"""

import io
import json
import logging
import socket
import urllib.error
from email.message import Message

from django.test import SimpleTestCase, override_settings

from drafter.services.brawl_api_client import (
    ApiFehler, BrawlApiClient, KeinKeyFehler, NetzwerkFehler, NichtGefundenFehler,
    RatenlimitFehler, ServerFehler, UngueltigerKeyFehler, ZugriffVerweigertFehler,
)

# Ein ausgedachter Wert. Er muss nur eindeutig genug sein, um in Texten
# gefunden zu werden, wenn er dort faelschlich auftaucht.
TEST_KEY = "TEST-KEY-nicht-echt-7f3a9c"


class _Antwort:
    def __init__(self, daten, status=200, header=None):
        self._koerper = json.dumps(daten).encode("utf-8")
        self.status = status
        self.headers = Message()
        for name, wert in (header or {}).items():
            self.headers[name] = wert

    def read(self):
        return self._koerper

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _Oeffner:
    """Ersatz fuer urlopen: merkt sich die Anfrage, liefert das Vorgegebene."""

    def __init__(self, ergebnis):
        self.ergebnis = ergebnis
        self.anfragen = []

    def __call__(self, anfrage, timeout=None):
        self.anfragen.append(anfrage)
        if isinstance(self.ergebnis, Exception):
            raise self.ergebnis
        return self.ergebnis


def _http_fehler(status, koerper):
    return urllib.error.HTTPError(
        "https://api.brawlstars.com/v1/players/%23X", status, "Fehler", Message(),
        io.BytesIO(json.dumps(koerper).encode("utf-8")),
    )


class OhneKeyTest(SimpleTestCase):
    @override_settings(BRAWL_STARS_API_KEY="")
    def test_ohne_key_kein_abruf_und_klare_meldung(self):
        oeffner = _Oeffner(_Antwort({}))
        client = BrawlApiClient(oeffner=oeffner)
        self.assertFalse(client.einsatzbereit)
        with self.assertRaises(KeinKeyFehler) as fehler:
            client.abrufen("brawlers")
        self.assertIn("BRAWL_STARS_API_KEY", str(fehler.exception))
        self.assertEqual(oeffner.anfragen, [], "Ohne Key darf keine Anfrage rausgehen")

    @override_settings(BRAWL_STARS_API_KEY=TEST_KEY)
    def test_key_kommt_aus_den_settings(self):
        oeffner = _Oeffner(_Antwort({"items": []}))
        BrawlApiClient(oeffner=oeffner).abrufen("brawlers")
        self.assertEqual(oeffner.anfragen[0].get_header("Authorization"), f"Bearer {TEST_KEY}")


class AntwortTest(SimpleTestCase):
    def test_status_header_und_json_werden_geliefert(self):
        oeffner = _Oeffner(_Antwort({"items": [1]}, header={
            "Content-Type": "application/json", "Set-Cookie": "sitzung=abc", "X-Beispiel": "1",
        }))
        antwort = BrawlApiClient(api_key=TEST_KEY, oeffner=oeffner).abrufen("brawlers")
        self.assertEqual(antwort.status, 200)
        self.assertEqual(antwort.daten, {"items": [1]})
        self.assertEqual(antwort.pfad, "/brawlers")
        self.assertIn("x-beispiel", antwort.header)
        self.assertNotIn("set-cookie", antwort.header)

    def test_antwort_enthaelt_den_key_nirgends(self):
        oeffner = _Oeffner(_Antwort({"ok": True}, header={"Server": "x"}))
        antwort = BrawlApiClient(api_key=TEST_KEY, oeffner=oeffner).abrufen("brawlers")
        text = json.dumps({"pfad": antwort.pfad, "header": antwort.header, "daten": antwort.daten})
        self.assertNotIn(TEST_KEY, text)
        self.assertNotIn("authorization", text.lower())


class FehlercodeTest(SimpleTestCase):
    FAELLE = (
        (401, UngueltigerKeyFehler, "Key"),
        (403, ZugriffVerweigertFehler, "IP"),
        (404, NichtGefundenFehler, "Tag"),
        (429, RatenlimitFehler, "Ratenlimit"),
        (500, ServerFehler, "API"),
        (503, ServerFehler, "API"),
    )

    def test_jeder_status_hat_seinen_fehlertyp_und_eine_hilfreiche_meldung(self):
        for status, typ, stichwort in self.FAELLE:
            with self.subTest(status=status):
                client = BrawlApiClient(
                    api_key=TEST_KEY,
                    oeffner=_Oeffner(_http_fehler(status, {"reason": "beispielGrund"})),
                )
                with self.assertRaises(typ) as fehler:
                    client.abrufen("players/%23X")
                self.assertEqual(fehler.exception.status, status)
                self.assertEqual(fehler.exception.grund, "beispielGrund")
                self.assertIn(stichwort, str(fehler.exception))

    def test_meldung_der_api_wird_mitgegeben_aber_vom_key_bereinigt(self):
        # Selbst wenn eine Fehlerantwort den Key zurueckspiegeln wuerde:
        koerper = {"reason": "accessDenied", "message": f"Key {TEST_KEY} nicht erlaubt fuer IP 203.0.113.9"}
        client = BrawlApiClient(api_key=TEST_KEY, oeffner=_Oeffner(_http_fehler(403, koerper)))
        with self.assertRaises(ZugriffVerweigertFehler) as fehler:
            client.abrufen("brawlers")
        meldung = str(fehler.exception)
        self.assertNotIn(TEST_KEY, meldung)
        self.assertIn("203.0.113.9", meldung)
        self.assertIn("accessDenied", meldung)

    def test_fehler_ohne_json_koerper(self):
        fehler = urllib.error.HTTPError("u", 502, "Bad Gateway", Message(), io.BytesIO(b"<html>"))
        client = BrawlApiClient(api_key=TEST_KEY, oeffner=_Oeffner(fehler))
        with self.assertRaises(ServerFehler) as f:
            client.abrufen("brawlers")
        self.assertIsNone(f.exception.grund)

    def test_fehler_haben_keine_ausnahmekette(self):
        """Kein __cause__/__context__, das die urllib-Anfrage mitschleppen koennte."""
        client = BrawlApiClient(api_key=TEST_KEY, oeffner=_Oeffner(_http_fehler(401, {})))
        with self.assertRaises(ApiFehler) as fehler:
            client.abrufen("brawlers")
        self.assertIsNone(fehler.exception.__cause__)
        self.assertTrue(fehler.exception.__suppress_context__)


class NetzwerkTest(SimpleTestCase):
    def test_zeitueberschreitung(self):
        client = BrawlApiClient(api_key=TEST_KEY, oeffner=_Oeffner(socket.timeout("timed out")))
        with self.assertRaises(NetzwerkFehler) as fehler:
            client.abrufen("brawlers")
        self.assertIn("Zeitüberschreitung", str(fehler.exception))

    def test_zeitueberschreitung_in_urlerror(self):
        client = BrawlApiClient(
            api_key=TEST_KEY, oeffner=_Oeffner(urllib.error.URLError(socket.timeout("timed out")))
        )
        with self.assertRaises(NetzwerkFehler):
            client.abrufen("brawlers")

    def test_dns_oder_verbindungsfehler(self):
        client = BrawlApiClient(
            api_key=TEST_KEY, oeffner=_Oeffner(urllib.error.URLError("Name or service not known"))
        )
        with self.assertRaises(NetzwerkFehler) as fehler:
            client.abrufen("brawlers")
        self.assertIn("Netzwerkfehler", str(fehler.exception))

    def test_antwort_ohne_json(self):
        class Kaputt(_Antwort):
            def read(self):
                return b"<html>Wartung</html>"
        client = BrawlApiClient(api_key=TEST_KEY, oeffner=_Oeffner(Kaputt({})))
        with self.assertRaises(ServerFehler):
            client.abrufen("brawlers")


class GeheimhaltungTest(SimpleTestCase):
    def test_repr_zeigt_den_key_nicht(self):
        client = BrawlApiClient(api_key=TEST_KEY)
        self.assertNotIn(TEST_KEY, repr(client))
        self.assertNotIn(TEST_KEY, str(client))
        self.assertFalse(hasattr(client, "api_key"), "Kein öffentliches Attribut mit dem Key")

    def test_kein_log_eintrag_mit_dem_key(self):
        """Ein kompletter Abruf samt Fehler hinterlaesst den Key in keinem Logger."""
        with self.assertLogs(level=logging.DEBUG) as protokoll:
            logging.getLogger("drafter.test").debug("Protokoll-Anker")
            for ergebnis in (_Antwort({"ok": 1}), _http_fehler(403, {"reason": "x"})):
                try:
                    BrawlApiClient(api_key=TEST_KEY, oeffner=_Oeffner(ergebnis)).abrufen("brawlers")
                except ApiFehler as fehler:
                    logging.getLogger("drafter.test").error("Abruf fehlgeschlagen: %s", fehler)
        self.assertFalse(any(TEST_KEY in zeile for zeile in protokoll.output))
