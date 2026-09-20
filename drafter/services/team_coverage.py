"""Was ein Team kann, was ihm fehlt und was es doppelt hat.

Hier wohnt der Unterschied zwischen diesem Werkzeug und einer Tierlist.
Eine Tierlist bewertet Brawler einzeln; dieses Modul bewertet, was ein
Brawler **dem Rest hinzufuegt**. Drei einzeln starke Tanks scheitern
hier an drei Stellen gleichzeitig: keine Reichweite gedeckt, kein
Anti-Tank gedeckt, Robustheit dreifach.

Die zentrale Rechnung ist das Teamprofil. Es ist **nicht die Summe** der
Einzelwerte und **nicht ihr Mittel**:

    profil = bester + 0.45 * zweitbester + 0.20 * drittbester   (gedeckelt)

Warum: zwei halbe Anti-Tanks sind kein ganzer - wenn keiner den Tank
wirklich aufhalten kann, hilft es nicht, dass beide es ein bisschen
koennen. Gleichzeitig ist ein zweiter guter Anti-Tank mehr wert als
keiner, also darf es auch kein reines Maximum sein. Der Mittelwert
wiederum waere falsch herum: er *senkt* die Deckung, wenn ein Spezialist
dazukommt, der anderswo stark ist.
"""

from dataclasses import dataclass, field

from drafter import attributes as attr
from drafter import config


def teamprofil(brawler_liste):
    """Was das Team in jeder Eigenschaft leistet, je 0-1.

    Gerechnet wird ueber **jeden** Pick, der zu dieser Eigenschaft etwas
    beitraegt - egal aus welcher Quelle. Bis zum 2026-09-20 zaehlten nur
    Mitglieder mit gepflegtem `attributes`-Profil, also zwanzig von 106.
    AMBER, ein eigener Pick mit Rolle, Faehigkeiten und 2044 gemessenen
    Partien, trug damit nichts bei: das Profil eines Zweierteams stammte
    von einem Brawler, und fast jede Eigenschaft sah aus wie eine Luecke.

    Wer zu einer Eigenschaft nichts sagt, zaehlt weiterhin nicht mit -
    aber er zaehlt auch nicht als Null. Wie viel des Teams ueberhaupt
    bekannt ist, steht in `bekannt_anteil()` daneben.
    """
    profil = {}
    for key in attr.ATTRIBUT_KEYS:
        werte = sorted(_bekannte_teamwerte(brawler_liste, key), reverse=True)
        gesamt = 0.0
        for rang, wert in enumerate(werte[:3]):
            anteil = (
                1.0 if rang == 0
                else config.ZWEITBESTER_ANTEIL if rang == 1
                else config.DRITTBESTER_ANTEIL
            )
            gesamt += wert * anteil
        profil[key] = min(1.0, gesamt)
    return profil


def _bekannte_teamwerte(brawler_liste, key):
    """Die Werte der Teammitglieder, die zu `key` wirklich etwas sagen."""
    from drafter.services import vertrauen

    werte = []
    for b in brawler_liste:
        wert, stufe = vertrauen.wert_mit_stufe(b, key)
        if wert is not None:
            werte.append(wert)
    return werte


def bekannt_anteil(brawler_liste, key):
    """Von wie vielen Picks wissen wir etwas ueber diese Eigenschaft?

    (bekannt, gesamt) - die Zahl, die aus "Frontline 0.00" entweder
    "niemand kann das" oder "wir wissen es von keinem" macht. Zwei sehr
    verschiedene Saetze, die bisher gleich aussahen.
    """
    gesamt = len(brawler_liste)
    return len(_bekannte_teamwerte(brawler_liste, key)), gesamt


