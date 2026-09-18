# -*- coding: utf-8 -*-
"""CURRENT STRENGTH - wie gut laeuft ein Brawler messbar gerade.

Die einzige empirische Groesse der Engine. Profilwissen kommt hier NIE
hinein: was ein Brawler kann, sagt nichts darueber, wie er laeuft.

Geschaetzt wird als **Beta-Binomial-Posterior**:

    mittel = (siege + a) / (spiele + a + b)
    sd     = sqrt(mittel * (1 - mittel) / (spiele + a + b + 1))

Kleine Stichproben ziehen dadurch stark zum Prior, grosse ueberstimmen
ihn - stetig, ohne Schwelle. 1 Sieg aus 1 Spiel landet praktisch auf dem
Prior, 1100 aus 2000 praktisch auf der Messung.

**Hierarchie statt Spezifitaet.** Frueher gewann die spezifischste Zeile,
egal wie duenn: eine Map-Zeile mit 4 Partien verdraengte eine globale mit
44. Jetzt zaehlen alle Ebenen zusammen, die groeberen mit Abschlag:

    effektive Spiele = 1.0 * Map + 0.5 * (nur Modus) + 0.25 * (nur global)

Der Abschlag richtet sich nach dem Abstand zur FEINSTEN vorhandenen
Ebene - ohne Map-Zeile zaehlt der Modus voll. Gezaehlt wird jede Partie
genau einmal: die Ebenen sind ineinander verschachtelt (die globale Zeile
enthaelt die Map-Partien), deshalb geht nur der Rest der groeberen Ebene
ein. Eine duenne Map-Zeile verschiebt den Wert damit wenig und senkt die
Sicherheit nie - mehr Daten koennen nicht weniger wissen.

Gerechnet wird auf Rohzaehlungen, weil die Aggregation ihre eigene
Prior-Kette schon gefahren hat (`aggregator._brawler_prior`) -
`adjusted_rate` waere doppelt geschrumpft.

**Unsicherheit steht daneben, nicht im Wert.** Die Sicherheit kommt aus
der Streuung des Posteriors (wie viel Information gegenueber dem reinen
Prior gewonnen wurde) und wird zusaetzlich gesenkt, wenn ein Brawler
selten gespielt wird: eine Rate aus 1 % Pickrate beschreibt die wenigen,
die ihn spielen, nicht das Feld. Der Schaetzwert selbst bleibt unberuehrt -
"selten" heisst nicht "schlecht".
"""

import math
from dataclasses import dataclass, field

from drafter import config
from drafter.services.quellen import MEASURED, MEASURED_PRIOR, PROFILE, UNKNOWN

GLOBAL, MODUS, MAP = "global", "modus", "map"
EBENEN = (GLOBAL, MODUS, MAP)

__all__ = ["Staerke", "schaetze", "posterior", "prior_sd", "wilson",
           "paar_confidence", "selection_bias", "GLOBAL", "MODUS", "MAP",
           "MEASURED", "MEASURED_PRIOR", "PROFILE", "UNKNOWN"]


def posterior(spiele, siege, prior_rate=0.5, prior_staerke=None):
    """(Mittel, Standardabweichung) eines Beta-Binomial-Posteriors."""
    prior_staerke = (config.STAERKE_PRIOR_GLOBAL if prior_staerke is None
                     else float(prior_staerke))
    a = prior_rate * prior_staerke
    b = (1.0 - prior_rate) * prior_staerke
    a += max(0.0, siege)
    b += max(0.0, spiele - siege)
    gesamt = a + b
    mittel = a / gesamt if gesamt > 0 else prior_rate
    sd = math.sqrt(max(0.0, mittel * (1.0 - mittel) / (gesamt + 1.0)))
    return mittel, sd


def prior_sd(prior_rate=0.5, prior_staerke=None):
    """Streuung, die allein aus dem Prior kommt - die Referenz fuer 'nichts gelernt'."""
    return posterior(0, 0, prior_rate, prior_staerke)[1]


def wilson(spiele, siege, z=1.96):
    """Klassisches Wilson-Intervall - zur Kontrolle, nicht als Score."""
    if spiele <= 0:
        return (0.0, 1.0)
    p = siege / spiele
    mitte = (p + z * z / (2 * spiele)) / (1 + z * z / spiele)
    rand = z * math.sqrt(p * (1 - p) / spiele + z * z / (4 * spiele * spiele)) / (1 + z * z / spiele)
    return (max(0.0, mitte - rand), min(1.0, mitte + rand))


def selection_bias(pickrate, spiele):
    """0-1: wie stark die Rate nach Spezialisten riecht.

    Hoch, wenn ein Brawler selten gespielt wird UND die Stichprobe duenn
    ist. Beides zusammen: die Rate beschreibt dann die wenigen, die ihn
    ueberhaupt waehlen. Senkt nur die Sicherheit.
    """
    if pickrate is None or pickrate <= 0:
        return 1.0 if spiele < config.STAERKE_PRIOR_GLOBAL else 0.5
    selten = max(0.0, 1.0 - pickrate / config.STAERKE_PICKRATE_REFERENZ)
    duenn = config.STAERKE_PRIOR_GLOBAL / (config.STAERKE_PRIOR_GLOBAL + max(0.0, spiele))
    return max(0.0, min(1.0, selten * duenn))


