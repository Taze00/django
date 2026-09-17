"""Meta-Staerke: wie gut laeuft ein Brawler derzeit ueberhaupt.

Bezieht sich auf gemessene bzw. gepflegte Statistiken (`BrawlerStat`) -
nicht auf Attribute. Die Attribute sagen, was ein Brawler *kann*; die
Meta sagt, was davon im aktuellen Patch *funktioniert*.

Quelle je Brawler nach services/quellen.py: Messung, Messung mit
gepflegtem Prior, gepflegter Wert. Fehlt beides, ist die Komponente
nicht verfuegbar und faellt aus dem Score heraus. Frueher lieferte sie 0 ("durchschnittlich") mit
niedriger Confidence - das zog einen unbekannten Brawler still zur Mitte.
"""

from drafter import config
from drafter.services import quellen
from drafter.services.scoring import Grund, Komponente
from drafter.services.patch_weighting import statistik_gewicht


def komponenten_fuer_pool(kandidaten, raum, patch=None):
    ergebnis = {}
    for b in kandidaten:
        komp = Komponente(key=config.K_META)
        auskunft = raum.meta(b)
        # Weder Messung noch gepflegter Wert: keine Auskunft, nicht "50 %".
        if auskunft.quelle == quellen.UNKNOWN:
            komp.verfuegbar = False
            komp.confidence = 0.0
            komp.quelle = quellen.UNKNOWN
            ergebnis[b.id] = komp
            continue

        gewicht = statistik_gewicht(auskunft.record, b, patch)
        komp.wert = auskunft.staerke * gewicht
        komp.confidence = auskunft.confidence * gewicht
        komp.quelle = auskunft.quelle

        rate = auskunft.rate
        grund_quelle = "demo" if auskunft.quelle == quellen.PROFILE else "daten"
        # Bei gemessenen Daten die Stichprobe mitnennen: "58 %" aus 40
        # Spielen und aus 40 000 Spielen sind verschiedene Aussagen.
        umfang = f", {auskunft.games} Spiele" if auskunft.games else ""
        if auskunft.quelle == quellen.MEASURED_PRIOR:
            umfang += ", mit Profil gemischt" if raum.stat_prior(b) else ""
        if rate >= 0.55 and gewicht > 0.5:
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
        ergebnis[b.id] = komp
    return ergebnis
