# -*- coding: utf-8 -*-
"""HTTP-Huelle fuer die offizielle Brawl-Stars-API.

Diese Datei kennt KEINE Antwortfelder. Sie ruft Pfade ab und gibt zurueck,
was Supercell schickt - Status, Antwort-Header und JSON. Was davon
brauchbar ist, entscheidet der Parser, und der entsteht erst anhand
echter, gespeicherter Antworten.

Der API-Key - drei Regeln, die hier technisch durchgesetzt werden:

1. **Nur aus der Umgebung.** `BRAWL_STARS_API_KEY` -> settings ->
   `config.api_key()`. Nie aus dem Repository, nie aus einem Argument
   eines Management-Commands.
2. **Nur im Anfrage-Header.** Er steht ausschliesslich im
   `Authorization`-Header der ausgehenden Anfrage. Gespeichert werden nur
   ANTWORT-Header - die enthalten ihn nicht.
3. **Nie in Text.** Der Key liegt privat am Client (`_api_key`), `repr()`
   zeigt ihn nicht, Fehlermeldungen laufen durch `_ohne_geheimnis()`, und
   Fehler werden ohne Ausnahme-Kette geworfen (`from None`), damit kein
   Traceback ein Objekt mit dem Header mitschleppt.

IP-Bindung: Supercell bindet jeden Key an die IP-Adressen, die beim
Anlegen eingetragen wurden. Ein Key, der vom Laptop funktioniert, ergibt
auf dem Server 403 - und umgekehrt. Aendert sich die oeffentliche IP des
Servers (DynDNS), ebenfalls 403.

Wiederholen: 429, 5xx und Zeitueberschreitungen sind voruebergehend und
werden bis zu `config.API_VERSUCHE`-mal versucht - mit exponentieller
Pause, bei 429 mit `Retry-After`, falls die Antwort den Header traegt
(beobachtet wurde er bisher nicht). 401, 403 und 404 werden nie
wiederholt: ein zweiter Versuch aendert an Key, IP-Freigabe oder Tag nichts.

Belegte Pfade (echte 200-Antworten vom 2026-09-15): /brawlers,
/players/{tag}, /players/{tag}/battlelog, /rankings/global/players,
/rankings/global/brawlers/{id}, /rankings/global/clubs, /events/rotation.
/rankings/global/powerplay/seasons antwortete 404. Eine Ranked-Rangliste
nach Elo ist nicht darunter - die Ranglisten sind Trophaeenlisten.
"""

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from drafter import config

BASIS_URL = "https://api.brawlstars.com/v1"
ZEITLIMIT_SEKUNDEN = 12

# Antwort-Header, die nicht gespeichert werden. Alle anderen bleiben
# erhalten - darunter moeglicherweise Hinweise auf Ratenbegrenzung.
NICHT_SPEICHERN = frozenset({"set-cookie"})

# Namensbestandteile von Headern, die auf eine Ratenbegrenzung hindeuten
# KOENNTEN. Die Statistik haelt fest, ob je einer auftaucht - bis zum
# 2026-09-15 kam keiner vor.
RATENLIMIT_HINWEISE = ("ratelimit", "rate-limit", "retry-after")

PFAD_BRAWLER = "brawlers"
PFAD_EVENT_ROTATION = "events/rotation"


# =========================================================================
# Fehler
# =========================================================================

class ApiFehler(RuntimeError):
    """Oberklasse. Traegt HTTP-Status und Supercells `reason`, falls vorhanden."""

    def __init__(self, meldung, status=None, grund=None):
        super().__init__(meldung)
        self.status = status
        self.grund = grund


class KeinKeyFehler(ApiFehler):
    """Kein API-Key konfiguriert - es wurde nichts abgerufen."""


class UngueltigerKeyFehler(ApiFehler):
    """401 - Key fehlt in der Anfrage oder wird nicht akzeptiert."""


class ZugriffVerweigertFehler(ApiFehler):
    """403 - meist: Key nicht fuer die IP dieses Servers freigegeben."""


class NichtGefundenFehler(ApiFehler):
    """404 - z.B. ungueltiger Spieler-Tag."""


