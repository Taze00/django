"""Poster-URLs von TMDB.

Die Bild-URL braucht den `poster_path` eines Films, der weder im
Letterboxd-RSS noch in filme.json steht - er muss einmal pro Film bei
TMDB erfragt werden. Ergebnisse werden lange gecacht, weil sich der
Posterpfad praktisch nie aendert.

Ohne TMDB_API_KEY liefert das Modul ueberall None. Die Sektion
funktioniert dann weiter, nur ohne Bilder.

Poster werden bewusst von image.tmdb.org geladen und nicht von
a.ltrbxd.com - Letterboxds Bilder sind nicht zum Einbetten gedacht.
"""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Filme und Serien liegen bei TMDB unter verschiedenen Endpunkten. Eine
# Serien-ID gegen /movie/ zu schicken liefert 404 - deshalb zwei Zweige.
DETAIL_URL = {
    "movie": "https://api.themoviedb.org/3/movie/{tmdb_id}",
    "tv": "https://api.themoviedb.org/3/tv/{tmdb_id}",
}

# Medium steckt im Cache-Key: dieselbe Zahl kann als Film und als Serie
# existieren und auf voellig verschiedene Titel zeigen.
CACHE_KEY = "tmdb:poster:{medium}:{tmdb_id}"
CACHE_SECONDS = 30 * 24 * 60 * 60  # 30 Tage
CACHE_MISS = ""  # gecachtes "kein Poster" - None hiesse "noch nicht geprueft"

REQUEST_TIMEOUT = 5
USER_AGENT = "alex-volkmann-portfolio/1.0 (+https://alex.volkmann.com)"


def _hole_poster_pfad(tmdb_id, api_key, medium):
    query = urlencode({"api_key": api_key})
    request = Request(
        f"{DETAIL_URL[medium].format(tmdb_id=tmdb_id)}?{query}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        daten = json.loads(response.read().decode("utf-8"))
    return daten.get("poster_path") or CACHE_MISS


def get_poster_url(tmdb_id, groesse=None, medium="movie"):
    """Vollstaendige Poster-URL oder None.

    `medium` waehlt den Endpunkt: "movie" (Standard) oder "tv".
    """
    api_key = getattr(settings, "TMDB_API_KEY", "")
    if not tmdb_id or not api_key or medium not in DETAIL_URL:
        return None

    cache_key = CACHE_KEY.format(medium=medium, tmdb_id=tmdb_id)
    pfad = cache.get(cache_key)

    if pfad is None:
        try:
            pfad = _hole_poster_pfad(tmdb_id, api_key, medium)
        except (URLError, HTTPError, TimeoutError, OSError) as fehler:
            logger.warning("TMDB nicht erreichbar (%s): %s", tmdb_id, fehler)
            return None
        except (json.JSONDecodeError, ValueError) as fehler:
            logger.warning("TMDB-Antwort unlesbar (%s): %s", tmdb_id, fehler)
            return None
        except Exception as fehler:
            logger.exception("TMDB unerwartet fehlgeschlagen (%s): %s", tmdb_id, fehler)
            return None
        cache.set(cache_key, pfad, CACHE_SECONDS)

    if not pfad:
        return None

    basis = getattr(settings, "TMDB_IMAGE_BASE", "https://image.tmdb.org/t/p")
    groesse = groesse or getattr(settings, "TMDB_POSTER_SIZE", "w342")
    return f"{basis}/{groesse}{pfad}"


def mit_postern(eintraege, id_feld="tmdb_id", ziel_feld="poster_url", medium="movie"):
    """Ergaenzt jeden Eintrag um seine Poster-URL (None, wenn keine)."""
    for eintrag in eintraege:
        eintrag[ziel_feld] = get_poster_url(eintrag.get(id_feld), medium=medium)
    return eintraege


def mit_postern_gemischt(eintraege):
    """Wie mit_postern, waehlt den Endpunkt aber pro Eintrag.

    Fuer das Letterboxd-Tagebuch: Filme tragen tmdb_id, Serien
    tmdb_tv_id. Bisher blieben Serien ohne Poster.
    """
    for eintrag in eintraege:
        if eintrag.get("tmdb_id"):
            eintrag["poster_url"] = get_poster_url(eintrag["tmdb_id"], medium="movie")
        elif eintrag.get("tmdb_tv_id"):
            eintrag["poster_url"] = get_poster_url(eintrag["tmdb_tv_id"], medium="tv")
        else:
            eintrag["poster_url"] = None
    return eintraege
