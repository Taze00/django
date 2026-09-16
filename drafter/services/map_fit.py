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

from drafter import config
from drafter.services.scoring import Grund, Komponente, z_werte


def roh_passung(brawler, anforderungen):
    """0-1: Anteil der Map-Anforderungen, den dieser Brawler erfuellt."""
    gewicht = sum(anforderungen.values())
    if gewicht <= 0:
        return 0.5
    erfuellt = sum(w * brawler.wert(k) for k, w in anforderungen.items())
    return erfuellt / gewicht


def komponenten_fuer_pool(kandidaten, anforderungen, brawl_map=None):
    """Map-Fit fuer alle Kandidaten auf einmal.

    Einmal fuer das ganze Feld, weil die Normalisierung das ganze Feld
    braucht - einzeln waere sie nicht berechenbar.
    """
    # Nur ueber Brawler mit Profil: ohne Eigenschaften ist die Passung
    # unbekannt, nicht 0 - und ein Feld voller Nullen wuerde ausserdem
    # die z-Werte aller anderen verschieben.
    roh = {b.id: roh_passung(b, anforderungen) for b in kandidaten if b.hat_profil}
    z = z_werte(roh)

    # Welche Eigenschaften praegen diese Map? Nur darueber wird begruendet -
    # "passt gut zur Map" ohne Grund ist keine Erklaerung.
    wichtigste = sorted(anforderungen.items(), key=lambda p: -p[1])[:3]

    ergebnis = {}
    for b in kandidaten:
        if not b.hat_profil:
            ergebnis[b.id] = Komponente(key=config.K_MAP_MODE, verfuegbar=False)
            continue
        komp = Komponente(key=config.K_MAP_MODE, wert=z.get(b.id, 0.0))
        if komp.wert > 0.15:
            treffer = [
                (k, w) for k, w in wichtigste if w > 0.3 and b.wert(k) >= 0.6
            ]
            from drafter import attributes as attr
            for k, w in treffer[:2]:
                label = attr.EIGENSCHAFT_NACH_KEY[k].label
                ort = brawl_map.name if brawl_map else "diesem Modus"
                komp.gruende.append(Grund(
                    text=f"{label} zählt auf {ort} viel - genau seine Stärke",
                    positiv=True, staerke=0.6 + w * 0.3,
                ))
            if not treffer:
                komp.gruende.append(Grund(
                    text="passt insgesamt gut zu den Anforderungen dieser Map",
                    positiv=True, staerke=0.5,
                ))
        elif komp.wert < -0.25:
            fehlend = [
                (k, w) for k, w in wichtigste if w > 0.4 and b.wert(k) < 0.35
            ]
            from drafter import attributes as attr
            for k, w in fehlend[:1]:
                komp.gruende.append(Grund(
                    text=f"bringt kaum {attr.EIGENSCHAFT_NACH_KEY[k].label}, was hier wichtig wäre",
                    positiv=False, staerke=0.5 + w * 0.3,
                ))
        ergebnis[b.id] = komp
    return ergebnis