def anforderungen_mit_gegner(basis, gegner_picks):
    """Map-Anforderungen um das erweitern, was das Gegnerteam erzwingt.

    Ohne diesen Schritt kennt der Teambedarf nur die Map - und eine Map
    verlangt nun einmal kein "Anti-Thrower". Steht auf der anderen Seite
    ein Tick, brauchen wir trotzdem eine Antwort auf ihn, auch wenn die
    Map das Wort nie erwaehnt. Genau hier entsteht der Unterschied
    zwischen "guter Pick auf dieser Map" und "guter Pick in diesem
    Draft".

    Verknuepft wird mit `max`, nicht mit einer Summe: die Map bleibt die
    Grundlage, der Gegner kann Anforderungen nur **hinzufuegen** oder
    verschaerfen. Sonst koennte ein Gegnerteam eine echte Map-Anforderung
    verwaessern, indem es nebenbei andere Bedarfe erzeugt.
    """
    erweitert = dict(basis)
    # Gegner ohne Profil erzwingen nichts - was er kann, ist unbekannt.
    gegner_picks = [g for g in gegner_picks if g.hat_profil]
    if not gegner_picks:
        return erweitert

    def hoechster(fn):
        return max((fn(g) for g in gegner_picks), default=0.0)

    # Jede Zeile: welche gegnerische Eigenschaft erzwingt welche Antwort.
    # Bewusst kurz und explizit - das sind die Paarungen, die im Spiel
    # tatsaechlich ueber Siege entscheiden.
    erzwungen = {
        "anti_tank": hoechster(lambda g: g.wert_oder("tankiness")) * 0.95,
        "anti_assassin": hoechster(
            lambda g: max(g.wert_oder("engage"), g.wert_oder("mobility"))
            if {"assassin", "aggro"} & set(g.alle_rollen) else 0.0
        ) * 0.90,
        "anti_thrower": hoechster(
            lambda g: 0.95 if "thrower" in g.alle_rollen else g.wert_oder("area_control") * 0.5
        ),
        # Gegen viel Reichweite braucht man entweder eigene Reichweite
        # oder jemanden, der hinkommt.
        "long_range": hoechster(lambda g: g.wert_oder("long_range")) * 0.65,
        "backline_pressure": hoechster(
            lambda g: g.wert_oder("long_range") * (1.0 - g.wert_oder("survivability"))
        ) * 0.85,
        # Wer Flaechen verweigert, zwingt uns zu Beweglichkeit.
        "mobility": hoechster(lambda g: g.wert_oder("area_control")) * 0.6,
        # Eine gegnerische Frontlinie erzeugt den schwaechsten Zwang der
        # Liste: sie laesst sich auch mit Kontrolle beantworten, nicht nur
        # mit einer eigenen Frontlinie. Waere der Faktor hoch, wuerde aus
        # "der Gegner hat einen Tank" reflexhaft "wir brauchen einen Tank" -
        # genau die Denkfalle, die dieses Werkzeug vermeiden soll.
        "frontline": hoechster(lambda g: g.wert_oder("frontline")) * 0.35,
    }

    for key, wert in erzwungen.items():
        if wert > 0:
            erweitert[key] = max(erweitert.get(key, 0.0), wert)
    return erweitert


def bekannt_je_eigenschaft(brawler_liste):
    """{key: (bekannt, gesamt)} fuer das ganze Vokabular."""
    return {key: bekannt_anteil(brawler_liste, key) for key in attr.ATTRIBUT_KEYS}


def bedarf(profil, anforderungen):
    """Wie dringend jede Eigenschaft noch gebraucht wird, je 0-1.

    Zwei Faktoren multipliziert:
    - wie wichtig die Map/der Modus diese Eigenschaft nimmt
    - wie weit das Team noch unter dem Deckungsziel liegt

    Was die Map nicht verlangt, erzeugt keinen Bedarf. Deshalb ist
    Wallbreak auf einer offenen Map kein Mangel, auf einer Brawl-Ball-
    Map dagegen ein dringender - ohne dass irgendwo eine Sonderregel je
    Map steht.
    """
    offen = {}
    for key in attr.ATTRIBUT_KEYS:
        wichtigkeit = anforderungen.get(key, 0.0)
        if wichtigkeit <= 0:
            offen[key] = 0.0
            continue
        fehlt = max(0.0, config.COVERAGE_ZIEL - profil.get(key, 0.0))
        offen[key] = wichtigkeit * (fehlt / config.COVERAGE_ZIEL)
    return offen


def ueberschuss(profil, anforderungen):
    """Wo das Team bereits mehr als genug hat.

    Gegenstueck zum Bedarf: ueber der Redundanzschwelle bringt zusaetzliche
    Deckung fast nichts mehr und kostet einen Pickplatz.
    """
    zuviel = {}
    for key in attr.ATTRIBUT_KEYS:
        gedeckt = profil.get(key, 0.0)
        if gedeckt <= config.REDUNDANZ_SCHWELLE:
            zuviel[key] = 0.0
            continue
        # Wie unwichtig die Eigenschaft hier ist, verstaerkt die Redundanz:
        # doppelte Reichweite auf einer offenen Map ist verzeihlich,
        # doppelter Wallbreak auf einer offenen Map ist verschwendet.
        unwichtig = 1.0 - anforderungen.get(key, 0.0)
        zuviel[key] = (gedeckt - config.REDUNDANZ_SCHWELLE) * (0.4 + 0.6 * unwichtig)
    return zuviel


def rollenzaehlung(brawler_liste):
    zaehler = {}
    for b in brawler_liste:
        for rolle in b.alle_rollen:
            zaehler[rolle] = zaehler.get(rolle, 0) + 1
    return zaehler


def rollen_ueberhang(brawler_liste):
    """Rollen, von denen das Team mehr hat, als sinnvoll ist."""
    zaehler = rollenzaehlung(brawler_liste)
    ueberhang = {}
    for rolle, anzahl in zaehler.items():
        grenze = config.ROLLEN_OBERGRENZE.get(rolle, 2)
        if anzahl > grenze:
            ueberhang[rolle] = anzahl - grenze
    return ueberhang


