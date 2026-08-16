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

from films.models import Film, KEIN_TREFFER

logger = logging.getLogger(__name__)

# Zwei Endpunkte. Der Bestand kommt aus Letterboxd und ist ueberwiegend
# Film, enthaelt aber auch Serien - die liegen bei TMDB unter /tv/ und
# sind ueber /search/movie grundsaetzlich nicht zu finden. Genau daran
# sind The Queen's Gambit, DAHMER, Squid Game und Stranger Things
# gescheitert: gesucht wurde, gefunden nichts, und der Merker
# KEIN_TREFFER machte das dauerhaft.
SUCHE_URL = {
    "movie": "https://api.themoviedb.org/3/search/movie",
    "tv": "https://api.themoviedb.org/3/search/tv",
}

# TMDB nennt den Jahres-Parameter je Endpunkt anders. Mit "year" gegen
# /search/tv bekaeme man ihn nicht als Fehler zurueck - er wird still
# ignoriert, und die Suche liefe ohne Jahreseinschraenkung.
JAHR_FELD = {"movie": "year", "tv": "first_air_date_year"}

TIMEOUT = 5
USER_AGENT = "alex-volkmann-portfolio/1.0 (+https://alex.volkmann.com)"

# Hoechstens so viele Filme je Anfrage bei TMDB nachschlagen.
MAX_JE_ANFRAGE = 8


def _suche(film, api_key, medium):
    """Erster Treffer bei TMDB, oder None."""
    frage = {"api_key": api_key, "query": film.titel}
    if film.jahr:
        frage[JAHR_FELD[medium]] = film.jahr

    anfrage = Request(
        f"{SUCHE_URL[medium]}?{urlencode(frage)}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urlopen(anfrage, timeout=TIMEOUT) as antwort:
            ergebnisse = json.loads(antwort.read().decode("utf-8")).get("results")
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as fehler:
        logger.warning(
            "TMDB-Suche (%s) fehlgeschlagen fuer %s: %s", medium, film.titel, fehler
        )
        return None

    return ergebnisse[0] if ergebnisse else None


def _frage_tmdb(film, api_key):
    """Erst als Film suchen, bei Fehlschlag als Serie.

    Gibt (treffer, medium) zurueck. Die zweite Anfrage kostet nur dort
    etwas, wo die erste ohnehin leer ausging - und auch das nur einmal
    je Titel, danach steht das Ergebnis in der Datenbank.
    """
    treffer = _suche(film, api_key, "movie")
    if treffer:
        return treffer, "movie"
    return _suche(film, api_key, "tv"), "tv"


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
        daten, medium = _frage_tmdb(film, api_key)
        pfad = (daten or {}).get("poster_path")

        # Auch das Nichtfinden wird festgehalten, sonst sucht die Seite
        # bei jedem Besuch aufs Neue.
        film.poster_pfad = pfad or KEIN_TREFFER

        # tmdb_id nur bei einem Filmtreffer. Das Feld kommt aus dem
        # Letterboxd-Import (tmdb:movieId) und meint dort eine Film-ID;
        # eine Serien-ID darin saehe genauso aus, wuerde aber gegen
        # /movie/ gestellt 404 liefern. Fuer die Kachel wird sie nicht
        # gebraucht - dafuer reicht der Posterpfad.
        if daten and medium == "movie":
            film.tmdb_id = daten.get("id")
        film.save(update_fields=["poster_pfad", "tmdb_id", "titel_normalisiert",
                                 "aktualisiert_am"])

        ergebnis[film.id] = film.poster_url if pfad else None

    # Was ueber der Grenze lag, bleibt diesmal ohne Antwort - die Seite
    # fragt beim naechsten Sichtbarwerden erneut.
    return ergebnis