@dataclass(frozen=True)
class Staerke:
    """Schaetzung samt Herkunft und Unsicherheit."""

    rate: float = None
    sd: float = 0.0
    n_effektiv: float = 0.0
    spiele: int = 0
    pickrate: float = None
    quelle: str = UNKNOWN
    ebene: str = ""
    beitraege: dict = field(default_factory=dict)   # ebene -> (spiele, rate)
    bias: float = 0.0
    record: object = None
    # Nur im Profile-Pfad: die Sicherheit, die die gepflegte Zeile selbst
    # angibt. Aus einer Schaetzung laesst sich keine Stichprobe ableiten.
    profil_confidence: float = None
    # Streuung, die allein aus dem verwendeten Prior kaeme - der
    # Nullpunkt der Confidence. Muss mitgefuehrt werden, weil der Prior
    # nicht immer die volle Staerke hat: gegen den vollen gemessen, waere
    # jede Schaetzung mit abgeschwaechtem Prior scheinbar "nichts gelernt".
    referenz_sd: float = None

    @property
    def bekannt(self):
        return self.rate is not None

    @property
    def wert(self):
        """Abweichung von 50 % in [-1, +1] - der Score-Vertrag der Engine."""
        if self.rate is None:
            return None
        return max(-1.0, min(1.0, (self.rate - 0.5) * 2))

    @property
    def confidence(self):
        """0-1 aus der Streuung des Posteriors, gedaempft durch Selection Bias.

        sd == prior_sd heisst "nichts dazugelernt" -> 0. Je kleiner die
        Streuung, desto mehr Information steckt in der Schaetzung.
        """
        if self.rate is None:
            return 0.0
        if self.profil_confidence is not None:
            return max(0.0, min(1.0, self.profil_confidence))
        referenz = self.referenz_sd if self.referenz_sd else prior_sd()
        gelernt = max(0.0, min(1.0, 1.0 - (self.sd / referenz))) if referenz else 0.0
        return max(0.0, gelernt * (1.0 - config.STAERKE_BIAS_MAX_ABZUG * self.bias))

    @property
    def intervall(self):
        """95-%-Bereich des Posteriors - fuer die Anzeige."""
        if self.rate is None:
            return None
        return (max(0.0, self.rate - 1.96 * self.sd), min(1.0, self.rate + 1.96 * self.sd))

    def als_dict(self):
        return {
            "rate": round(self.rate, 4) if self.rate is not None else None,
            "wert": round(self.wert, 4) if self.rate is not None else None,
            "sd": round(self.sd, 4),
            "n_effektiv": round(self.n_effektiv, 1),
            "spiele": self.spiele,
            "pickrate": self.pickrate,
            "selection_bias": round(self.bias, 3),
            "confidence": round(self.confidence, 3),
            "quelle": self.quelle,
            "ebene": self.ebene,
            # Was jede Ebene beigesteuert hat: Rohstichprobe, Rohrate,
            # Abschlag und die daraus effektiv gezaehlten Partien.
            "ebenen": {
                k: {
                    "spiele": b["spiele"],
                    "rate": round(b["rate"], 4) if b["rate"] is not None else None,
                    "gewicht": round(b["gewicht"], 3),
                    "effektive_spiele": round(b["effektive_spiele"], 1),
                }
                for k, b in self.beitraege.items()
            },
        }


def _zaehlung(record):
    """(spiele, siege) einer Statistikzeile - roh, nicht geglaettet."""
    if record is None:
        return 0.0, 0.0
    spiele = float(record.games or 0)
    if not spiele:
        return 0.0, 0.0
    if record.wins:
        return spiele, float(record.wins)
    rate = record.raw_rate if record.raw_rate is not None else record.adjusted_rate
    return (spiele, spiele * rate) if rate is not None else (0.0, 0.0)


def _rest(grob, fein):
    """Zaehlung der groeberen Ebene ohne die Partien der feineren.

    Die Ebenen sind verschachtelt: die globale Zeile enthaelt die
    Modus-Partien, die Modus-Zeile die der Map. Ohne diesen Abzug zaehlte
    dieselbe Partie zwei- oder dreifach.
    """
    spiele = max(0.0, grob[0] - fein[0])
    siege = min(max(0.0, grob[1] - fein[1]), spiele)
    return spiele, siege


