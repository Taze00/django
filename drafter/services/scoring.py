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
    # False = fuer diesen Brawler NICHT berechenbar (Eigenschaften oder
    # Messwerte fehlen). Das ist etwas anderes als Wert 0: eine
    # nicht verfuegbare Komponente faellt aus dem Score heraus, statt ihn
    # Richtung "durchschnittlich" oder "schlecht" zu ziehen. "Nicht
    # anwendbar" (Counter ohne bekannte Gegner) bleibt dagegen verfuegbar
    # mit Wert 0 - das gilt fuer alle Kandidaten gleich.
    verfuegbar: bool = True
    quelle: str = "Unknown"   # Measured | Measured + Prior | Profile | Unknown

    @property
    def beitrag(self):
        return self.wert * self.gewicht if self.verfuegbar else 0.0

    @property
    def label(self):
        return config.KOMPONENTEN_LABEL.get(self.key, self.key)

    @property
    def ist_strafe(self):
        return self.key in config.STRAF_KOMPONENTEN

    def als_dict(self, skalierung=1.0):
        """`skalierung` rechnet die Bewertungsgewichte hoch, wenn andere
        Komponenten nicht verfuegbar sind - so summieren sich die
        angezeigten Beitraege weiter genau zum Score."""
        faktor = (
            1.0 if self.ist_strafe or not self.verfuegbar or self.key == config.K_PERSONAL
            else skalierung
        )
        return {
            "key": self.key,
            "label": self.label,
            "verfuegbar": self.verfuegbar,
            "quelle": self.quelle if self.verfuegbar else "Unknown",
            # Der Rohwert der Komponente in [-1, +1]. Steht mit dabei,
            # weil Beitrag = Wert x Gewicht ist: ohne den Wert kann man
            # "schwache Komponente" nicht von "kleines Gewicht"
            # unterscheiden. Genau das will die Aufschluesselung zeigen.
            "wert": round(self.wert, 3),
            "gewicht": round(self.gewicht * faktor, 3),
            # Beitrag in Anzeigepunkten - das ist die Zahl, die in der
            # Aufschluesselung steht ("Map Fit +18").
            "beitrag": round(self.beitrag * faktor * 50, 1),
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
    # profil | gemessen - Kandidaten der Stufe "katalog" werden nicht bewertet.
    stufe: str = "profil"

    # --- Datenabdeckung -------------------------------------------------
    def _bewertungsgewichte(self, ohne_persoenlich=False):
        komps = [
            k for k in self.komponenten.values()
            if not k.ist_strafe and not (ohne_persoenlich and k.key == config.K_PERSONAL)
        ]
        gesamt = sum(k.gewicht for k in komps)
        verfuegbar = sum(k.gewicht for k in komps if k.verfuegbar)
        return gesamt, verfuegbar

    @property
    def skalierung(self):
        """Faktor, mit dem die verfuegbaren Bewertungsbeitraege hochgerechnet
        werden. 1.0, wenn alles berechenbar ist - dann ist der Score exakt
        die alte Summe.

        Ohne die persoenliche Sicherheit gerechnet und nicht auf sie
        angewandt: sie hat einen harten Deckel (PERSOENLICH_MAX_AUSSCHLAG),
        und hochgerechnet koennte sie bei einem nur gemessenen Brawler ein
        Vielfaches davon ausmachen.
        """
        gesamt, verfuegbar = self._bewertungsgewichte(ohne_persoenlich=True)
        if verfuegbar <= 0 or verfuegbar >= gesamt:
            return 1.0
        return gesamt / verfuegbar

    @property
    def datenabdeckung(self):
        """0-1: auf welchem Anteil der Bewertungsgewichte der Score beruht.

        Die persoenliche Sicherheit zaehlt nicht mit - sie ist immer
        bekannt und wuerde jede Abdeckung um ihren Anteil schoenen.
        """
        gesamt, verfuegbar = self._bewertungsgewichte(ohne_persoenlich=True)
        return verfuegbar / gesamt if gesamt > 0 else 0.0

    @property
    def datenabdeckung_label(self):
        for grenze, text in config.DATENABDECKUNG_STUFEN:
            if self.datenabdeckung >= grenze:
                return text
        return config.DATENABDECKUNG_STUFEN[-1][1]

    @property
    def ausgelassen(self):
        """Komponenten, die mangels Daten aus dem Score fallen.

        Ohne die persoenliche Sicherheit: sie ist freiwillig. Wer keine
        pflegt, soll nicht lesen, dass ihm etwas fehlt - sie zaehlt weder
        zur Abdeckung noch zur Confidence.
        """
        return [
            k for k in self.aufschluesselung()
            if k.key in self.komponenten and not k.verfuegbar and k.key != config.K_PERSONAL
        ]

    @property
    def roher_score(self):
        """Ungeklemmte Summe der gewichteten Komponenten.

        Nach DIESEM Wert wird sortiert, nicht nach `score`. Die
        Bewertungsgewichte summieren sich auf 1.0, die Strafen kommen
        obendrauf - die Summe kann also bis etwa -1.6 fallen. Geklemmt
        wuerden zwei Kandidaten bei -1.2 und -1.5 gleich aussehen und
        ihre Reihenfolge waere Zufall. In den Demo-Daten tritt das nicht
        auf (tiefster gemessener Wert -0.95 ueber 900 Kandidaten), mit
        echten Daten ist es nicht ausgeschlossen.
        """
        komps = self.komponenten.values()
        bewertung = sum(
            k.beitrag for k in komps if not k.ist_strafe and k.key != config.K_PERSONAL
        )
        persoenlich = sum(k.beitrag for k in komps if k.key == config.K_PERSONAL)
        strafen = sum(k.beitrag for k in komps if k.ist_strafe)
        # Fehlende Bewertungskomponenten fallen heraus, die vorhandenen
        # werden auf die volle Gewichtssumme hochgerechnet. Nicht die
        # persoenliche Sicherheit (Deckel) und nicht die Strafen: eine
        # Strafe, die nicht berechenbar ist, faellt einfach weg.
        return bewertung * self.skalierung + persoenlich + strafen

    @property
    def score(self):
        """Score in [-1, +1] - fuer die Anzeige. Rangfolge: `roher_score`."""
        return klemme(self.roher_score)

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
            # Ungeklemmt - `score_roh` hiess vorher so, lieferte aber den
            # geklemmten Wert.
            "score_roh": round(self.roher_score, 3),
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
            "komponenten": [k.als_dict(self.skalierung) for k in self.aufschluesselung()],
            "datenstufe": self.stufe,
            "datenabdeckung": round(self.datenabdeckung * 100),
            "datenabdeckung_label": self.datenabdeckung_label,
            "ausgelassen": [k.label for k in self.ausgelassen],
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
