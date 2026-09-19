"""Wie gut ein Brawler zu Map und Modus passt.

Die Rechnung ist ein gewichtetes Skalarprodukt: Anforderung mal Koennen,
summiert ueber das gemeinsame Vokabular, geteilt durch die Summe der
Anforderungen. Ergebnis 0-1 - "wie viel von dem, was hier zaehlt, bringt
er mit".

Die Normalisierung danach ist **feldrelativ** (z-Wert ueber alle
Brawler), nicht absolut. Grund: der Rohwert haengt davon ab, wie viele
Anforderungen eine Map stellt. Eine Map mit fuenf scharfen Anforderungen
erzeugt niedrigere Rohwerte als eine mit zwei - ohne dass die Brawler
dort schlechter passen. Erst der Vergleich innerhalb derselben Map macht
die Zahl aussagekraeftig.
"""

from drafter import attributes as attr
from drafter import config
from drafter.services import objective, quellen, rollenwissen
from drafter.services.scoring import Grund, Komponente, klemme, z_werte


def roh_passung(brawler, anforderungen):
    """0-1: Anteil der Map-Anforderungen, den dieser Brawler erfuellt."""
    gewicht = sum(anforderungen.values())
    if gewicht <= 0:
        return 0.5
    erfuellt = sum(w * brawler.wert(k) for k, w in anforderungen.items())
    return erfuellt / gewicht


