"""Der Score-Vertrag.

**Die eine Regel dieser App:** jede Score-Komponente liefert einen Wert
in [-1, +1]. 0 heisst "durchschnittlich", nicht "null".

Warum so streng: die Eingangsgroessen sind voellig verschieden skaliert -
Attribute 0-100, Winrates 0-1, Vorteile -1..+1, Stichproben 0..50000.
Wer die addiert, bekommt eine Zahl, die niemand mehr deuten kann und
deren Gewichte keine Bedeutung mehr haben. Erst nach der Normalisierung
heisst "Gewicht 0.30" tatsaechlich "30 % der Entscheidung".

Die Umrechnung auf die Anzeige (0-100) passiert genau einmal, ganz am
Ende, in `Empfehlung.anzeige_score`.
"""

from dataclasses import dataclass, field
from statistics import fmean, pstdev

from drafter import config


def klemme(wert, unten=-1.0, oben=1.0):
    return max(unten, min(oben, wert))


def zentriere(wert, mitte=0.5, spanne=0.5):
    """Einen 0-1-Wert auf [-1, +1] legen. 0.5 wird zu 0."""
    return klemme((wert - mitte) / spanne)


def z_werte(werte):
    """Werte relativ zum Feld normalisieren.

    Gibt {schluessel: z} zurueck, gedeckelt auf [-1, +1] bei zwei
    Standardabweichungen. Fuer Groessen wie Map-Fit ist das die ehrliche
    Skala: "wie gut passt er **im Vergleich zu den anderen**" - ein
    absoluter Schwellenwert waere geraten und muesste je Map anders sein.

    Streuen alle Werte gleich (oder gibt es nur einen), ist das Ergebnis
    ueberall 0 - korrekt, denn dann unterscheidet diese Komponente nicht.
    """
    if not werte:
        return {}
    zahlen = list(werte.values())
    mittel = fmean(zahlen)
    streuung = pstdev(zahlen)
    if streuung < 1e-9:
        return {k: 0.0 for k in werte}
    return {k: klemme((v - mittel) / (2 * streuung)) for k, v in werte.items()}


@dataclass
class Grund:
    """Ein nachvollziehbarer Satz zu einem Teil der Bewertung.

    `staerke` sortiert nur - sie ist kein zweiter Score. Die Zahl im
    Score kommt ausschliesslich aus den Komponenten, damit Erklaerung und
    Bewertung nicht auseinanderlaufen koennen.
    """

    text: str
    positiv: bool = True
    staerke: float = 0.5
    quelle: str = "heuristik"   # heuristik | demo | daten

    def als_dict(self):
        return {
            "text": self.text,
            "positiv": self.positiv,
            "staerke": round(self.staerke, 3),
            "quelle": self.quelle,
        }


@dataclass
class Komponente:
    """Ein Bestandteil des Scores mit seiner Begruendung."""

    key: str
    wert: float = 0.0
    gewicht: float = 0.0
    gruende: list = field(default_factory=list)
    confidence: float = 1.0

    @property
    def beitrag(self):
        return self.wert * self.gewicht

    @property
    def label(self):
        return config.KOMPONENTEN_LABEL.get(self.key, self.key)

    @property
    def ist_strafe(self):
        return self.key in config.STRAF_KOMPONENTEN

    def als_dict(self):
        return {
            "key": self.key,
            "label": self.label,
            # Der Rohwert der Komponente in [-1, +1]. Steht mit dabei,
            # weil Beitrag = Wert x Gewicht ist: ohne den Wert kann man
            # "schwache Komponente" nicht von "kleines Gewicht"
            # unterscheiden. Genau das will die Aufschluesselung zeigen.
            "wert": round(self.wert, 3),
            "gewicht": round(self.gewicht, 3),
            # Beitrag in Anzeigepunkten - das ist die Zahl, die in der
            # Aufschluesselung steht ("Map Fit +18").
            "beitrag": round(self.beitrag * 50, 1),
            "ist_strafe": self.ist_strafe,
            # Begruendungen der Komponente, damit jede Zeile der Tabelle
            # aufklappbar ist und nicht nur eine Zahl bleibt.
            "gruende": [g.als_dict() for g in self.gruende],
        }


