"""Client fuer die offizielle Brawl-Stars-API - Geruest, nicht fertig.

**Wichtig und ausdruecklich so gemeint:** diese Datei ruft die API noch
nicht produktiv ab, und sie interpretiert keine Antwortfelder. Der Grund
steht in der Aufgabenstellung und ist richtig:

    Es ist ungeprueft, ob die offizielle API historische Draft-Bans,
    Build-Daten oder die genaue Pick-Reihenfolge ueberhaupt liefert.

Wer hier jetzt `antwort["battles"][0]["battle"]["teams"]` schreibt,
erfindet eine Struktur und baut den Rest darauf. Deshalb liefert der
Client rohes JSON zurueck, und die Auswertung entsteht erst, wenn eine
echte Antwort vorliegt.

Was schon steht und auch spaeter so bleibt:
- Key ausschliesslich aus der Umgebung (`BRAWL_STARS_API_KEY`)
- Ratenbegrenzung, Zeitlimits, saubere Fehlertypen
- Tags werden normalisiert (fuehrendes #, Grossschreibung, URL-Kodierung)

Die IP-Bindung nicht vergessen: Supercell bindet API-Keys an die IP des
abrufenden Servers. Ein Key, der lokal funktioniert, funktioniert auf
dem Server nicht automatisch.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from drafter import config

BASIS_URL = "https://api.brawlstars.com/v1"

# Mindestabstand zwischen zwei Anfragen. Konservativ gewaehlt: das
# tatsaechliche Limit steht in der offiziellen Dokumentation und wird
# geprueft, sobald ein Key vorliegt.
MINDESTABSTAND_SEKUNDEN = 0.2
ZEITLIMIT_SEKUNDEN = 12


class ApiFehler(RuntimeError):
    """Oberklasse aller Fehler dieses Clients."""


class KeinKeyFehler(ApiFehler):
    """Kein API-Key konfiguriert."""


class RatenlimitFehler(ApiFehler):
    """Die API hat wegen zu vieler Anfragen abgelehnt (429)."""


class NichtGefundenFehler(ApiFehler):
    """Angefragte Ressource existiert nicht (404)."""


def tag_normalisieren(tag):
    """'#2ABC' / '2abc' -> '%232ABC'.

    Spieler- und Clubtags beginnen im Spiel mit '#'. In der URL muss das
    Zeichen kodiert werden, sonst endet der Pfad dort. Haeufige Quelle
    stiller 404er.
    """
    sauber = str(tag or "").strip().upper().lstrip("#")
    if not sauber:
        raise ApiFehler("Leerer Tag")
    return urllib.parse.quote(f"#{sauber}", safe="")


class BrawlApiClient:
    """Duenne Huelle um die HTTP-Ebene.

    Absichtlich ohne Kenntnis der Antwortstruktur: `get()` gibt zurueck,
    was die API schickt. Was davon brauchbar ist, entscheidet spaeter
    der Aggregator - anhand echter Antworten.
    """

    def __init__(self, api_key=None, basis_url=BASIS_URL):
        self.api_key = api_key if api_key is not None else config.api_key()
        self.basis_url = basis_url.rstrip("/")
        self._letzte_anfrage = 0.0

    @property
    def einsatzbereit(self):
        """Gibt es ueberhaupt einen Key? Ohne ihn laeuft der Drafter weiter."""
        return bool(self.api_key)

    # --- HTTP -----------------------------------------------------------
    def get(self, pfad, **parameter):
        """Ein GET gegen die API. Gibt das rohe JSON zurueck."""
        if not self.einsatzbereit:
            raise KeinKeyFehler(
                "BRAWL_STARS_API_KEY ist nicht gesetzt. Der Key gehört in die "
                "gitignorte .env und wird über docker-compose.yml durchgereicht."
            )

        self._warten()
        url = f"{self.basis_url}/{pfad.lstrip('/')}"
        if parameter:
            url += "?" + urllib.parse.urlencode(parameter)

        anfrage = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(anfrage, timeout=ZEITLIMIT_SEKUNDEN) as antwort:
                return json.loads(antwort.read().decode("utf-8"))
        except urllib.error.HTTPError as fehler:
            if fehler.code == 429:
                raise RatenlimitFehler("Ratenlimit erreicht") from fehler
            if fehler.code == 404:
                raise NichtGefundenFehler(f"Nicht gefunden: {pfad}") from fehler
            if fehler.code == 403:
                raise ApiFehler(
                    "403 - Key ungültig oder nicht für diese IP freigegeben. "
                    "Supercell bindet Keys an die IP des Servers."
                ) from fehler
            raise ApiFehler(f"HTTP {fehler.code} bei {pfad}") from fehler
        except urllib.error.URLError as fehler:
            raise ApiFehler(f"Netzwerkfehler bei {pfad}: {fehler.reason}") from fehler

    def _warten(self):
        vergangen = time.monotonic() - self._letzte_anfrage
        if vergangen < MINDESTABSTAND_SEKUNDEN:
            time.sleep(MINDESTABSTAND_SEKUNDEN - vergangen)
        self._letzte_anfrage = time.monotonic()

    # --- Pfade ----------------------------------------------------------
    # UNGEPRUEFT: Diese Pfade folgen der oeffentlich bekannten Struktur
    # der Supercell-APIs. Vor dem ersten produktiven Lauf gegen die
    # aktuelle offizielle Dokumentation pruefen - und die Antworten
    # ansehen, BEVOR irgendwo Felder ausgelesen werden.
    def spieler(self, tag):
        return self.get(f"players/{tag_normalisieren(tag)}")

    def battlelog(self, tag):
        return self.get(f"players/{tag_normalisieren(tag)}/battlelog")

    def brawler_liste(self):
        return self.get("brawlers")