class RatenlimitFehler(ApiFehler):
    """429 - zu viele Anfragen. `retry_after` in Sekunden, falls genannt."""

    def __init__(self, meldung, status=None, grund=None, retry_after=None):
        super().__init__(meldung, status, grund)
        self.retry_after = retry_after


class ServerFehler(ApiFehler):
    """5xx - Fehler oder Wartung auf Seiten der API."""


class NetzwerkFehler(ApiFehler):
    """Zeitueberschreitung, DNS, Verbindungsabbruch - keine HTTP-Antwort."""


# Voruebergehend - ein spaeterer Versuch kann gelingen.
WIEDERHOLBAR = (RatenlimitFehler, ServerFehler, NetzwerkFehler)


# =========================================================================
# Antwort und Statistik
# =========================================================================

@dataclass(frozen=True)
class ApiAntwort:
    """Eine erfolgreiche Antwort - vollstaendig, nichts interpretiert."""

    pfad: str
    status: int
    header: dict
    daten: object
    abgerufen_am: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AbrufStatistik:
    """Was ein Client erlebt hat - Grundlage der Fehler- und Ratenlimit-Berichte.

    `anfragen` zaehlt jeden HTTP-Versuch, auch wiederholte. Enthaelt weder
    Pfade mit Spieler-Tags noch den Key.
    """

    anfragen: int = 0
    status: Counter = field(default_factory=Counter)
    wiederholungen: int = 0
    wartezeit_sekunden: float = 0.0
    retry_after: list = field(default_factory=list)
    ratenlimit_header: set = field(default_factory=set)

    def als_dict(self):
        return {
            "anfragen": self.anfragen,
            "status": {str(k): v for k, v in sorted(self.status.items(), key=lambda p: str(p[0]))},
            "wiederholungen": self.wiederholungen,
            "wartezeit_sekunden": round(self.wartezeit_sekunden, 2),
            "retry_after": list(self.retry_after),
            "ratenlimit_header": sorted(self.ratenlimit_header),
        }


# =========================================================================
# Tags und Pfade
# =========================================================================

def tag_bereinigen(tag):
    """'#2abc ' / '2ABC' -> '#2ABC' - die Form, in der Tags gespeichert werden."""
    sauber = str(tag or "").strip().upper().lstrip("#")
    if not sauber:
        raise ApiFehler("Leerer Tag")
    return f"#{sauber}"


def tag_normalisieren(tag):
    """'#2ABC' / '2abc' -> '%232ABC'.

    Spieler- und Clubtags beginnen im Spiel mit '#'. In der URL muss das
    Zeichen kodiert werden, sonst endet der Pfad dort.
    """
    return urllib.parse.quote(tag_bereinigen(tag), safe="")


def land_pruefen(land):
    """'global' oder ein zweistelliger Laendercode. Belegt ist bisher nur 'global'."""
    text = str(land or "").strip()
    if text.lower() == "global":
        return "global"
    if len(text) == 2 and text.isalpha():
        return text.upper()
    raise ApiFehler(
        f"Ungültiger Ranglistenbereich {land!r}: 'global' oder zweistelliger Ländercode"
    )


def pfad_spieler(tag):
    return f"players/{tag_normalisieren(tag)}"


def pfad_battlelog(tag):
    return f"players/{tag_normalisieren(tag)}/battlelog"


def pfad_rangliste_spieler(land="global"):
    return f"rankings/{land_pruefen(land)}/players"


def pfad_rangliste_brawler(brawler_id, land="global"):
    return f"rankings/{land_pruefen(land)}/brawlers/{int(brawler_id)}"


def _fehlertext_der_api(koerper):
    """(reason, message) aus einer Fehlerantwort - nur wenn es JSON ist.

    Es werden keine Felder vorausgesetzt: fehlt eines, bleibt es None.
    """
    try:
        daten = json.loads(koerper)
    except (ValueError, TypeError):
        return None, None
    if not isinstance(daten, dict):
        return None, None
    grund = daten.get("reason")
    nachricht = daten.get("message")
    return (grund if isinstance(grund, str) else None,
            nachricht if isinstance(nachricht, str) else None)


def _retry_after(header):
    """Retry-After in Sekunden - nur die Sekundenform, ein Datum wird ignoriert."""
    wert = str((header or {}).get("retry-after", "")).strip()
    return int(wert) if wert.isdigit() else None


