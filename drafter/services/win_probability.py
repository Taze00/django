"""Geschaetzte Siegchance - hinter einem austauschbaren Interface.

Im MVP rechnet hier eine Heuristik, kein Modell. Das ist ausdruecklich
so gemeint und wird der Oberflaeche auch so gemeldet (`ist_heuristik`),
damit niemand eine kalibrierte Wahrscheinlichkeit liest, wo eine
Einschaetzung steht.

Die Architektur ist der eigentliche Punkt dieser Datei: alle Aufrufer
kennen nur `hole_provider().vorhersage(...)`. Sobald genug saubere
Matchdaten existieren, tritt an die Stelle der Heuristik ein
`MLWinProbabilityProvider` mit derselben Signatur - ohne dass Engine,
Views oder Templates sich aendern.

Die Spanne ist bewusst eng (config.WIN_SPANNE): ein Draftvorteil
verschiebt die Siegchance real selten ueber 65 %. Wer 85 % anzeigt,
verkauft Sicherheit, die es nicht gibt.
"""

import math

from drafter import config
from drafter.services.counters import vorteil


class WinProbabilityProvider:
    """Vertrag fuer jede Schaetzung der Siegchance."""

    ist_heuristik = True
    name = "basis"

    def vorhersage(self, ctx, raum, eigene_analyse=None, gegner_analyse=None):
        """Gibt (wahrscheinlichkeit 0-1, confidence 0-1) zurueck."""
        raise NotImplementedError


class HeuristicWinProbabilityProvider(WinProbabilityProvider):
    """Drei messbare Vorteile, gewichtet und weich begrenzt.

    1. **Deckung**: wie gut erfuellt jedes Team die Anforderungen der Map
    2. **Matchups**: Summe der Counter-Verhaeltnisse beider Teams
    3. **Meta**: wie gut laufen die gewaehlten Brawler derzeit

    `tanh` sorgt dafuer, dass der erste Vorteil viel zaehlt und der
    fuenfte kaum noch - ein Team kann nicht beliebig weit davonziehen.
    """

    name = "heuristik"

    GEWICHT_DECKUNG = 0.45
    GEWICHT_MATCHUP = 0.35
    GEWICHT_META = 0.20

    def vorhersage(self, ctx, raum, eigene_analyse=None, gegner_analyse=None):
        vorteile = []

        # Deckung nur vergleichen, wenn beide Teams vollstaendig bekannt
        # sind: ein Mitglied ohne Profil fehlt im Teamprofil, und die
        # Deckung dieses Teams waere systematisch zu niedrig.
        if (eigene_analyse is not None and gegner_analyse is not None
                and not eigene_analyse.unbekannt and not gegner_analyse.unbekannt):
            vorteile.append(
                self.GEWICHT_DECKUNG
                * (eigene_analyse.deckungsgrad() - gegner_analyse.deckungsgrad())
                * 2.0
            )

        if ctx.own_picks and ctx.enemy_picks:
            paare = []
            for a in ctx.own_picks:
                for b in ctx.enemy_picks:
                    wert, _, quelle = vorteil(a, b, raum)
                    if quelle is not None:   # unbekannte Paare zaehlen nicht mit
                        paare.append(wert)
            if paare:
                vorteile.append(self.GEWICHT_MATCHUP * (sum(paare) / len(paare)))

        meta_diff = self._meta_diff(ctx, raum)
        if meta_diff is not None:
            vorteile.append(self.GEWICHT_META * meta_diff)

        roh = sum(vorteile)
        wahrscheinlichkeit = config.WIN_BASIS + config.WIN_SPANNE * math.tanh(roh * 1.6)
        wahrscheinlichkeit = max(
            config.WIN_UNTERGRENZE, min(config.WIN_OBERGRENZE, wahrscheinlichkeit)
        )

        # Confidence: ein halb fertiger Draft laesst sich schlechter
        # bewerten als ein fertiger, und Demo-Daten gar nicht richtig.
        vollstaendig = ctx.picks_gesamt / 6.0
        conf = 0.25 + 0.5 * vollstaendig
        if raum.nur_demo:
            conf = min(conf, 0.35)
        return wahrscheinlichkeit, conf

    def _meta_diff(self, ctx, raum):
        def staerke(picks):
            werte = [raum.meta(b).staerke for b in picks if raum.meta(b).rate is not None]
            return sum(werte) / len(werte) if werte else None

        eigen = staerke(ctx.own_picks)
        gegner = staerke(ctx.enemy_picks)
        if eigen is None or gegner is None:
            return None
        return eigen - gegner


_provider = None


def hole_provider():
    """Der aktuell gueltige Provider.

    Einstiegspunkt fuer den spaeteren Austausch - hier kaeme die
    Entscheidung "ML-Modell vorhanden und kalibriert? dann das" hin.
    """
    global _provider
    if _provider is None:
        _provider = HeuristicWinProbabilityProvider()
    return _provider


def setze_provider(provider):
    """Fuer Tests und den spaeteren Umstieg."""
    global _provider
    _provider = provider