def komponenten_fuer_pool(kandidaten, anforderungen, brawl_map=None,
                          raum=None, patch=None):
    """Map-Fit fuer alle Kandidaten auf einmal.

    Einmal fuer das ganze Feld, weil die Normalisierung das ganze Feld
    braucht - einzeln waere sie nicht berechenbar.

    Die Komponente hat seit dem 2026-09-18 **zwei Haelften**:

      allgemein  - passt sein Koennen zu dem, was hier gefordert ist?
                   (Attribute, sonst Rolle - wie bisher)
      objective  - ist er im ZIEL dieses Modus messbar besser oder
                   schlechter als sonst? (services/objective.py)

    Warum beide: auf Safe Zone stand BROCK mit +17 Punkten auf Platz 1,
    weil sein gepflegtes Profil perfekt zum Anforderungsvektor passt -
    waehrend 221 gemessene Partien auf dieser Map 40,7 % Siegquote
    zeigten. Ein Profil konnte einen Modus-Fit behaupten, dem hunderte
    Partien widersprachen, und nichts im Modell konnte antworten.

    Eine fehlende Haelfte wird NICHT hochgerechnet: sie zaehlt 0 und
    zieht den Wert damit zur Mitte - dieselbe Regel wie im Gesamtscore.
    Wer nur die eine Haelfte belegt hat, behauptet auch nur die eine.
    """
    # Nur ueber Brawler mit Profil: ohne Eigenschaften ist die Passung
    # unbekannt, nicht 0 - und ein Feld voller Nullen wuerde ausserdem
    # die z-Werte aller anderen verschieben.
    # Mit gepflegten Zielaspekten zaehlt der BESTE erfuellte statt der
    # flachen Summe ueber alles: ein Modus verlangt verschiedene Dinge,
    # und niemand muss sie alle koennen (config.MODUS_ZIELASPEKTE). Ohne
    # Aspekte bleibt es beim Skalarprodukt.
    aspekt_tabelle = objective.aspekte(brawl_map.game_mode if brawl_map else None)
    roh, aspekt_je_id = {}, {}
    for b in kandidaten:
        if not b.hat_profil:
            continue
        if aspekt_tabelle:
            erfuellung = objective.aspekt_erfuellung(b, aspekt_tabelle)
            name, wert = objective.bester_aspekt(erfuellung)
            if name is not None:
                roh[b.id] = wert
                aspekt_je_id[b.id] = (name, erfuellung)
                continue
        roh[b.id] = roh_passung(b, anforderungen)
    z = z_werte(roh)

    # Ohne Profil, aber mit gepflegter Draft-Rolle: die Rolle sagt, WELCHE
    # Anforderungen der Map sie ueberhaupt beruehrt - das Gewicht steht in
    # der Map, nicht im Brawler. Eigenes Bezugsfeld, ebenfalls bei 0
    # zentriert und gedeckelt (services/rollenwissen.py).
    roh_rolle = {}
    for b in kandidaten:
        if b.hat_profil:
            continue
        anteil = rollenwissen.anforderungsdeckung(b, anforderungen)
        if anteil is not None:
            roh_rolle[b.id] = anteil
    z_rolle = rollenwissen.rollen_z(roh_rolle)

    objektiv = (objective.fuer_pool(kandidaten, raum, anforderungen, patch,
                                    modus=brawl_map.game_mode if brawl_map else None)
                if raum is not None else {})

    # Welche Eigenschaften praegen diese Map? Nur darueber wird begruendet -
    # "passt gut zur Map" ohne Grund ist keine Erklaerung.
    wichtigste = sorted(anforderungen.items(), key=lambda p: -p[1])[:3]

    ergebnis = {}
    for b in kandidaten:
        komp = Komponente(key=config.K_MAP_MODE)

        # --- Haelfte 1: passt sein Koennen hierher? -------------------
        if b.hat_profil:
            allgemein, a_quelle = z.get(b.id, 0.0), quellen.PROFILE
        elif b.id in z_rolle:
            allgemein, a_quelle = z_rolle[b.id], quellen.FACHWISSEN
        else:
            allgemein, a_quelle = None, None

        # --- Haelfte 2: was sagt die Messung ueber diesen Modus? ------
        auskunft = objektiv.get(b.id)
        obj = auskunft.wert if auskunft is not None and auskunft.verfuegbar else None

        if allgemein is None and obj is None:
            komp.verfuegbar = False
            ergebnis[b.id] = komp
            continue

        komp.wert = klemme(
            config.MAP_FIT_ANTEIL_ALLGEMEIN * (allgemein or 0.0)
            + config.MAP_FIT_ANTEIL_OBJECTIVE * (obj or 0.0)
        )
        komp.quelle = quellen.schwaechste(
            [q for q in (a_quelle, auskunft.quelle if obj is not None else None) if q]
        )
        komp.objective = auskunft

        # --- Begruendung: erst der Beleg, dann die Eigenschaft --------
        if auskunft is not None and auskunft.verfuegbar and auskunft.text:
            komp.gruende.append(Grund(
                text=auskunft.text, positiv=auskunft.wert >= 0,
                staerke=0.5 + 0.3 * abs(auskunft.wert),
                quelle="daten" if auskunft.quelle == objective.MESSUNG else "fachquelle",
            ))
        if b.hat_profil and allgemein is not None:
            name, _erfuellung = aspekt_je_id.get(b.id, (None, {}))
            if name and allgemein > 0.15:
                komp.gruende.append(Grund(
                    text=f"erfüllt hier vor allem: {name}",
                    positiv=True, staerke=0.5 + allgemein * 0.2,
                ))
            if allgemein > 0.15:
                treffer = [
                    (k, w) for k, w in wichtigste if w > 0.3 and b.wert(k) >= 0.6
                ]
                for k, w in treffer[:2]:
                    label = attr.EIGENSCHAFT_NACH_KEY[k].label
                    ort = brawl_map.name if brawl_map else "diesem Modus"
                    komp.gruende.append(Grund(
                        text=f"{label} zählt auf {ort} viel - genau seine Stärke",
                        positiv=True, staerke=0.6 + w * 0.3,
                    ))
            elif allgemein < -0.25:
                fehlend = [
                    (k, w) for k, w in wichtigste if w > 0.4 and b.wert(k) < 0.35
                ]
                for k, w in fehlend[:1]:
                    komp.gruende.append(Grund(
                        text=f"bringt kaum {attr.EIGENSCHAFT_NACH_KEY[k].label},"
                             " was hier wichtig wäre",
                        positiv=False, staerke=0.5 + w * 0.2,
                    ))
        elif allgemein is not None and not komp.gruende:
            richtung = "passt zu" if allgemein >= 0 else "passt wenig zu"
            komp.gruende.append(Grund(
                text=f"{b.draft_rolle_label} {richtung} dem, was hier verlangt wird"
                     " (Rolle, kein Profil)",
                positiv=allgemein >= 0, staerke=0.35, quelle="fachquelle",
            ))
        ergebnis[b.id] = komp
    return ergebnis
