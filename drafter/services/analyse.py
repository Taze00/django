# -*- coding: utf-8 -*-
"""Die vollstaendige Bewertung EINES Brawlers sichtbar machen.

Dieses Modul rechnet **nichts Eigenes**. Es holt die Bewertung, die die
Engine ohnehin erzeugt, und legt sie offen - auch fuer Brawler, die es
nie in die Vorschlagsliste schaffen. Fuer die Fehlersuche ist genau das
der interessante Fall: warum steht EDGAR auf Platz 71?

Zwei Dinge kommen zur normalen Empfehlung dazu, und beide sind
Ablesungen, keine Rechnungen:

1. **Der Rang im ganzen Feld.** Er faellt als Listenindex aus demselben
   Lauf ab (`DraftEngine.analyse`).

2. **Die Paarbeitraege.** Counter- und Synergie-Komponente mitteln ueber
   die Gegner bzw. Mitspieler; im Score steht am Ende eine Zahl. Hier
   stehen die Einzelwerte daneben - geholt mit `counters.vorteil` und
   `synergies.paar`, also mit genau den Funktionen, aus denen die
   Komponenten ihren Mittelwert bilden. Es gibt keinen zweiten Rechenweg.

**Keine Rueckwirkung.** Nichts hier veraendert einen Score, eine
Reihenfolge oder eine Komponente. Wer das aendert, macht aus einem
Messgeraet einen Teil der Maschine, die es messen soll.
"""

from drafter.services import counters, synergies


def _paarzeile(gegenueber, wert, grund, quelle, sicherheit, heuristisch=False):
    return {
        "slug": gegenueber.slug,
        "name": gegenueber.name,
        # Der Rohwert des Paares in [-1, +1] - so, wie die Komponente ihn
        # mittelt.
        "wert": round(wert, 3),
        # Derselbe Wert in Anzeigepunkten, damit er neben den Beitraegen
        # der Aufschluesselung lesbar ist (dort gilt Beitrag = Wert x 50).
        "punkte": round(wert * 50, 1),
        "quelle": quelle or "Unknown",
        "bekannt": quelle is not None,
        "heuristisch": bool(heuristisch),
        "sicherheit": round(sicherheit, 2),
        "grund": grund or "",
    }


def paarbeitraege(brawler, ctx, raum):
    """Counter je Gegner und Synergie je Mitspieler - einzeln aufgefuehrt.

    Ein Paar ohne bekannte Datenlage steht mit `bekannt: False` drin,
    statt zu fehlen: "darueber wissen wir nichts" ist eine Aussage, eine
    Luecke in der Tabelle waere keine.
    """
    counter = []
    for gegner in ctx.enemy_picks:
        wert, grund, quelle = counters.vorteil(brawler, gegner, raum)
        counter.append(_paarzeile(
            gegner, wert, grund, quelle,
            counters.paar_sicherheit(brawler, gegner, raum),
            heuristisch=counters.ist_heuristisch(brawler, gegner, raum),
        ))

    synergie = []
    for mitspieler in ctx.own_picks:
        wert, grund, quelle = synergies.paar(brawler, mitspieler, raum)
        synergie.append(_paarzeile(
            mitspieler, wert, grund, quelle,
            synergies.paar_sicherheit(brawler, mitspieler, raum),
            heuristisch=(raum.synergie(brawler, mitspieler) is None
                         and raum.synergie_prior(brawler, mitspieler) is None),
        ))

    return {"counter": counter, "synergie": synergie}


def als_dict(empfehlung, rang, anzahl, ctx, raum):
    """Die Empfehlung als Analyse-Antwort: alles, was sie ohnehin traegt.

    Der Kern ist unveraendert `Empfehlung.als_dict(ausfuehrlich=True)` -
    dieselben Felder, die auch die Vorschlagsliste liefert. Ergaenzt sind
    nur Rang, Feldgroesse und die Paarbeitraege.
    """
    daten = empfehlung.als_dict(ausfuehrlich=True)
    daten.update({
        "rang": rang,
        "kandidaten": anzahl,
        "matchups": paarbeitraege(empfehlung.brawler, ctx, raum),
        # Mit welchen Zahlen gerechnet wurde. "seit Patch" ist das
        # bevorzugte Fenster; faellt es aus, muss das dastehen, statt
        # dass 7-Tage-Werte als Patchstand durchgehen.
        "statistikfenster": raum.fenster_lage(),
    })
    return daten
