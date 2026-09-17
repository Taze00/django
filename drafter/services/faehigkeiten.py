# -*- coding: utf-8 -*-
"""Was ein Brawler kann - aus Profil, aus der Fachquelle, oder gar nicht.

Drei Wissensstaende, streng getrennt:

    Profile      ein gepflegtes Eigenschaftsprofil nennt eine ZAHL
    Fachquelle   die Role-&-Ability-Map nennt die Faehigkeit (oder nennt
                 sie ausdruecklich nicht) - qualitativ, ohne Staerke
    Unknown      weder noch

Der Unterschied zwischen "Fachquelle sagt nein" und "Unknown" ist wichtig:
Steht ein Brawler in der Map und traegt den Marker NICHT, dann ist das
eine Aussage ("er bricht keine Waende"). Steht er gar nicht in der Map,
wissen wir es nicht - und 0 waere gelogen.

**Aus der Map entsteht nie eine Zahl.** "Griff bricht Waende" heisst nicht
"wallbreak = 0.95". Wer eine Groesse braucht, bekommt `vorhanden=True` und
`wert=None` und muss damit umgehen koennen.
"""

from dataclasses import dataclass

from drafter import config

PROFILE = "Profile"
FACHQUELLE = "Fachquelle"
UNKNOWN = "Unknown"


@dataclass(frozen=True)
class Auskunft:
    """Was ueber eine Faehigkeit bekannt ist.

    `wert`      0-1 aus dem Profil, sonst None
    `vorhanden` True/False aus Profil oder Fachquelle, sonst None
    `quelle`    Profile | Fachquelle | Unknown
    """

    wert: float = None
    vorhanden: bool = None
    quelle: str = UNKNOWN

    @property
    def bekannt(self):
        return self.quelle != UNKNOWN

    def __bool__(self):
        return bool(self.vorhanden)


def auskunft(brawler, faehigkeit):
    """Wissensstand zu einer Faehigkeit der Role-&-Ability-Map."""
    attribute = config.FAEHIGKEIT_ATTRIBUTE.get(faehigkeit, ())

    # 1. Profil: die Zahl gewinnt, sie sagt auch WIE stark.
    if brawler.hat_profil and attribute:
        wert = max(brawler.wert(key) for key in attribute)
        return Auskunft(wert=wert, vorhanden=wert > 0.0, quelle=PROFILE)

    # 2. Fachquelle: qualitativ. Auch das Fehlen des Markers ist eine
    #    Aussage - aber nur, wenn der Brawler in der Quelle ueberhaupt steht.
    if brawler.draft_rolle:
        return Auskunft(vorhanden=brawler.kann(faehigkeit), quelle=FACHQUELLE)

    # 3. Nichts bekannt. Ausdruecklich NICHT 0.
    return Auskunft()


def wandabhaengigkeit(brawler):
    """Wie sehr lebt dieser Brawler von Waenden? 0-1, oder Unknown.

    Abgeleitet, nicht gepflegt - es gibt bewusst kein 109. Handfeld:

        Draft-Rolle   Thrower hoch, Sniper niedrig (config)
        Profil        Nahkampf und Flaechenkontrolle dafuer,
                      Reichweite dagegen

    Liegt beides vor, zaehlt beides je zur Haelfte; liegt nur eines vor,
    gilt dieses; liegt nichts vor, ist das Ergebnis Unknown. Die Zahlen
    stehen in config (WANDABHAENGIGKEIT_*) und sind Annahmen, keine
    Messung - sie fliessen in keinen Score ein.
    """
    teile = []
    quellen = []

    aus_rolle = config.WANDABHAENGIGKEIT_ROLLE.get(brawler.draft_rolle)
    if aus_rolle is not None:
        teile.append(aus_rolle)
        quellen.append(FACHQUELLE)

    if brawler.hat_profil:
        roh = 0.5 + sum(
            gewicht * brawler.wert(key)
            for key, gewicht in config.WANDABHAENGIGKEIT_ATTRIBUTE.items()
        )
        teile.append(max(0.0, min(1.0, roh)))
        quellen.append(PROFILE)

    if not teile:
        return Auskunft()
    wert = sum(teile) / len(teile)
    return Auskunft(wert=wert, vorhanden=wert > 0.5,
                    quelle=PROFILE if PROFILE in quellen else FACHQUELLE)


def wallbreak_value(kandidat, eigene, gegner, karte=None):
    """Was Wandbruch in DIESER Lage wert ist, [-1, +1] - oder Unknown.

        Faehigkeit des Kandidaten
      x Wandrelevanz der Map
      x (Wandabhaengigkeit des Gegners - Wandabhaengigkeit unseres Teams)

    Kein Brawler kommt darin vor. Wandbruch ist hier nicht pauschal gut:
    gegen ein Team, das Waende braucht, ist er stark - im eigenen Team,
    das Waende braucht, schadet er.

    Gibt (Auskunft, Begruendung) zurueck. Unbekannte Groessen fuehren zu
    Unknown, nie zu 0.
    """
    kann = auskunft(kandidat, "wallbreak")
    if not kann.bekannt or not kann.vorhanden:
        # Kann er es nicht (oder wissen wir es nicht), gibt es nichts zu
        # bewerten - im ersten Fall ist der Wert 0 korrekt, im zweiten
        # bleibt er unbekannt.
        if kann.quelle == UNKNOWN:
            return Auskunft(), "unbekannt, ob er Wände bricht"
        return Auskunft(wert=0.0, vorhanden=False, quelle=kann.quelle), "bricht keine Wände"

    relevanz = None
    if karte is not None and (karte.traits or {}).get("wall_density") is not None:
        relevanz = karte.trait("wall_density") / 100.0
    if relevanz is None:
        return Auskunft(), "Map kennt keine Wanddichte"

    def teamwert(team):
        werte = [a.wert for a in (wandabhaengigkeit(b) for b in team) if a.wert is not None]
        return sum(werte) / len(werte) if werte else None

    eigen = teamwert(eigene)
    feind = teamwert(gegner)
    if eigen is None or feind is None:
        return Auskunft(), "Wandabhängigkeit eines Teams unbekannt"

    staerke = kann.wert if kann.wert is not None else 1.0
    # Kein Verstaerkungsfaktor: die drei Groessen liegen je in [0, 1],
    # das Produkt damit in [-1, +1]. Ein Faktor wuerde den Wert bei
    # eindeutigen Aufstellungen sofort an die Grenze druecken und dort
    # jeden Unterschied einebnen.
    wert = max(-1.0, min(1.0, staerke * relevanz * (feind - eigen)))
    richtung = "hilft uns" if wert > 0 else "schadet uns" if wert < 0 else "neutral"
    return (
        Auskunft(wert=wert, vorhanden=wert > 0, quelle=kann.quelle),
        f"{richtung}: Gegner {feind:.2f} gegen uns {eigen:.2f} Wandabhängigkeit "
        f"bei Wanddichte {relevanz:.2f}",
    )
