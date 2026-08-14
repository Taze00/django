"""Endpunkte der Filmsektion."""

import json

from django.http import HttpResponse

from films import suchindex


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