@dataclass
class Teamanalyse:
    """Das vollstaendige Bild eines Teams - eine Rechnung, viele Nutzer.

    Die Analyse wird je Empfehlungslauf einmal gebaut und von
    Teambedarf, Redundanz, Angreifbarkeit und dem Coach gemeinsam
    benutzt. Wuerde jede Komponente sie selbst rechnen, koennten sie
    auseinanderlaufen und dem Nutzer widersprechende Saetze zeigen.
    """

    brawler: list = field(default_factory=list)
    anforderungen: dict = field(default_factory=dict)
    profil: dict = field(default_factory=dict)
    # {key: (bekannt, gesamt)} - wie viele Picks zu dieser Eigenschaft
    # ueberhaupt etwas sagen. Ohne diese Zahl ist ein Profilwert von 0
    # nicht lesbar: er kann "niemand kann das" oder "wir wissen nichts"
    # heissen.
    bekannt: dict = field(default_factory=dict)
    bedarf: dict = field(default_factory=dict)
    ueberschuss: dict = field(default_factory=dict)
    rollen: dict = field(default_factory=dict)
    rollen_ueberhang: dict = field(default_factory=dict)
    # Mitglieder ohne Profil: gehen nicht ins Teamprofil ein. Luecken und
    # Deckung beschreiben dann nur die bekannten Mitglieder.
    unbekannt: list = field(default_factory=list)

    @classmethod
    def bauen(cls, brawler_liste, anforderungen):
        profil = teamprofil(brawler_liste)
        return cls(
            unbekannt=[b for b in brawler_liste if not b.hat_profil],
            brawler=list(brawler_liste),
            anforderungen=anforderungen,
            profil=profil,
            bekannt=bekannt_je_eigenschaft(brawler_liste),
            bedarf=bedarf(profil, anforderungen),
            ueberschuss=ueberschuss(profil, anforderungen),
            rollen=rollenzaehlung(brawler_liste),
            rollen_ueberhang=rollen_ueberhang(brawler_liste),
        )

    # --- Auswertung -----------------------------------------------------
    def groesste_luecken(self, anzahl=4, mindestens=0.15):
        """Die dringendsten offenen Eigenschaften, wichtigste zuerst."""
        sortiert = sorted(self.bedarf.items(), key=lambda p: -p[1])
        return [
            (attr.EIGENSCHAFT_NACH_KEY[k], wert)
            for k, wert in sortiert[:anzahl]
            if wert >= mindestens and k in attr.EIGENSCHAFT_NACH_KEY
        ]

    def kritische_luecken(self, mindestens=0.25):
        """Offene Luecken bei Eigenschaften, deren Fehlen richtig weh tut."""
        return [
            (attr.EIGENSCHAFT_NACH_KEY[k], wert)
            for k, wert in sorted(self.bedarf.items(), key=lambda p: -p[1])
            if k in attr.KNAPPE_KEYS and wert >= mindestens
        ]

    def staerken(self, anzahl=4, mindestens=0.55):
        sortiert = sorted(self.profil.items(), key=lambda p: -p[1])
        return [
            (attr.EIGENSCHAFT_NACH_KEY[k], wert)
            for k, wert in sortiert[:anzahl]
            if wert >= mindestens and k in attr.EIGENSCHAFT_NACH_KEY
        ]

    def deckungsgrad(self):
        """Ein Wert 0-1: wie gut erfuellt das Team die Anforderungen?

        Gewichtet mit der Wichtigkeit - eine perfekt gedeckte
        Nebensaechlichkeit hebt ihn kaum, eine offene Hauptanforderung
        zieht ihn deutlich.
        """
        gewicht = sum(self.anforderungen.values())
        if gewicht <= 0:
            return 0.5
        erreicht = sum(
            self.anforderungen.get(k, 0.0) * min(1.0, self.profil.get(k, 0.0) / config.COVERAGE_ZIEL)
            for k in attr.ATTRIBUT_KEYS
        )
        return min(1.0, erreicht / gewicht)

    def zuwachs(self, kandidat):
        """Was ein Kandidat dem Team wirklich hinzufuegt, je Eigenschaft.

        Nicht sein Eigenwert, sondern die Verbesserung des Teamprofils -
        genau der Unterschied, den eine Tierlist nicht sehen kann. Ein
        Anti-Tank 95 neben einem vorhandenen Anti-Tank 90 bringt fast
        nichts; derselbe Brawler in einem Team ohne Anti-Tank bringt
        alles.
        """
        neu = teamprofil(self.brawler + [kandidat])
        return {k: neu[k] - self.profil.get(k, 0.0) for k in attr.ATTRIBUT_KEYS}

    def als_dict(self):
        return {
            "deckungsgrad": round(self.deckungsgrad() * 100),
            "profil": {k: round(v * 100) for k, v in self.profil.items() if v > 0.05},
            "luecken": [
                {"key": e.key, "label": e.label, "dringlichkeit": round(w * 100), "kritisch": e.knapp}
                for e, w in self.groesste_luecken()
            ],
            "staerken": [
                {"key": e.key, "label": e.label, "wert": round(w * 100)}
                for e, w in self.staerken()
            ],
            "rollen": self.rollen,
            "rollen_ueberhang": self.rollen_ueberhang,
            "unbekannt": [b.name for b in self.unbekannt],
        }
