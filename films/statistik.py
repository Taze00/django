"""Kennzahlen des Filmbestands.

Alle Werte kommen aus der Datenbank. Nichts hier ist hartkodiert - nach
einem neuen Import stimmen Text und Grafik von selbst.
"""

from decimal import Decimal

from django.core.cache import cache
from django.db.models import Avg, Count

from films.models import Film

CACHE_KEY = "films:statistik:v1"
CACHE_SECONDS = 60 * 60

# Die volle Skala in halben Schritten. Bewusst alle zehn Stufen und
# nicht nur die belegten: dass bei 1.0 kein einziger Film steht, ist
# eine Aussage und keine Luecke.
STUFEN = [Decimal(f"{n / 2:.1f}") for n in range(1, 11)]


def _leere_cache():
    cache.delete(CACHE_KEY)


def baue_statistik():
    bewertet = Film.objects.filter(wertung__isnull=False)
    anzahl_bewertet = bewertet.count()

    gezaehlt = dict(
        bewertet.values_list("wertung").annotate(n=Count("id")).values_list("wertung", "n")
    )

    verteilung = []
    hoechster = max(gezaehlt.values(), default=0)
    for stufe in STUFEN:
        anzahl = gezaehlt.get(stufe, 0)
        verteilung.append({
            "stufe": stufe,
            "anzahl": anzahl,
            # Anteil an der haeufigsten Stufe - danach richtet sich die
            # Balkenhoehe. An der Gesamtzahl gemessen waeren alle Balken
            # winzig und der Verlauf nicht mehr lesbar.
            "anteil": round(anzahl / hoechster * 100) if hoechster else 0,
            # Der Gipfel ist die Pointe der Grafik und wird hervorgehoben.
            "gipfel": anzahl == hoechster and anzahl > 0,
        })

    schnitt = bewertet.aggregate(s=Avg("wertung"))["s"] or Decimal("0")
    ab_vier = bewertet.filter(wertung__gte=Decimal("4.0")).count()
    volle = gezaehlt.get(Decimal("5.0"), 0)

    # Als fertige Zeichenkette mit Komma. LANGUAGE_CODE steht auf en-us,
    # floatformat lieferte sonst "2.83" auf einer deutschen Seite - und
    # die Locale global umzustellen haette Datumsformate ueberall sonst
    # mitgeaendert.
    def mit_komma(wert, stellen):
        return f"{wert:.{stellen}f}".replace(".", ",")

    return {
        "gesehen": Film.objects.filter(gesehen=True).count(),
        "schnitt_anzeige": mit_komma(schnitt, 2),
        "schnitt_kurz": mit_komma(schnitt, 1),
        "bewertet": anzahl_bewertet,
        "watchlist": Film.objects.filter(auf_watchlist=True).count(),
        "schnitt": float(schnitt),
        "volle_wertung": volle,
        "ab_vier": ab_vier,
        "ab_vier_prozent": round(ab_vier / anzahl_bewertet * 100) if anzahl_bewertet else 0,
        "verteilung": verteilung,
    }


def hole_statistik():
    daten = cache.get(CACHE_KEY)
    if daten is None:
        daten = baue_statistik()
        cache.set(CACHE_KEY, daten, CACHE_SECONDS)
    return daten
