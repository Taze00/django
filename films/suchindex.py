"""Suchindex fuer die Filmsuche im Browser.

Ein einziger Abruf liefert alle Filme; gesucht wird danach vollstaendig
im Browser, ohne weitere Serveranfrage. Deshalb zaehlt hier jedes Byte:
die Schluessel sind einbuchstabig und der Letterboxd-Link wird auf seine
ID eingedampft (aus "https://boxd.it/2a9q" wird "2a9q"), die volle URL
baut das JavaScript wieder zusammen.

    t  Titel, wie er angezeigt wird
    n  Titel normalisiert (klein, ohne Akzente) - danach wird gesucht
    j  Jahr
    w  Wertung als Zahl, fehlt bei unbewerteten
    u  Letterboxd-ID
    l  1 = steht auf der Watchlist, fehlt sonst

Was fehlt, ist bewusst weggelassen und nicht vergessen: `w` fehlt heisst
"gesehen, aber nicht bewertet", `l` fehlt heisst "nicht auf der Liste".
Das spart bei 266 Eintraegen deutlich mehr, als es an Sonderfaellen im
JavaScript kostet.
"""

from django.core.cache import cache

from films.models import Film

CACHE_KEY = "films:suchindex:v1"
CACHE_SECONDS = 60 * 60  # Der Bestand aendert sich nur beim Import.

BOXD_PRAEFIX = "https://boxd.it/"


def _kurz_uri(uri):
    """'https://boxd.it/2a9q' -> '2a9q'. Fremde URLs bleiben ganz."""
    if uri and uri.startswith(BOXD_PRAEFIX):
        return uri[len(BOXD_PRAEFIX):]
    return uri or ""


def baue_index():
    """Liste aller Filme als kompakte dicts."""
    felder = ("titel", "titel_normalisiert", "jahr", "wertung",
              "letterboxd_uri", "auf_watchlist")

    eintraege = []
    for film in Film.objects.all().only(*felder).order_by("titel"):
        eintrag = {
            "t": film.titel,
            "n": film.titel_normalisiert,
            "u": _kurz_uri(film.letterboxd_uri),
        }
        if film.jahr:
            eintrag["j"] = film.jahr
        if film.wertung is not None:
            # float statt Decimal - json.dumps kann Decimal nicht, und
            # 4.5 ist kuerzer als "4.5".
            eintrag["w"] = float(film.wertung)
        if film.auf_watchlist:
            eintrag["l"] = 1
        eintraege.append(eintrag)

    return eintraege


def hole_index():
    """Gecachter Index. Beim Import wird der Cache verworfen."""
    daten = cache.get(CACHE_KEY)
    if daten is None:
        daten = baue_index()
        cache.set(CACHE_KEY, daten, CACHE_SECONDS)
    return daten


def leere_cache():
    cache.delete(CACHE_KEY)
