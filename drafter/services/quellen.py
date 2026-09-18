"""Welche Quelle gilt fuer eine Komponente - an genau einer Stelle.

Prioritaet je Komponente (nicht je Brawler):

    1. genug Messung  (Stichprobe >= CONFIDENCE_VOLL_AB)  -> Measured
    2. wenig Messung  (> 0 Spiele)                         -> Measured + Prior
    3. keine Messung, gepflegter Wert vorhanden            -> Profile
    4. nur Rolle/Faehigkeiten der Fachquelle               -> Fachquelle
    5. weder noch                                          -> Unknown

Stufe 4 liefert keine Zahl, sondern eine Richtung: die Rolle sagt, WORUM
es bei dem Brawler geht, der Betrag kommt aus Map-Anforderung oder
Team-Luecke. Details in services/rollenwissen.py.

Stufe 2 mischt, statt zu ersetzen. Die Messung ist in der Aggregation
schon Bayes-geglaettet - aber zum NEUTRALEN Erwartungswert (50 % bzw.
log5), nicht zum gepflegten Wert. Gibt es einen gepflegten Wert, wird er
deshalb hier als Prior dazugemischt:

    wert = w * gemessen + (1 - w) * gepflegt,   w = n / (n + k)

mit n = gewichtete Stichprobe und k = PRIOR_STAERKE (Einzelbrawler) bzw.
PAAR_PRIOR_STAERKE (Paare) - dieselben Staerken wie in der Aggregation.
Die gemessene Seite ist damit zweimal zur Mitte gezogen (einmal beim
Aggregieren, einmal hier). Das ist gewollt konservativ: bei 35 Spielen
zaehlt die Messung ~23 %, das gepflegte Profil ~77 %.

Ohne gepflegten Wert bleibt in Stufe 2 die geglaettete Messung allein
stehen - der Prior ist dann der neutrale aus der Aggregation.

Nichts hier erfindet einen Wert: gemischt wird nur, was vorliegt.

Fuer die **Meta-Staerke eines Brawlers** gilt diese Mischung nicht mehr:
sie wird in services/staerke.py als Beta-Binomial-Posterior ueber die
Ebenen global -> Modus -> Map geschaetzt. `mischen()` bleibt fuer die
Paarwerte (Counter, Synergie), wo es nur eine Ebene gibt.
"""

from drafter import config

MEASURED = "Measured"
MEASURED_PRIOR = "Measured + Prior"
PROFILE = "Profile"
# Gepflegtes Fachwissen ohne Zahlen: Draft-Rolle und Faehigkeiten aus der
# Role-&-Ability-Map. Schwaecher als ein Profil, weil es nur die Richtung
# kennt - aber ungleich besser als Unknown, das die Komponente ganz
# ausfallen laesst. Siehe services/rollenwissen.py.
FACHWISSEN = "Fachquelle"
UNKNOWN = "Unknown"

# Rangfolge fuer zusammengesetzte Komponenten (Counter ueber drei Gegner):
# es gilt die schwaechste beteiligte Quelle. "Measured" nur, wenn ALLES
# gemessen ist - sonst taeuschte ein gemessenes Paar Sicherheit fuer die
# ganze Komponente vor.
_RANG = {MEASURED: 4, MEASURED_PRIOR: 3, PROFILE: 2, FACHWISSEN: 1, UNKNOWN: 0}


def schwaechste(quellen):
    quellen = [q for q in quellen if q and q != UNKNOWN]
    if not quellen:
        return UNKNOWN
    return min(quellen, key=lambda q: _RANG[q])


def _n(record):
    if record is None:
        return 0.0
    return float(record.sample_size or record.games or 0)


def _gemessen(record):
    return record is not None and record.ist_gemessen and (record.games or 0) > 0


def mischen(gemessen, gepflegt, n, k):
    """(wert, quelle) aus einem gemessenen und einem gepflegten Wert.

    Beide Werte duerfen None sein. Rechnet nur, stuft ein - kennt keine
    Modelle.
    """
    if gemessen is not None and n >= config.CONFIDENCE_VOLL_AB:
        return gemessen, MEASURED
    if gemessen is not None and n > 0:
        if gepflegt is None:
            return gemessen, MEASURED_PRIOR
        w = n / (n + k)
        return w * gemessen + (1.0 - w) * gepflegt, MEASURED_PRIOR
    if gepflegt is not None:
        return gepflegt, PROFILE
    return None, UNKNOWN
