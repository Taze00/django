"""Liest das oeffentliche Letterboxd-RSS eines Nutzers.

Auslegung: Diese Sektion ist Beiwerk. Faellt Letterboxd aus, ist langsam
oder aendert sein Feed-Format, liefert `get_recent_entries()` eine leere
Liste und die Sektion verschwindet im Template. Die Seite darf unter
keinen Umstaenden wegen Letterboxd eine Fehlerseite zeigen - deshalb ist
die Fehlerbehandlung hier bewusst breit (`except Exception`) statt
selektiv.
"""

import logging
import re
from datetime import datetime
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

FEED_URL = "https://letterboxd.com/{username}/rss/"
PROFILE_URL = "https://letterboxd.com/{username}/"

CACHE_KEY = "letterboxd:entries:{username}"
CACHE_SECONDS = 6 * 60 * 60  # 6 Stunden

REQUEST_TIMEOUT = 5  # Sekunden; lieber leere Sektion als haengende Seite
USER_AGENT = "alex-volkmann-portfolio/1.0 (+https://alex.volkmann.com)"

# Letterboxd haengt seine Zusatzfelder in einen eigenen Namespace.
NS = {
    "letterboxd": "https://letterboxd.com",
    "tmdb": "https://themoviedb.org",
}

# "Se7en, 1995 - ★★★½" -> Titel und Jahr stehen sauber in eigenen
# Feldern, der <title> dient nur als Rueckfallebene.
TITLE_FALLBACK = re.compile(r"^(?P<titel>.+),\s*(?P<jahr>\d{4})\b")


def _text(item, path, namespaces=None):
    """Elementtext oder None - erspart ueberall dieselbe None-Pruefung."""
    node = item.find(path, namespaces or {})
    if node is None or node.text is None:
        return None
    stripped = node.text.strip()
    return stripped or None


def _parse_item(item):
    """Ein <item> in ein flaches dict. None, wenn unbrauchbar."""
    titel = _text(item, "letterboxd:filmTitle", NS)
    jahr = _text(item, "letterboxd:filmYear", NS)

    # Aeltere oder abweichende Eintraege ohne die Extrafelder: aus dem
    # <title> herausziehen, statt den Eintrag zu verlieren.
    if not titel:
        roh = _text(item, "title")
        if not roh:
            return None
        treffer = TITLE_FALLBACK.match(roh)
        titel = treffer.group("titel") if treffer else roh
        jahr = jahr or (treffer.group("jahr") if treffer else None)

    # Bewertung ist optional - ein Tagebucheintrag muss keine haben.
    bewertung = None
    roh_bewertung = _text(item, "letterboxd:memberRating", NS)
    if roh_bewertung:
        try:
            bewertung = float(roh_bewertung)
        except ValueError:
            bewertung = None

    # Serien tragen tmdb:tvId statt tmdb:movieId. Nur movieId ergibt eine
    # gueltige TMDB-Poster-URL, tvId wird deshalb verworfen.
    tmdb_id = _text(item, "tmdb:movieId", NS)

    gesehen_am = None
    roh_datum = _text(item, "letterboxd:watchedDate", NS)
    if roh_datum:
        try:
            gesehen_am = datetime.strptime(roh_datum, "%Y-%m-%d").date()
        except ValueError:
            gesehen_am = None

    try:
        jahr = int(jahr) if jahr else None
    except (TypeError, ValueError):
        jahr = None

    return {
        "titel": titel,
        "jahr": jahr,
        "bewertung": bewertung,
        "tmdb_id": tmdb_id,
        "gesehen_am": gesehen_am,
        "link": _text(item, "link"),
    }


def _fetch_feed(username):
    """Roh-XML holen. Wirft bei Netzwerk- oder HTTP-Fehlern."""
    request = Request(
        FEED_URL.format(username=username),
        headers={"User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return response.read()


def get_recent_entries(username=None, limit=None):
    """Zuletzt gesehene Filme, neueste zuerst.

    Gibt bei jedem Problem eine leere Liste zurueck. Das Ergebnis wird
    sechs Stunden gecacht - auch die leere Liste, damit ein Ausfall nicht
    bei jedem Seitenaufruf einen neuen Timeout ausloest.
    """
    username = username or getattr(settings, "LETTERBOXD_USERNAME", "")
    if not username:
        return []

    cache_key = CACHE_KEY.format(username=username)
    zwischengespeichert = cache.get(cache_key)
    if zwischengespeichert is not None:
        return zwischengespeichert[:limit] if limit else zwischengespeichert

    eintraege = []
    try:
        roh = _fetch_feed(username)
        wurzel = ElementTree.fromstring(roh)
        for item in wurzel.iterfind("./channel/item"):
            eintrag = _parse_item(item)
            if eintrag:
                eintraege.append(eintrag)
    except (URLError, HTTPError, TimeoutError, OSError) as fehler:
        logger.warning("Letterboxd nicht erreichbar (%s): %s", username, fehler)
        eintraege = []
    except ElementTree.ParseError as fehler:
        logger.warning("Letterboxd-Feed unlesbar (%s): %s", username, fehler)
        eintraege = []
    except Exception as fehler:  # bewusst breit - siehe Modul-Docstring
        logger.exception("Letterboxd unerwartet fehlgeschlagen (%s): %s", username, fehler)
        eintraege = []

    cache.set(cache_key, eintraege, CACHE_SECONDS)
    return eintraege[:limit] if limit else eintraege


def get_profile_url(username=None):
    username = username or getattr(settings, "LETTERBOXD_USERNAME", "")
    return PROFILE_URL.format(username=username) if username else ""
