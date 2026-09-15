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
"""

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

from drafter import config

BASIS_URL = "https://api.brawlstars.com/v1"

# Abstand zwischen zwei Anfragen dieses Clients. KEINE Aussage ueber das
# erlaubte Limit - das steht nicht in der Dokumentation, die wir einsehen
# konnten. Der Abstand verhindert nur, dass ein Testlauf versehentlich
# viele Anfragen in kurzer Zeit abfeuert.
MINDESTABSTAND_SEKUNDEN = 0.2
ZEITLIMIT_SEKUNDEN = 12

# Antwort-Header, die nicht gespeichert werden. Alle anderen bleiben
# erhalten - darunter moeglicherweise Hinweise auf Ratenbegrenzung, die
# wir erst an echten Antworten sehen.
NICHT_SPEICHERN = frozenset({"set-cookie"})


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
    """429 - zu viele Anfragen."""


class ServerFehler(ApiFehler):
    """5xx - Fehler oder Wartung auf Seiten der API."""


class NetzwerkFehler(ApiFehler):
    """Zeitueberschreitung, DNS, Verbindungsabbruch - keine HTTP-Antwort."""


# =========================================================================
# Antwort
# =========================================================================

@dataclass(frozen=True)
class ApiAntwort:
    """Eine erfolgreiche Antwort - vollstaendig, nichts interpretiert."""

    pfad: str
    status: int
    header: dict
    daten: object
    abgerufen_am: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def tag_normalisieren(tag):
    """'#2ABC' / '2abc' -> '%232ABC'.

    Spieler- und Clubtags beginnen im Spiel mit '#'. In der URL muss das
    Zeichen kodiert werden, sonst endet der Pfad dort.
    """
    sauber = str(tag or "").strip().upper().lstrip("#")
    if not sauber:
        raise ApiFehler("Leerer Tag")
    return urllib.parse.quote(f"#{sauber}", safe="")


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


class BrawlApiClient:
    """Duenne Huelle um die HTTP-Ebene. Kennt Pfade, keine Felder."""

    def __init__(self, api_key=None, basis_url=BASIS_URL, oeffner=None):
        # Privat - siehe Modulkommentar. `oeffner` ersetzt urlopen in Tests,
        # damit kein Test das Netz braucht.
        self._api_key = (api_key if api_key is not None else config.api_key()) or ""
        self.basis_url = basis_url.rstrip("/")
        self._oeffner = oeffner or urllib.request.urlopen
        self._letzte_anfrage = 0.0

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
        """GET gegen die API. Gibt eine ApiAntwort zurueck oder wirft ApiFehler."""
        if not self.einsatzbereit:
            raise KeinKeyFehler(
                "BRAWL_STARS_API_KEY ist nicht gesetzt. Der Key gehört in die gitignorte "
                ".env und wird über docker-compose.yml durchgereicht - es wurde nichts abgerufen."
            )

        self._warten()
        pfad = pfad.lstrip("/")
        abfrage = f"?{urllib.parse.urlencode(parameter)}" if parameter else ""
        anfrage = urllib.request.Request(f"{self.basis_url}/{pfad}{abfrage}", headers={
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        })
        anzeige = f"/{pfad}{abfrage}"

        try:
            with self._oeffner(anfrage, timeout=ZEITLIMIT_SEKUNDEN) as antwort:
                koerper = antwort.read().decode("utf-8")
                status = getattr(antwort, "status", 200)
                header = {k.lower(): v for k, v in antwort.headers.items()
                          if k.lower() not in NICHT_SPEICHERN}
        except urllib.error.HTTPError as fehler:
            koerper = ""
            try:
                koerper = fehler.read().decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001 - Fehlerkoerper ist optional
                pass
            raise self._fehler_fuer(fehler.code, koerper, anzeige) from None
        except (socket.timeout, TimeoutError):
            raise NetzwerkFehler(
                f"Zeitüberschreitung nach {ZEITLIMIT_SEKUNDEN} s bei {anzeige}"
            ) from None
        except urllib.error.URLError as fehler:
            if isinstance(fehler.reason, (socket.timeout, TimeoutError)):
                raise NetzwerkFehler(
                    f"Zeitüberschreitung nach {ZEITLIMIT_SEKUNDEN} s bei {anzeige}"
                ) from None
            raise NetzwerkFehler(
                self._ohne_geheimnis(f"Netzwerkfehler bei {anzeige}: {fehler.reason}")
            ) from None

        try:
            daten = json.loads(koerper)
        except ValueError:
            raise ServerFehler(f"Antwort von {anzeige} ist kein JSON", status=status) from None
        return ApiAntwort(pfad=anzeige, status=status, header=header, daten=daten)

    def get(self, pfad, **parameter):
        """Nur das JSON - fuer Aufrufer, die Status und Header nicht brauchen."""
        return self.abrufen(pfad, **parameter).daten

    def _fehler_fuer(self, status, koerper, anzeige):
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
            return RatenlimitFehler(
                f"429 bei {anzeige}: Ratenlimit erreicht. Pause einlegen und später "
                f"erneut versuchen.{zusatz}",
                status, grund)
        if 500 <= status < 600:
            return ServerFehler(
                f"{status} bei {anzeige}: Fehler oder Wartung auf Seiten der API.{zusatz}",
                status, grund)
        return ApiFehler(f"HTTP {status} bei {anzeige}.{zusatz}", status, grund)

    def _warten(self):
        vergangen = time.monotonic() - self._letzte_anfrage
        if vergangen < MINDESTABSTAND_SEKUNDEN:
            time.sleep(MINDESTABSTAND_SEKUNDEN - vergangen)
        self._letzte_anfrage = time.monotonic()

    # --- Pfade ----------------------------------------------------------
    # Nur Pfade, die ausdruecklich getestet werden sollen. Weitere kommen
    # erst dazu, wenn sie in der offiziellen Dokumentation belegt sind.
    def spieler(self, tag):
        return self.get(f"players/{tag_normalisieren(tag)}")

    def battlelog(self, tag):
        return self.get(f"players/{tag_normalisieren(tag)}/battlelog")

    def brawler_liste(self):
        return self.get("brawlers")
