"""Endpunkte der Filmsektion."""

import json

from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render

from films import poster, statistik, suchindex
from films.models import Film


def suchindex_json(request):
    """Alle Filme als kompaktes JSON fuer die Suche im Browser.

    Bewusst ein Endpunkt und keine statische Datei: eine Datei muesste
    nach jedem Import neu erzeugt werden und waere sonst still veraltet.
    Der Inhalt haengt an einem Cache, der Abruf kostet also keine
    Datenbankrunde.

    separators ohne Leerzeichen: bei 266 Eintraegen sind das rund 2 KB
    weniger. ensure_ascii=False laesst Umlaute als Umlaute stehen, statt
    sie zu \\u-Sequenzen aufzublasen.
    """
    daten = suchindex.hole_index()
    rumpf = json.dumps(daten, ensure_ascii=False, separators=(",", ":"))

    antwort = HttpResponse(rumpf, content_type="application/json; charset=utf-8")
    # Der Bestand aendert sich nur beim Import. Eine Stunde Browsercache
    # spart bei wiederholten Besuchen den Abruf ganz.
    antwort["Cache-Control"] = "public, max-age=3600"
    return antwort


def poster_json(request):
    """Posterbilder fuer die angefragten Filme.

        /api/filme/poster?ids=12,34,56

    Antwortet mit {"12": "https://...", "34": null}. Wird von der
    Uebersichtsseite aufgerufen, sobald Kacheln in Sichtweite kommen -
    nicht fuer alle 216 auf einmal.
    """
    roh = request.GET.get("ids", "")
    ids = []
    for teil in roh.split(",")[:50]:
        teil = teil.strip()
        if teil.isdigit():
            ids.append(int(teil))

    if not ids:
        return HttpResponse("{}", content_type="application/json")

    treffer = poster.hole_poster(ids)
    rumpf = json.dumps({str(k): v for k, v in treffer.items()}, ensure_ascii=False)
    return HttpResponse(rumpf, content_type="application/json; charset=utf-8")


def uebersicht(request):
    """Alle gesehenen Filme als Raster - sortier- und filterbar.

    Die ganze Liste geht ins Markup, sortiert und gefiltert wird im
    Browser. Bei 216 Eintraegen ist das schneller als jede Serverrunde
    und funktioniert ohne Nachladen.
    """
    # nulls_last: PostgreSQL sortiert NULL bei DESC von sich aus nach
    # vorn - die beiden unbewerteten Filme staenden sonst ueber den
    # Fuenf-Sterne-Filmen. Betrifft die Ausgabe ohne JavaScript; mit JS
    # sortiert der Browser beim Start ohnehin neu.
    filme = list(
        Film.objects.filter(gesehen=True)
        .order_by(F("wertung").desc(nulls_last=True), "titel")
    )
    return render(request, "filme.html", {
        "filme": filme,
        "statistik": statistik.hole_statistik(),
    })
