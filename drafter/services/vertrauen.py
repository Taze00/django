# -*- coding: utf-8 -*-
"""Wie belastbar ist eine Aussage ueber einen Brawler?

Fuenf Stufen, absteigend. Die Reihenfolge ist die Grundregel der
Wissensbasis - wer eine Eigenschaft braucht, nimmt die hoechste Stufe,
die etwas dazu sagt, und nicht die bequemste:

    MECHANIK   objektiv, patchstabil, nachschlagbar ("Pam heilt")
    FACHQUELLE gepflegte Einordnung (Rolle, Faehigkeit) - qualitativ
    GEMESSEN   aus Partien abgeleitet
    DEMO       Handschaetzung vom 2026-09-14, grobes 5er-Raster
    UNBEKANNT  nichts davon - und das ist eine Antwort, keine Luecke

**Warum DEMO unter GEMESSEN steht.** Die zwanzig Demo-Profile sind in
einer Sitzung entstanden und tragen 263 Werte aus nur 21 verschiedenen
Zahlen, 92 % davon Vielfache von fuenf. Das ist eine Einordnung in
grobe Baender, keine Messung auf zwei Stellen. Sie weiter als Zahl
zwischen 0 und 100 zu lesen, behauptet eine Genauigkeit, die nie
dahinterstand - und weil nur zwanzig von 106 Brawlern sie haben,
entstand daraus ein struktureller Vorteil fuer genau diese zwanzig.

Deshalb: Demo-Werte werden vor jeder Verwendung auf ihre **Baender**
zurueckgefuehrt. Die Aussage "Pam heilt viel" bleibt; die Aussage "Pam
heilt zu 90 von 100" verschwindet. Geloescht wird nichts - `attributes`
bleibt unveraendert lesbar, damit alte Faelle reproduzierbar bleiben.
"""

from drafter.models.base import Datenquelle

MECHANIK = "mechanik"
FACHQUELLE = "fachquelle"
GEMESSEN = "gemessen"
DEMO = "demo"
UNBEKANNT = "unbekannt"

RANGFOLGE = (MECHANIK, FACHQUELLE, GEMESSEN, DEMO, UNBEKANNT)

LABEL = {
    MECHANIK: "Mechanik",
    FACHQUELLE: "Fachquelle",
    GEMESSEN: "gemessen",
    DEMO: "Demo-Schätzung",
    UNBEKANNT: "unbekannt",
}

# Baender, auf die eine Demo-Zahl zurueckgefuehrt wird. Die Grenzen
# folgen dem Raster, in dem die Werte tatsaechlich eingetragen wurden
# (haeufigste Werte: 60, 70, 80, 55, 65) - drei Stufen, mehr gibt die
# Quelle nicht her.
BAENDER = ((0.45, 0.30), (0.70, 0.55), (1.01, 0.80))


def band(wert):
    """Eine Demo-Zahl auf ihr Band zurueckfuehren (0-1 rein, 0-1 raus).

    Null bleibt Null: ein ausdruecklich eingetragenes "kann das nicht"
    ist eine Aussage und wird nicht auf 0,30 angehoben.
    """
    if wert is None:
        return None
    if wert <= 0.0:
        return 0.0
    for grenze, ersatz in BAENDER:
        if wert < grenze:
            return ersatz
    return BAENDER[-1][1]


def stufe_fuer_attribut(brawler, key):
    """Auf welcher Stufe steht das, was wir ueber diese Eigenschaft wissen?"""
    from drafter.services import mechanik as mechanik_dienst

    if mechanik_dienst.sagt_etwas_zu(brawler, key):
        return MECHANIK if mechanik_dienst.ist_objektiv(key) else FACHQUELLE
    if brawler.bekannt(key):
        return DEMO if brawler.source == Datenquelle.DEMO else FACHQUELLE
    return UNBEKANNT


def wert_mit_stufe(brawler, key):
    """(wert, stufe) - der belastbarste verfuegbare Wert, oder (None, UNBEKANNT).

    Reihenfolge ist die Rangfolge oben. Eine Demo-Zahl kommt nur zum
    Zug, wenn keine bessere Quelle etwas sagt - und dann gebaendert.
    """
    from drafter.services import mechanik as mechanik_dienst

    aus_mechanik = mechanik_dienst.attributwert(brawler, key)
    if aus_mechanik is not None:
        return aus_mechanik, (MECHANIK if mechanik_dienst.ist_objektiv(key)
                              else FACHQUELLE)
    if brawler.bekannt(key):
        roh = brawler.wert(key)
        if brawler.source == Datenquelle.DEMO:
            return band(roh), DEMO
        return roh, FACHQUELLE
    return None, UNBEKANNT