class BrawlApiClient:
    """Duenne Huelle um die HTTP-Ebene. Kennt Pfade, keine Felder."""

    def __init__(self, api_key=None, basis_url=BASIS_URL, oeffner=None,
                 versuche=None, schlafen=None, mindestabstand=None):
        # Privat - siehe Modulkommentar. `oeffner` ersetzt urlopen und
        # `schlafen` time.sleep in Tests: kein Test braucht Netz, keiner wartet.
        self._api_key = (api_key if api_key is not None else config.api_key()) or ""
        self.basis_url = basis_url.rstrip("/")
        self._oeffner = oeffner or urllib.request.urlopen
        self._schlafen = schlafen or time.sleep
        self.versuche = max(1, int(config.API_VERSUCHE if versuche is None else versuche))
        self.mindestabstand = (
            config.API_MINDESTABSTAND_SEKUNDEN if mindestabstand is None else mindestabstand
        )
        self._letzte_anfrage = 0.0
        self.statistik = AbrufStatistik()

    def __repr__(self):
        return f"<BrawlApiClient einsatzbereit={self.einsatzbereit}>"

    @property
    def einsatzbereit(self):
        """Gibt es ueberhaupt einen Key? Ohne ihn laeuft der Drafter weiter."""
        return bool(self._api_key)

    def _ohne_geheimnis(self, text):
        """Den Key aus einem Text entfernen - falls er je darin landet."""
        text = str(text or "")
        if self._api_key:
            text = text.replace(self._api_key, "<entfernt>")
        return text[:500]

    # --- HTTP -----------------------------------------------------------
    def abrufen(self, pfad, **parameter):
        """GET gegen die API, mit Wiederholungen. ApiAntwort oder ApiFehler."""
        if not self.einsatzbereit:
            raise KeinKeyFehler(
                "BRAWL_STARS_API_KEY ist nicht gesetzt. Der Key gehört in die gitignorte "
                ".env und wird über docker-compose.yml durchgereicht - es wurde nichts abgerufen."
            )

        versuch = 1
        while True:
            try:
                return self._einmal(pfad, parameter)
            except WIEDERHOLBAR as fehler:
                if versuch >= self.versuche:
                    raise
                pause = self._pause(fehler, versuch)
            self.statistik.wiederholungen += 1
            self.statistik.wartezeit_sekunden += pause
            self._schlafen(pause)
            versuch += 1

    def _pause(self, fehler, versuch):
        """Wartezeit vor dem naechsten Versuch.

        Nennt die Antwort ein Retry-After, gilt dieses (gedeckelt). Sonst
        exponentiell: Basis, doppelt, vierfach ... bis zur Obergrenze.
        """
        retry_after = getattr(fehler, "retry_after", None)
        if retry_after is not None:
            self.statistik.retry_after.append(retry_after)
            return float(min(max(retry_after, config.API_BACKOFF_BASIS_SEKUNDEN),
                             config.API_RETRY_AFTER_MAX_SEKUNDEN))
        return float(min(config.API_BACKOFF_BASIS_SEKUNDEN * 2 ** (versuch - 1),
                         config.API_BACKOFF_MAX_SEKUNDEN))

    def _header_beobachten(self, header):
        for name in header:
            if any(hinweis in name for hinweis in RATENLIMIT_HINWEISE):
                self.statistik.ratenlimit_header.add(name)

    def _einmal(self, pfad, parameter):
        self._warten()
        pfad = pfad.lstrip("/")
        abfrage = f"?{urllib.parse.urlencode(parameter)}" if parameter else ""
        anfrage = urllib.request.Request(f"{self.basis_url}/{pfad}{abfrage}", headers={
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        })
        anzeige = f"/{pfad}{abfrage}"
        self.statistik.anfragen += 1

        try:
            with self._oeffner(anfrage, timeout=ZEITLIMIT_SEKUNDEN) as antwort:
                koerper = antwort.read().decode("utf-8")
                status = getattr(antwort, "status", 200)
                header = {k.lower(): v for k, v in antwort.headers.items()
                          if k.lower() not in NICHT_SPEICHERN}
        except urllib.error.HTTPError as fehler:
            self.statistik.status[fehler.code] += 1
            fehler_header = {k.lower(): v for k, v in (fehler.headers or {}).items()}
            self._header_beobachten(fehler_header)
            koerper = ""
            try:
                koerper = fehler.read().decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001 - Fehlerkoerper ist optional
                pass
            raise self._fehler_fuer(fehler.code, koerper, anzeige, fehler_header) from None
        except (socket.timeout, TimeoutError):
            self.statistik.status["zeitueberschreitung"] += 1
            raise NetzwerkFehler(
                f"Zeitüberschreitung nach {ZEITLIMIT_SEKUNDEN} s bei {anzeige}"
            ) from None
        except urllib.error.URLError as fehler:
            if isinstance(fehler.reason, (socket.timeout, TimeoutError)):
                self.statistik.status["zeitueberschreitung"] += 1
                raise NetzwerkFehler(
                    f"Zeitüberschreitung nach {ZEITLIMIT_SEKUNDEN} s bei {anzeige}"
                ) from None
            self.statistik.status["netzwerk"] += 1
            raise NetzwerkFehler(
                self._ohne_geheimnis(f"Netzwerkfehler bei {anzeige}: {fehler.reason}")
            ) from None

        self.statistik.status[status] += 1
        self._header_beobachten(header)
        try:
            daten = json.loads(koerper)
        except ValueError:
            raise ServerFehler(f"Antwort von {anzeige} ist kein JSON", status=status) from None
        return ApiAntwort(pfad=anzeige, status=status, header=header, daten=daten)

    def get(self, pfad, **parameter):
        """Nur das JSON - fuer Aufrufer, die Status und Header nicht brauchen."""
        return self.abrufen(pfad, **parameter).daten

    def _fehler_fuer(self, status, koerper, anzeige, header=None):
        grund, nachricht = _fehlertext_der_api(koerper)
        # Supercells eigene Meldung mitgeben - sie ist der beste Hinweis
        # (bei 403 etwa, WELCHE IP abgelehnt wurde). Durch den Filter,
        # damit nichts Geheimes durchrutscht.
        zusatz = f" - Supercell: {grund or '?'}"
        if nachricht:
            zusatz += f" ({nachricht})"
        zusatz = self._ohne_geheimnis(zusatz)

        if status == 401:
            return UngueltigerKeyFehler(
                f"401 bei {anzeige}: Key fehlt oder wird nicht akzeptiert. "
                f"BRAWL_STARS_API_KEY in der .env prüfen und den Container neu erzeugen.{zusatz}",
                status, grund)
        if status == 403:
            return ZugriffVerweigertFehler(
                f"403 bei {anzeige}: Zugriff verweigert. Häufigste Ursache: Der Key ist nicht "
                f"für die öffentliche IP dieses Servers freigegeben (IP-Allowlist im "
                f"Developer-Portal). Ändert sich die IP (DynDNS), muss der Key angepasst "
                f"werden.{zusatz}",
                status, grund)
        if status == 404:
            return NichtGefundenFehler(
                f"404 bei {anzeige}: nicht gefunden - bei Spielern meist ein falscher Tag.{zusatz}",
                status, grund)
        if status == 429:
            retry_after = _retry_after(header)
            hinweis = f" Retry-After: {retry_after} s." if retry_after is not None else ""
            return RatenlimitFehler(
                f"429 bei {anzeige}: Ratenlimit erreicht. Pause einlegen und später "
                f"erneut versuchen.{hinweis}{zusatz}",
                status, grund, retry_after=retry_after)
        if 500 <= status < 600:
            return ServerFehler(
                f"{status} bei {anzeige}: Fehler oder Wartung auf Seiten der API.{zusatz}",
                status, grund)
        return ApiFehler(f"HTTP {status} bei {anzeige}.{zusatz}", status, grund)

    def _warten(self):
        vergangen = time.monotonic() - self._letzte_anfrage
        if vergangen < self.mindestabstand:
            self._schlafen(self.mindestabstand - vergangen)
        self._letzte_anfrage = time.monotonic()

    # --- Pfade ----------------------------------------------------------
    def spieler(self, tag):
        return self.get(pfad_spieler(tag))

    def battlelog(self, tag):
        return self.get(pfad_battlelog(tag))

    def brawler_liste(self):
        return self.get(PFAD_BRAWLER)