def schaetze(zeilen, profil_rate=None, pickrate=None, profil_record=None,
             kontext_ebene=GLOBAL):
    """Staerke aus den Zeilen aller Ebenen.

    `zeilen` ist {"global": record|None, "modus": ..., "map": ...}.
    `kontext_ebene` ist die Frage, die gestellt wird: auf einer Map
    gefragt, zaehlen globale Partien nur ein Viertel - unabhaengig davon,
    ob es fuer diese Map ueberhaupt Zeilen gibt. Am Datenbestand
    festgemacht waere der Abschlag ruckartig: die erste Map-Partie wuerde
    rueckwirkend alle globalen abwerten und die Sicherheit einbrechen
    lassen.

    Der gepflegte Wert ist der Prior; ohne jede Messung gilt er allein
    (Profile), ohne beides ist nichts bekannt - nicht 50 %.
    """
    zeilen = {k: v for k, v in (zeilen or {}).items() if v is not None}
    gemessen = {}
    for ebene in EBENEN:
        zeile = zeilen.get(ebene)
        if zeile is None or zeile.is_demo or not (zeile.games or 0) > 0:
            continue
        spiele, siege = _zaehlung(zeile)
        if spiele > 0:
            gemessen[ebene] = (spiele, siege)

    if not gemessen:
        # Keine Messung: gepflegter Wert, falls vorhanden.
        if profil_rate is None:
            return Staerke()
        return Staerke(
            rate=profil_rate, sd=prior_sd(), quelle=PROFILE, ebene="profil",
            pickrate=pickrate, record=profil_record,
            profil_confidence=getattr(profil_record, "confidence", 0.0) or 0.0,
        )

    reihenfolge = [e for e in (MAP, MODUS, GLOBAL) if e in gemessen]
    feinste = reihenfolge[0]
    abstand = {MAP: 0, MODUS: 1, GLOBAL: 2}
    bezug = abstand.get(kontext_ebene, abstand[GLOBAL])
    stufen = {e: max(0, abstand[e] - bezug) for e in reihenfolge}

    obs_spiele = 0.0
    obs_siege = 0.0
    beitraege = {}
    vorheriger = (0.0, 0.0)
    for ebene in reihenfolge:                      # fein -> grob
        roh_spiele, roh_siege = gemessen[ebene]
        eigen_spiele, eigen_siege = _rest(gemessen[ebene], vorheriger)
        gewicht = config.STAERKE_EBENEN_ABSCHLAG ** stufen[ebene]
        obs_spiele += gewicht * eigen_spiele
        obs_siege += gewicht * eigen_siege
        beitraege[ebene] = {
            "spiele": int(roh_spiele),
            "rate": roh_siege / roh_spiele if roh_spiele else None,
            "gewicht": gewicht,
            "effektive_spiele": gewicht * eigen_spiele,
        }
        vorheriger = gemessen[ebene]

    # Der gepflegte Wert ist der Prior - aber er ist selbst eine GLOBALE
    # Aussage und zaehlt deshalb mit demselben Abschlag wie globale
    # Partien. Sonst ueberstand er auch 1500 gemessene Partien auf einer
    # Map noch mit einem Viertel Gewicht. Ohne gepflegten Wert bleibt der
    # neutrale Prior (50 %) in voller Staerke: je duenner die Datenlage,
    # desto mehr soll sie zur Mitte gezogen werden.
    if profil_rate is not None:
        prior_rate = profil_rate
        prior_staerke = config.STAERKE_PRIOR_GLOBAL * (
            config.STAERKE_EBENEN_ABSCHLAG ** max(0, abstand[GLOBAL] - bezug))
    else:
        prior_rate = config.PRIOR_RATE
        prior_staerke = config.STAERKE_PRIOR_GLOBAL
    rate, sd = posterior(obs_spiele, obs_siege, prior_rate=prior_rate,
                         prior_staerke=prior_staerke)
    referenz = prior_sd(prior_rate, prior_staerke)

    spiele_gesamt = int(max(n for n, _ in gemessen.values()))
    bias = selection_bias(pickrate, obs_spiele)
    genug = spiele_gesamt >= config.CONFIDENCE_VOLL_AB
    return Staerke(
        rate=rate, sd=sd, n_effektiv=obs_spiele, spiele=spiele_gesamt,
        pickrate=pickrate, bias=bias, ebene=feinste,
        quelle=MEASURED if genug else MEASURED_PRIOR,
        beitraege=beitraege, referenz_sd=referenz,
        record=zeilen.get(feinste),
    )


def paar_confidence(spiele, prior_staerke=None):
    """Sicherheit einer Paar-Aussage (Counter/Synergie) aus IHRER Stichprobe.

    Dieselbe Logik wie oben: wie viel Streuung gegenueber dem reinen Prior
    verschwunden ist. Ein Paar mit 3 Partien bekommt damit nicht mehr
    dieselbe Sicherheit wie eines mit 100 - frueher hing sie nur an der
    Zahl der Gegner im Draft.
    """
    prior_staerke = (config.PAAR_PRIOR_STAERKE if prior_staerke is None
                     else float(prior_staerke))
    referenz = prior_sd(0.5, prior_staerke)
    _, sd = posterior(max(0.0, spiele), max(0.0, spiele) * 0.5, 0.5, prior_staerke)
    return max(0.0, min(1.0, 1.0 - sd / referenz)) if referenz else 0.0
