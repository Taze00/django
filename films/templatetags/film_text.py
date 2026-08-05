"""Textfilter fuer die Filmsektion.

Der volle `mein_text` bleibt unangetastet in films/data/ - gekuerzt wird
erst bei der Ausgabe. Das Detail-Overlay kann spaeter denselben Datensatz
in voller Laenge zeigen.
"""

import re

from django import template

register = template.Library()

# Satzende = Punkt/Ausrufe-/Fragezeichen gefolgt von Leerraum. Der
# Lookbehind laesst das Zeichen am Satz stehen, statt es wegzuwerfen.
SATZ_ENDE = re.compile(r"(?<=[.!?])\s+")

# Zeichen, die nach einem harten Schnitt am Wortende haesslich stehen
# bleiben ("... und," -> "... und").
SCHNITT_RESTE = ",;:.!?-–—"

MAX_SAETZE = 2
MAX_ZEICHEN = 120


@register.filter
def kurzfassung(text, laenge=MAX_ZEICHEN):
    """Die ersten zwei Saetze, hoechstens `laenge` Zeichen.

    Wird etwas weggelassen, endet das Ergebnis auf ein Auslassungszeichen.
    Passt der Text ohnehin, kommt er unveraendert zurueck.
    """
    text = " ".join(str(text or "").split())
    if not text:
        return ""

    try:
        laenge = int(laenge)
    except (TypeError, ValueError):
        laenge = MAX_ZEICHEN

    saetze = SATZ_ENDE.split(text)
    kurz = " ".join(saetze[:MAX_SAETZE]).strip()
    # Ab dem dritten Satz ist bereits etwas unter den Tisch gefallen.
    gekuerzt = len(saetze) > MAX_SAETZE

    if len(kurz) > laenge:
        # An der Wortgrenze schneiden, damit kein Wortfragment stehen
        # bleibt. Gibt es innerhalb der Grenze keinen Leerraum (ein sehr
        # langes Wort), bleibt der harte Schnitt.
        schnitt = kurz[:laenge].rsplit(" ", 1)[0] or kurz[:laenge]
        kurz = schnitt.rstrip(SCHNITT_RESTE)
        gekuerzt = True

    if not gekuerzt:
        return kurz

    # Das Auslassungszeichen schluckt einen Schlusspunkt ("Satz zwei.…"
    # liest sich falsch). Ausrufe- und Fragezeichen bleiben, die tragen
    # Bedeutung.
    if kurz.endswith("."):
        kurz = kurz[:-1]

    return f"{kurz}…"
