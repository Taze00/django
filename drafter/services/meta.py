"""Meta-Staerke: wie gut laeuft ein Brawler derzeit ueberhaupt.

Bezieht sich auf gemessene bzw. gepflegte Statistiken (`BrawlerStat`) -
nicht auf Attribute. Die Attribute sagen, was ein Brawler *kann*; die
Meta sagt, was davon im aktuellen Patch *funktioniert*.

Fehlt jede Statistik, liefert die Komponente 0 und eine niedrige
Confidence. Das ist der ehrliche Zustand "wir wissen es nicht" - und
nicht etwa "durchschnittlich gut".
"""

from drafter import config
from drafter.services.scoring import Grund, Komponente
from drafter.services.patch_weighting import statistik_gewicht


def komponenten_fuer_pool(kandidaten, raum, patch=None):
    ergebnis = {}
    for b in kandidaten:
        komp = Komponente(key=config.K_META)
        stat = raum.stat(b)
        if not stat:
            komp.confidence = 0.1
            ergebnis[b.id] = komp
            continue

        gewicht = statistik_gewicht(stat, b, patch)
        komp.wert = stat.staerke * gewicht
        komp.confidence = stat.confidence * gewicht

        if stat.win_rate >= 0.55 and gewicht > 0.5:
            komp.gruende.append(Grund(
                text=f"läuft im aktuellen Patch stark ({stat.win_rate:.0%} Siegquote)",
                positiv=True, staerke=0.55, quelle="demo" if stat.is_demo else "daten",
            ))
        elif stat.win_rate <= 0.45 and gewicht > 0.5:
            komp.gruende.append(Grund(
                text=f"läuft derzeit schwach ({stat.win_rate:.0%} Siegquote)",
                positiv=False, staerke=0.5, quelle="demo" if stat.is_demo else "daten",
            ))
        if gewicht < 0.5:
            komp.gruende.append(Grund(
                text="wurde zuletzt verändert - ältere Zahlen zählen hier wenig",
                positiv=False, staerke=0.3,
            ))
        ergebnis[b.id] = komp
    return ergebnis
