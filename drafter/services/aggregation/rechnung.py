# -*- coding: utf-8 -*-
"""Die Rechenregeln der Aggregation - ohne Datenbank, einzeln pruefbar.

Drei Fragen, drei Modelle:

**Wie stark ist ein Brawler?**
Gewichtete Siege durch gewichtete Spiele, Bayes-geglaettet gegen einen
Prior. Der Prior ist nicht immer 50 %: eine Map-Statistik schrumpft zur
Modus-Statistik desselben Brawlers, eine 7-Tage-Statistik zur
90-Tage-Statistik. Kleine Stichproben erben so die beste verfuegbare
Vorannahme statt eines Muenzwurfs.

**Wie gut ist A gegen B?**
Nicht die rohe Paar-Winrate. Ist A allgemein stark und B schwach,
gewinnt A haeufig - ohne B zu kontern. Erwartet wird deshalb nach log5
(Bill James): P(A schlaegt B) = pA(1-pB) / (pA(1-pB) + pB(1-pA)). Der
Counter-Vorteil ist die Abweichung davon, und der Bayes-Prior ist genau
diese Erwartung - kleine Stichproben landen bei "kein Vorteil".

**Wie gut sind A und B zusammen?**
Ebenso nicht die gemeinsame Winrate. Erwartet wird, dass sich die
Staerken additiv auf der Log-Odds-Skala verhalten:
logit(P) = logit(pA) + logit(pB). Synergie ist, was darueber hinausgeht.
Das ist eine Naeherung - aber eine, die "zwei starke Brawler" nicht mit
"zwei Brawler, die sich ergaenzen" verwechselt.

**Und was, wenn ein Paar in EINEM Modus nur sechs Mal vorkam?**
Dann traegt, was ausserhalb dieses Modus bekannt ist. Die Modus-Zeile
schrumpft nicht mehr gegen die nackte log5-Erwartung, sondern gegen die
Abweichung, die dasselbe Paar in allen ANDEREN Modi gezeigt hat
(`rest_zaehler` + `uebertragener_prior`). Sechs Partien bewegen den Wert
dann kaum, sechshundert bestimmen ihn.

Entscheidend fuer die Sauberkeit: der Prior ist die **Differenzmenge**
global minus Modus, nicht die Globalzeile selbst. Die Globalzeile
enthaelt die Modus-Partien bereits - sie als Prior zu nehmen, wuerde
dieselben Partien ein zweites Mal in die Schaetzung ziehen, einmal als
Prior und einmal als Beobachtung. So zaehlt jede Partie in jeder
einzelnen Schaetzung genau einmal.
"""

import math
from dataclasses import dataclass

from drafter.services.patch_weighting import bayes

# Raten nie exakt 0 oder 1 in Logit/log5 geben - beides ist unendlich.
RAND = 0.01


def begrenze(p):
    return min(1.0 - RAND, max(RAND, p))


def logit(p):
    p = begrenze(p)
    return math.log(p / (1.0 - p))


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def erwartet_gegeneinander(pa, pb):
    """log5: Erwartete Siegquote von A gegen B aus den Einzelstaerken."""
    pa, pb = begrenze(pa), begrenze(pb)
    a = pa * (1.0 - pb)
    return a / (a + pb * (1.0 - pa))


def erwartet_miteinander(pa, pb):
    """Erwartete Siegquote eines Teams mit A und B (additive Log-Odds)."""
    return sigmoid(logit(pa) + logit(pb))


def vorteil(geglaettet, erwartet):
    """Abweichung von der Erwartung auf [-1, +1] - der Score-Vertrag der Engine."""
    return max(-1.0, min(1.0, 2.0 * (geglaettet - erwartet)))


def rest_zaehler(grob, fein):
    """Was die groebere Ebene weiss, OHNE die feinere: grob minus fein.

    Die Globalzeile eines Paares enthaelt seine Knockout-Partien mit. Wer
    sie als Prior fuer Knockout benutzt, zaehlt dieselben Partien zweimal
    - erst als Vorannahme, dann als Beobachtung. Gezaehlt wird hier
    deshalb die Differenzmenge: alle Partien des Paares ausserhalb dieses
    Modus.

    Die Subtraktion ist exakt, weil beide Zaehler aus demselben Lauf
    ueber dieselben Partien stammen: jede Partie der feineren Ebene ist
    in der groeberen enthalten. `max(0, ...)` ist nur eine Sicherung
    gegen Aufrufe, die das verletzen - dann bleibt der Rest leer und der
    Prior faellt auf die Erwartung zurueck.
    """
    return Zaehler(
        games=max(0, grob.games - fein.games),
        wins=max(0, grob.wins - fein.wins),
        gewicht=max(0.0, grob.gewicht - fein.gewicht),
        gewicht_siege=max(0.0, grob.gewicht_siege - fein.gewicht_siege),
    )


def uebertragener_prior(rest_rate, erwartet_grob, erwartet_fein):
    """Die ausserhalb gemessene ABWEICHUNG auf die feinere Ebene uebertragen.

    Nicht die Rate wandert, sondern der Vorsprung. Beide Ebenen haben
    eigene Erwartungen - global kann ein Paar 53 % erwarten lassen und im
    Modus 47 %, weil dort andere Einzelstaerken gelten. Uebertragbar ist
    nur, was ueber die jeweilige Erwartung hinausgeht:

        prior_fein = erwartet_fein + (rest_rate - erwartet_grob)

    Damit heisst "ausserhalb dieses Modus 2 Punkte besser als erwartet"
    auch im Modus "2 Punkte besser als dort erwartet" - und nicht
    versehentlich "53 %", wo 53 % schon ueberdurchschnittlich waeren.
    """
    return begrenze(erwartet_fein + (rest_rate - erwartet_grob))


@dataclass
class Zaehler:
    """Gezaehlte und gewichtete Spiele fuer eine Statistikzeile."""

    games: int = 0
    wins: int = 0
    gewicht: float = 0.0
    gewicht_siege: float = 0.0

    def zaehle(self, sieg, gewicht):
        self.games += 1
        self.gewicht += gewicht
        if sieg:
            self.wins += 1
            self.gewicht_siege += gewicht

    @property
    def roh(self):
        """Ungewichtete, ungeglaettete Rate - fuer die Transparenz, nicht zum Rechnen."""
        return self.wins / self.games if self.games else None

    def geglaettet(self, prior_rate, prior_staerke):
        """Gewichtete Rate, Bayes-geglaettet.

        Mit der GEWICHTETEN Stichprobe: 100 Spiele von vor einem Rework
        zaehlen fast nichts - weder fuer die Rate noch gegen den Prior.
        """
        return bayes(self.gewicht, self.gewicht_siege, prior_rate, prior_staerke)
