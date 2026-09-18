"""CURRENT STRENGTH als Score-Komponente.

Wie gut laeuft ein Brawler derzeit **messbar**. Die Schaetzung selbst
steht in services/staerke.py (Beta-Binomial ueber die Ebenen global ->
Modus -> Map); hier wird sie nur zur Komponente gemacht.

Drei Trennungen, die diese Datei einhaelt:

* **Wissen ist keine Staerke.** Was ein Brawler kann (Attribute, Rolle,
  Faehigkeiten), fliesst hier NICHT ein. Es steht in Map-Fit, Counter und
  Teambedarf - also im Draft-Fit, nicht in der Form.
* **Unbekannt ist nicht 50 %.** Ohne Messung und ohne gepflegten Wert ist
  die Komponente `verfuegbar=False` und faellt aus dem Score. Frueher
  lieferte sie 0 mit niedriger Confidence - das zog jeden unbekannten
  Brawler still zur Mitte.
* **Unsicherheit steckt nicht im Wert.** Kleine Stichprobe heisst: der
  Schaetzwert liegt naeher am Prior UND die Confidence ist niedrig. Der
  Wert wird dafuer nicht zusaetzlich gestutzt.

Nach einer Balanceaenderung zaehlen alte Zahlen weniger: `gewicht` zieht
Wert und Sicherheit Richtung neutral, statt eine Rate zu behaupten, die
fuer eine andere Fassung des Brawlers gemessen wurde.
"""

from drafter import config
from drafter.services import quellen, staerke
from drafter.services.scoring import Grund, Komponente
from drafter.services.patch_weighting import statistik_gewicht


def komponenten_fuer_pool(kandidaten, raum, patch=None):
    # Erst alle Schaetzungen, dann das Feld: der Score-Wert ist die Lage
    # IM FELD, nicht der Abstand zu einer festen 50-%-Marke. Warum, steht
    # bei config.STAERKE_FELD_K.
    auskuenfte = {b.id: raum.staerke(b) for b in kandidaten}
    feld = staerke.Feld.aus([a.rate for a in auskuenfte.values() if a.bekannt])

    ergebnis = {}
    for b in kandidaten:
        komp = Komponente(key=config.K_META)
        komp.feld = feld
        auskunft = auskuenfte[b.id]
        # Weder Messung noch gepflegter Wert: keine Auskunft, nicht "50 %".
        if not auskunft.bekannt:
            komp.verfuegbar = False
            komp.confidence = 0.0
            komp.quelle = quellen.UNKNOWN
            komp.staerke = auskunft
            ergebnis[b.id] = komp
            continue

        gewicht = (statistik_gewicht(auskunft.record, b, patch)
                   if auskunft.record is not None else 1.0)
        komp.wert = staerke.feldwert(auskunft, feld) * gewicht
        komp.confidence = auskunft.confidence * gewicht
        komp.quelle = auskunft.quelle
        komp.staerke = auskunft

        rate = auskunft.rate
        grund_quelle = "demo" if auskunft.quelle == quellen.PROFILE else "daten"
        # Bei gemessenen Daten die Stichprobe mitnennen: "58 %" aus 40
        # Spielen und aus 40 000 Spielen sind verschiedene Aussagen.
        umfang = f", {auskunft.spiele} Spiele" if auskunft.spiele else ""
        if auskunft.quelle == quellen.MEASURED_PRIOR and raum.stat_prior(b):
            umfang += ", mit Profil gemischt"
        lage = komp.wert
        if lage >= 0.25 and gewicht > 0.5:
            komp.gruende.append(Grund(
                text=f"läuft derzeit besser als das Feld ({rate:.0%} Siegquote{umfang})",
                positiv=True, staerke=0.5 + 0.2 * lage, quelle=grund_quelle,
            ))
        elif lage <= -0.25 and gewicht > 0.5:
            komp.gruende.append(Grund(
                text=f"läuft derzeit schlechter als das Feld ({rate:.0%} Siegquote{umfang})",
                positiv=False, staerke=0.5 + 0.2 * abs(lage), quelle=grund_quelle,
            ))
        elif rate >= 0.55 and gewicht > 0.5:
            komp.gruende.append(Grund(
                text=f"läuft im aktuellen Patch stark ({rate:.0%} Siegquote{umfang})",
                positiv=True, staerke=0.55, quelle=grund_quelle,
            ))
        elif rate <= 0.45 and gewicht > 0.5:
            komp.gruende.append(Grund(
                text=f"läuft derzeit schwach ({rate:.0%} Siegquote{umfang})",
                positiv=False, staerke=0.5, quelle=grund_quelle,
            ))
        if gewicht < 0.5:
            komp.gruende.append(Grund(
                text="wurde zuletzt verändert - ältere Zahlen zählen hier wenig",
                positiv=False, staerke=0.3,
            ))
        # Selten gewaehlt: die Rate stammt dann von den wenigen, die ihn
        # spielen. Sie wird nicht abgewertet - nur ihre Reichweite.
        if auskunft.bias >= 0.5 and auskunft.spiele:
            komp.gruende.append(Grund(
                text=(f"wird selten gewählt ({auskunft.pickrate:.1%} Pickrate)"
                      " - die Siegquote sagt wenig über das ganze Feld"
                      if auskunft.pickrate
                      else "wird selten gewählt - die Siegquote ist wenig übertragbar"),
                positiv=False, staerke=0.25, quelle="daten",
            ))
        ergebnis[b.id] = komp
    return ergebnis
