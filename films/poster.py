"""Poster on demand.

Die Uebersichtsseite zeigt alle 216 Filme, aber nur 22 haben nach dem
Import einen Posterpfad. Die uebrigen hier alle beim Seitenaufbau zu
holen waeren rund 200 TMDB-Anfragen fuer Bilder, von denen die meisten
nie ins Bild kommen.

Stattdessen fragt die Seite nach, sobald eine Kachel in Sichtweite
kommt. Was einmal geholt wurde, steht danach in der Datenbank und kostet
beim naechsten Besuch nichts mehr.

Die Obergrenze je Anfrage ist Absicht: TMDB wird nacheinander gefragt,
und eine Anfrage ueber 50 Filme haette den Browser sekundenlang warten
lassen.
"""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from films.models import Film

logger = logging.getLogger(__name__)

SUCHE_URL = "https://api.themoviedb.org/3/search/movie"
TIMEOUT = 5
USER_AGENT = "alex-volkmann-portfolio/1.0 (+https://alex.volkmann.com)"

# Hoechstens so viele Filme je Anfrage bei TMDB nachschlagen.
MAX_JE_ANFRAGE = 8

# Kein Treffer bei TMDB. Wird gespeichert, damit derselbe Film nicht bei
# jedem Seitenaufruf erneut gesucht wird.
KEIN_TREFFER = "-"


def _frage_tmdb(film, api_key):
    frage = {"api_key": api_key, "query": film.titel}
    if film.jahr:
        frage["year"] = film.jahr

    anfrage = Request(
        f"{SUCHE_URL}?{urlencode(frage)}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urlopen(anfrage, timeout=TIMEOUT) as antwort:
            ergebnisse = json.loads(antwort.read().decode("utf-8")).get("results")
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as fehler:
        logger.warning("TMDB-Suche fehlgeschlagen fuer %s: %s", film.titel, fehler)
        return None

    return ergebnisse[0] if ergebnisse else None


def hole_poster(ids):
    """{film_id: poster_url oder None} fuer die angefragten IDs.

    Was schon einen Pfad hat, kommt ohne Netzanfrage zurueck. Der Rest
    wird bei TMDB gesucht - hoechstens MAX_JE_ANFRAGE Stueck.
    """
    filme = list(Film.objects.filter(id__in=ids))
    ergebnis = {}
    offen = []

    for film in filme:
        if film.poster_pfad == KEIN_TREFFER:
            ergebnis[film.id] = None
        elif film.poster_pfad:
            ergebnis[film.id] = film.poster_url
        else:
            offen.append(film)

    api_key = getattr(settings, "TMDB_API_KEY", "")
    if not api_key:
        for film in offen:
            ergebnis[film.id] = None
        return ergebnis

    for film in offen[:MAX_JE_ANFRAGE]:
        daten = _frage_tmdb(film, api_key)
        pfad = (daten or {}).get("poster_path")

        # Auch das Nichtfinden wird festgehalten, sonst sucht die Seite
        # bei jedem Besuch aufs Neue.
        film.poster_pfad = pfad or KEIN_TREFFER
        if daten:
            film.tmdb_id = daten.get("id")
        film.save(update_fields=["poster_pfad", "tmdb_id", "titel_normalisiert",
                                 "aktualisiert_am"])

        ergebnis[film.id] = film.poster_url if pfad else None

    # Was ueber der Grenze lag, bleibt diesmal ohne Antwort - die Seite
    # fragt beim naechsten Sichtbarwerden erneut.
    return ergebnis