@dataclass
class Empfehlung:
    """Das Ergebnis fuer genau einen Kandidaten.

    Traegt Bewertung UND Begruendung UND Auftrag - die Oberflaeche soll
    nichts nachrechnen und nichts selbst formulieren muessen.
    """

    brawler: object
    komponenten: dict = field(default_factory=dict)
    confidence: float = 0.0
    win_probability: float = 0.5
    rolle: str = ""
    aufgaben: list = field(default_factory=list)
    bevorzugte_matchups: list = field(default_factory=list)
    zu_vermeidendes_matchup: object = None
    vermeiden: list = field(default_factory=list)
    warnungen: list = field(default_factory=list)
    build: object = None

    @property
    def score(self):
        """Rohscore in [-1, +1]. Summe der gewichteten Komponenten."""
        return klemme(sum(k.beitrag for k in self.komponenten.values()))

    @property
    def anzeige_score(self):
        """0-100 fuer die Oberflaeche. 50 = durchschnittlicher Pick.

        Kein Min-Max ueber das Kandidatenfeld: das wuerde dem besten
        Kandidaten auch dann 95 geben, wenn alle Vorschlaege schlecht
        sind. Die feste Skala sagt stattdessen etwas ueber die Guete
        selbst - Anker bei 50, oben und unten offen bis 0/100.
        """
        return round(50 + 50 * self.score)

    @property
    def confidence_label(self):
        for grenze, label in config.CONFIDENCE_STUFEN:
            if self.confidence >= grenze:
                return label
        return config.CONFIDENCE_STUFEN[-1][1]

    def aufschluesselung(self):
        """Alle Komponenten in fester Reihenfolge - auch die mit Beitrag 0.

        Vollstaendig und stabil, nicht nach Betrag sortiert: nur so
        stehen bei jedem Brawler dieselben Zeilen an denselben Stellen,
        und nur so sieht man, dass eine Komponente NICHT beigetragen hat
        (Counter beim First Pick, Angreifbarkeit ohne bekannte Gegner).
        Eine fehlende Zeile waere nicht von einer Null zu unterscheiden.
        """
        vollstaendig = []
        for key in config.KOMPONENTEN_REIHENFOLGE:
            komp = self.komponenten.get(key)
            if komp is None:
                komp = Komponente(key=key, wert=0.0, gewicht=0.0)
            vollstaendig.append(komp)
        return vollstaendig

    @property
    def groesster_treiber(self):
        """Die Komponente, die diese Empfehlung am staerksten traegt."""
        if not self.komponenten:
            return None
        return max(self.komponenten.values(), key=lambda k: abs(k.beitrag))

    def gruende(self, positiv=True):
        gesammelt = []
        for komp in self.komponenten.values():
            gesammelt += [g for g in komp.gruende if g.positiv == positiv]
        gesammelt.sort(key=lambda g: -g.staerke)
        return gesammelt[: config.GRUENDE_MAX]

    def als_dict(self, ausfuehrlich=False):
        b = self.brawler
        daten = {
            "slug": b.slug,
            "name": b.name,
            "score": self.anzeige_score,
            "score_roh": round(self.score, 3),
            "win_probability": round(self.win_probability * 100, 1),
            "confidence": round(self.confidence, 2),
            "confidence_label": self.confidence_label,
            "rolle": self.rolle,
            "rollen": b.rollen_label,
            "farbe": b.color,
            "initialen": b.initialen,
            "image_url": b.image_url,
            "pro": [g.als_dict() for g in self.gruende(True)],
            "contra": [g.als_dict() for g in self.gruende(False)],
            # Die Aufschluesselung gehoert zu JEDER Empfehlung, nicht nur
            # zur Spitze: sie ist der Grund, warum das Werkzeug kein
            # Orakel ist. Sie kostet nichts extra - die Komponenten sind
            # ohnehin gerechnet, sonst gaebe es keinen Score.
            "komponenten": [k.als_dict() for k in self.aufschluesselung()],
            "groesster_treiber": (
                self.groesster_treiber.label if self.groesster_treiber else None
            ),
        }
        if ausfuehrlich:
            daten.update({
                "aufgaben": self.aufgaben,
                "hauptaufgabe": self.aufgaben[0] if self.aufgaben else None,
                "bevorzugte_matchups": self.bevorzugte_matchups,
                "bevorzugtes_matchup": (
                    self.bevorzugte_matchups[0] if self.bevorzugte_matchups else None
                ),
                "zu_vermeidendes_matchup": self.zu_vermeidendes_matchup,
                "vermeiden": self.vermeiden,
                "warnungen": self.warnungen,
                "build": self.build,
            })
        return daten
