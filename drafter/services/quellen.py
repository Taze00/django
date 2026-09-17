"""Welche Quelle gilt fuer eine Komponente - an genau einer Stelle.

Prioritaet je Komponente (nicht je Brawler):

    1. genug Messung  (Stichprobe >= CONFIDENCE_VOLL_AB)  -> Measured
    2. wenig Messung  (> 0 Spiele)                         -> Measured + Prior
    3. keine Messung, gepflegter Wert vorhanden            -> Profile
    4. weder noch                                          -> Unknown

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
"""

from dataclasses import dataclass

from drafter import config

MEASURED = "Measured"
MEASURED_PRIOR = "Measured + Prior"
PROFILE = "Profile"
UNKNOWN = "Unknown"

# Rangfolge fuer zusammengesetzte Komponenten (Counter ueber drei Gegner):
# es gilt die schwaechste beteiligte Quelle. "Measured" nur, wenn ALLES
# gemessen ist - sonst taeuschte ein gemessenes Paar Sicherheit fuer die
# ganze Komponente vor.
_RANG = {MEASURED: 3, MEASURED_PRIOR: 2, PROFILE: 1, UNKNOWN: 0}


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


@dataclass(frozen=True)
class MetaAuskunft:
    rate: float = None          # 0-1, None = unbekannt
    quelle: str = UNKNOWN
    games: int = 0              # gemessene Spiele (0 bei Profile)
    confidence: float = 0.0
    record: object = None       # die Zeile, deren Patch/Kontext gilt

    @property
    def staerke(self):
        return max(-1.0, min(1.0, (self.rate - 0.5) * 2)) if self.rate is not None else None

    @property
    def is_demo(self):
        return self.quelle == PROFILE


def meta_aufloesen(messung, prior):
    # Ohne getrennte Prior-Quelle (reiner Demo-Provider, synthetische
    # Testdaten) steht der gepflegte Wert im Messplatz - dann ist ER der Prior.
    if prior is None and messung is not None and not _gemessen(messung):
        messung, prior = None, messung
    gem = messung if _gemessen(messung) and messung.adjusted_rate is not None else None
    pri = prior if prior is not None and prior.adjusted_rate is not None else None
    rate, quelle = mischen(
        gem.adjusted_rate if gem else None,
        pri.adjusted_rate if pri else None,
        _n(gem), config.PRIOR_STAERKE,
    )
    if quelle == UNKNOWN:
        return MetaAuskunft()
    if quelle == PROFILE:
        return MetaAuskunft(rate, quelle, 0, pri.confidence, pri)
    confidence = gem.confidence
    if quelle == MEASURED_PRIOR and pri is not None:
        # Mischung: nie sicherer als die sicherere der beiden Quellen.
        confidence = max(gem.confidence, pri.confidence)
    return MetaAuskunft(rate, quelle, gem.games, confidence, gem)
