# -*- coding: utf-8 -*-
"""OBJECTIVE FIT - passt ein Brawler zum ZIEL dieses Modus?

Nicht "ist er stark" (das ist CURRENT STRENGTH) und nicht "passt er zur
Geometrie dieser Map" (das ist die allgemeine Map-Passung), sondern:
**taugt er fuer das, was in diesem Modus gewonnen wird.**

Warum das eine eigene Groesse braucht: auf Safe Zone stand BROCK auf
Platz 1 mit +17 Map-Fit-Punkten aus seinem gepflegten Profil - waehrend
221 gemessene Partien auf genau dieser Map 40,7 % Siegquote zeigten und
624 Heist-Partien 43,3 %. Ein Profil behauptete einen Modus-Fit, den
hunderte Partien widerlegten, und nichts im Modell konnte widersprechen.

**Quellen, stetig gestaffelt statt hart priorisiert:**

    Messung (Modus-Eignung)  mit Gewicht  w = n / (n + K)
    Fachwissen (Rolle, Faehigkeiten)  mit  (1 - w) * Daempfung
    keines von beidem                     ->  Unknown, neutral

Die harte Prioritaet von vorher hatte eine Kante: die qualitative
Obergrenze war groesser als fast jedes gemessene Signal, und MR. P stand
auf Gem Grab mit NULL Modus-Partien vor AMBER mit 313. Jetzt zieht sich
das Fachwissen mit wachsender Stichprobe von selbst zurueck, ohne
Schwellenwert. Zahlen und Begruendung: config.OBJECTIVE_EVIDENZ_K.

**Stufe 1: die Modus-Eignung ist eine DIFFERENZ.**

    Modus-Eignung = geschaetzte Modus-Rate - geschaetzte globale Rate

Nicht die Modus-Rate selbst: die enthaelt, wie stark ein Brawler
allgemein ist, und das steht schon in CURRENT STRENGTH. Die Differenz
sagt etwas anderes - "laeuft er HIER besser als sonst". COLT: global
49,5 %, Heist 52,8 % -> +3,3 Punkte Modus-Eignung. BROCK: global 50,2 %,
Heist 43,3 % -> -6,9.

Geschaetzt wird mit demselben Beta-Binomial wie ueberall (services/
staerke.py), als Kette: die globale Rate ist der Prior der Modus-Rate.
Damit schrumpft die DIFFERENZ bei kleiner Modus-Stichprobe von selbst
gegen null - wer zehn Partien im Modus hat, bekommt keine Modus-Aussage,
ohne dass es dafuer eine Schwelle braucht. Zeitliche Abwertung und
Patchgewicht gelten wie fuer jede andere Statistik.

**Stufe 2 und 3 erfinden keine Zahlen.** Sie sagen nur, welche der
geforderten Eigenschaften ein Brawler ueberhaupt beruehrt; der Betrag
kommt aus dem Anforderungsgewicht des Modus. Siehe rollenwissen.py.

**Abgeleitete Zielgroessen.** `objective_sustain` und `objective_defense`
sind keine neuen Attribute, sondern Kombinationen vorhandener - ein Safe
faellt nicht von einem Burst, und wer den eigenen Safe haelt, tut das mit
Zonenkontrolle und Robustheit. Sie werden nur fuer Brawler mit Profil
gerechnet und dienen der Begruendung, nicht dem Score: der Score kommt
aus dem Anforderungsvektor, in dem dieselben Begriffe bereits stehen.
"""

from dataclasses import dataclass, field

from drafter import config
from drafter.models.base import NICHT_GEMESSEN
from drafter.services import quellen, rollenwissen, staerke
from drafter.services.patch_weighting import statistik_gewicht
from drafter.services.scoring import klemme

MESSUNG = quellen.MEASURED_PRIOR
UNBEKANNT = quellen.UNKNOWN


@dataclass
class Auskunft:
    """Objective Fit eines Kandidaten samt Herkunft."""

    wert: float = 0.0
    quelle: str = UNBEKANNT
    verfuegbar: bool = False
    # Rohsignal der Messung in Prozentpunkten (nur Stufe 1).
    differenz: float = None
    modus_rate: float = None
    global_rate: float = None
    modus_spiele: int = 0
    map_diff: float = None
    map_spiele: int = 0
    faehigkeiten: tuple = ()
    # Anteil, mit dem die Messung in den Wert eingeht (0-1). Der Rest ist
    # gedaempftes Fachwissen - siehe config.OBJECTIVE_EVIDENZ_K.
    mess_anteil: float = 0.0
    qualitativ: float = None
    # Welcher Zielaspekt des Modus ihn traegt, und wie weit er alle erfuellt.
    aspekt: str = ""
    aspekte: dict = field(default_factory=dict)
    text: str = ""

    def als_dict(self):
        return {
            "wert": round(self.wert, 3),
            "quelle": self.quelle,
            "verfuegbar": self.verfuegbar,
            "differenz_pp": (round(self.differenz * 100, 2)
                             if self.differenz is not None else None),
            "modus_rate": round(self.modus_rate, 4) if self.modus_rate else None,
            "global_rate": round(self.global_rate, 4) if self.global_rate else None,
            "modus_spiele": self.modus_spiele,
            "map_diff_pp": (round(self.map_diff * 100, 2)
                            if self.map_diff is not None else None),
            "map_spiele": self.map_spiele,
            "faehigkeiten": list(self.faehigkeiten),
            "mess_anteil": round(self.mess_anteil, 3),
            "aspekt": self.aspekt,
            "aspekte": {k: round(v, 3) for k, v in (self.aspekte or {}).items()},
            "qualitativ": (round(self.qualitativ, 3)
                           if self.qualitativ is not None else None),
            "text": self.text,
        }


def _zaehlung(zeile):
    """(Spiele, Siege) einer gemessenen Zeile - roh, wie in staerke.py."""
    if zeile is None or zeile.source in NICHT_GEMESSEN or not (zeile.games or 0):
        return 0.0, 0.0
    spiele = float(zeile.games)
    if zeile.wins:
        return spiele, float(zeile.wins)
    rate = zeile.raw_rate if zeile.raw_rate is not None else zeile.adjusted_rate
    return (spiele, spiele * rate) if rate is not None else (0.0, 0.0)


def modus_eignung(brawler, raum, patch=None):
    """Differenz Modus-Rate minus globale Rate, beide Beta-Binomial geschaetzt.

    None, wenn es keine Modus- oder keine globale Zeile gibt. Die Kette
    (global ist Prior des Modus) sorgt dafuer, dass eine duenne
    Modus-Stichprobe von selbst gegen null laeuft.
    """
    zeilen = raum.ebenen(brawler)
    global_zeile = zeilen.get(staerke.GLOBAL)
    feiner = zeilen.get(staerke.MODUS)
    if global_zeile is None or feiner is None:
        return None

    n_global, s_global = _zaehlung(global_zeile)
    n_modus, s_modus = _zaehlung(feiner)
    if n_global <= 0 or n_modus <= 0:
        return None

    # Die Modus-Partien stecken in der globalen Zeile mit drin - sonst
    # zaehlte dieselbe Partie auf beiden Seiten der Differenz.
    n_rest = max(0.0, n_global - n_modus)
    s_rest = min(max(0.0, s_global - s_modus), n_rest)
    rate_global, sd_global = staerke.posterior(n_rest, s_rest)
    rate_modus, sd_modus = staerke.posterior(
        n_modus, s_modus, prior_rate=rate_global,
        prior_staerke=config.STAERKE_PRIOR_GLOBAL,
    )
    # Eine Differenz ist hoechstens so belastbar wie ihre schwaechere
    # Seite. Spielt ein Brawler AUSSCHLIESSLICH in diesem Modus, bleibt
    # als Vergleich nur der Prior - dann waere "Modus gegen 50 %" in
    # Wahrheit die aktuelle Staerke, nicht die Modus-Eignung. Also wird
    # die Differenz mit der Information der Basis gewichtet: keine Basis,
    # keine Aussage.
    referenz = staerke.prior_sd()
    basis_gewicht = max(0.0, min(1.0, 1.0 - sd_global / referenz)) if referenz else 0.0
    gewicht = statistik_gewicht(feiner, brawler, patch) * basis_gewicht
    differenz = (rate_modus - rate_global) * gewicht
    ergebnis = {
        "differenz": differenz,
        "modus_diff": differenz,
        "map_diff": 0.0,
        "modus_rate": rate_modus,
        "global_rate": rate_global,
        "sd": sd_modus,
        "spiele": int(n_modus),
        "map_spiele": 0,
        "map_rate": None,
    }

    # Die Map-Ebene ist derselbe Gedanke eine Stufe tiefer: laeuft er auf
    # DIESER Map besser als im Modus insgesamt? Die Modus-Rate ist ihr
    # Prior, also schrumpft auch dieser Zuwachs bei duenner Stichprobe von
    # selbst. Beide Differenzen sind Zuwaechse und ueberschneiden sich
    # nicht - zusammen sind sie "Map gegen global", zerlegt in zwei
    # Schritte. Mit CURRENT STRENGTH hat keiner von beiden zu tun: dort
    # steht das Niveau, hier der Unterschied zum eigenen Schnitt.
    karte = zeilen.get(staerke.MAP)
    if karte is not None:
        n_map, s_map = _zaehlung(karte)
        if n_map > 0:
            n_rest_modus = max(0.0, n_modus - n_map)
            s_rest_modus = min(max(0.0, s_modus - s_map), n_rest_modus)
            rate_modus_rest, sd_modus_rest = staerke.posterior(
                n_rest_modus, s_rest_modus, prior_rate=rate_global,
                prior_staerke=config.STAERKE_PRIOR_GLOBAL)
            rate_map, sd_map = staerke.posterior(
                n_map, s_map, prior_rate=rate_modus_rest,
                prior_staerke=config.STAERKE_PRIOR_GLOBAL)
            referenz_modus = staerke.prior_sd()
            basis_modus = max(0.0, min(1.0, 1.0 - sd_modus_rest / referenz_modus))
            map_gewicht = statistik_gewicht(karte, brawler, patch) * basis_modus
            ergebnis["map_diff"] = (rate_map - rate_modus_rest) * map_gewicht
            ergebnis["differenz"] = differenz + ergebnis["map_diff"]
            ergebnis["map_rate"] = rate_map
            ergebnis["map_spiele"] = int(n_map)
            ergebnis["sd"] = (sd_modus ** 2 + sd_map ** 2) ** 0.5
    return ergebnis


def aspekte(modus):
    """Die benannten Zielaspekte eines Modus - oder {} wenn keine gepflegt.

    Daten aus config.MODUS_ZIELASPEKTE. Dieses Modul kennt keinen
    Modusnamen; es schlaegt nach, was zum Slug hinterlegt ist.
    """
    slug = getattr(modus, "slug", "") or ""
    return config.MODUS_ZIELASPEKTE.get(slug, {})


def aspekt_erfuellung(brawler, aspekte_tabelle):
    """Wie weit erfuellt er jeden Aspekt? {name: 0-1} - nur mit Profil.

    Gewichteter Mittelwert seiner Eigenschaften ueber die Schluessel des
    Aspekts. Ohne Profil gibt es nichts zu mitteln: `wert()` liefert dann
    ueberall 0, und das hiesse "kann nichts" statt "unbekannt".
    """
    if not brawler.hat_profil or not aspekte_tabelle:
        return {}
    ergebnis = {}
    for name, keys in aspekte_tabelle.items():
        gesamt = sum(keys.values())
        if gesamt <= 0:
            continue
        ergebnis[name] = sum(g * brawler.wert(k) for k, g in keys.items()) / gesamt
    return ergebnis


def aspekt_beruehrung(brawler, aspekte_tabelle):
    """Wie viel eines Aspekts beruehrt sein Fachwissen? {name: 0-1}.

    Fuer Brawler ohne Profil: Anteil des Aspektgewichts, den Rolle und
    gepflegte Faehigkeiten ueberhaupt adressieren. Wieder nur "beruehrt
    er das", nie "wie gut".
    """
    if not aspekte_tabelle:
        return {}
    abgedeckt = rollenwissen.deckt(brawler)
    if not abgedeckt:
        return {}
    ergebnis = {}
    for name, keys in aspekte_tabelle.items():
        gesamt = sum(keys.values())
        if gesamt <= 0:
            continue
        ergebnis[name] = sum(g for k, g in keys.items() if k in abgedeckt) / gesamt
    return ergebnis


def bester_aspekt(erfuellung):
    """(Name, Wert) des am besten erfuellten Aspekts.

    Bewusst das Maximum und nicht der Durchschnitt: ein Modus verlangt
    verschiedene Dinge, und niemand muss sie alle koennen. Ein starker
    Gem-Traeger ohne Zugriff auf den gegnerischen Traeger ist ein guter
    Pick - ein Mittelmass in allem dreien nicht unbedingt.
    """
    if not erfuellung:
        return None, None
    name = max(erfuellung, key=lambda k: erfuellung[k])
    return name, erfuellung[name]


def _qualitativ(brawler, anforderungen, modus=None):
    """(Anteil, belegte Faehigkeiten) - ohne einen Zahlenwert zu erfinden.

    Der Anteil kommt aus `rollenwissen.deckt()`: Rolle UND gepflegte
    Faehigkeiten gemeinsam. Eine markierte Faehigkeit sagt "kann er",
    nicht "wie gut"; der Betrag kommt ausschliesslich aus dem
    Anforderungsgewicht des Modus. COLT traegt `wallbreak` - verlangt der
    Modus Waende brechen, zaehlt das, und es wird trotzdem nie eine Zahl
    wie 0.8 daraus.
    """
    tabelle = aspekte(modus)
    treffer = tuple(sorted(
        f for f in (brawler.draft_faehigkeiten or ())
        if any(anforderungen.get(k, 0.0) > 0
               for k in config.FAEHIGKEIT_ATTRIBUTE.get(f, ()))
    ))
    if tabelle:
        # **Nur Rolle und Faehigkeiten, nie die Profilattribute.** Die
        # stecken schon vollstaendig in der anderen Haelfte von Map &
        # Modus; sie hier noch einmal zu lesen, waere dieselbe Evidenz
        # zweimal - derselbe Fehler, den wir zwischen Map-Fit und
        # Teambedarf beseitigt haben. Gemessen am 2026-09-19: zwei
        # profilierte Brawler sprangen dadurch von +6.8 auf +9.3
        # Map-Fit-Punkte und verdraengten den bestbelegten Kandidaten.
        erfuellung = aspekt_beruehrung(brawler, tabelle)
        name, wert = bester_aspekt(erfuellung)
        if name is not None:
            return wert, treffer, (name, erfuellung), quellen.FACHWISSEN
    anteil = rollenwissen.anforderungsdeckung(brawler, anforderungen)
    if anteil is None:
        return None, (), (None, {}), quellen.UNKNOWN
    return anteil, treffer, (None, {}), quellen.FACHWISSEN


def fuer_pool(kandidaten, raum, anforderungen, patch=None, modus=None):
    """Objective Fit fuer alle Kandidaten - feldrelativ skaliert.

    Feldrelativ aus demselben Grund wie ueberall: ein Unterschied von drei
    Prozentpunkten ist viel oder wenig, je nachdem, wie weit das Feld
    streut. Der Nullpunkt ist hier aber NICHT der Feldmedian, sondern die
    0 - "kein Unterschied zum eigenen Schnitt" ist eine Aussage, keine
    Konvention.
    """
    messungen = {}
    for b in kandidaten:
        m = modus_eignung(b, raum, patch)
        if m is not None:
            messungen[b.id] = m

    feld = staerke.Feld.aus([m["differenz"] for m in messungen.values()])
    streuung = max(feld.streuung, config.STAERKE_FELD_MIN_STREUUNG)

    # Die qualitativen Stufen zuerst sammeln: sie werden im Feld ihrer
    # eigenen Gruppe zentriert, nicht an einer festen Marke. Sonst haengt
    # ihr Vorzeichen daran, wie viele Posten ein Modus zufaellig auflistet.
    # Das Fachwissen wird fuer ALLE gerechnet, nicht nur fuer die ohne
    # Messung: es ist der Prior, zu dem eine duenne Messung zurueckfaellt.
    # EIN Feld. Die qualitative Seite ist hier immer dieselbe Groesse -
    # welchen Anteil des Ziels Rolle und Faehigkeiten beruehren - egal ob
    # der Brawler ausserdem ein Profil hat. Zwei getrennte Felder haetten
    # die Nullpunkte gegeneinander verschoben: gemessen am 2026-09-19
    # verschoben sich dadurch Spitzenplaetze in Modi, an denen gar nichts
    # geaendert worden war (bis zu 4 Scorepunkte).
    roh_qualitativ, faehigkeiten_je_id, aspekt_je_id, qual_quelle = {}, {}, {}, {}
    for b in kandidaten:
        anteil, faehigkeiten, aspekt_info, q = _qualitativ(b, anforderungen, modus)
        if anteil is None:
            continue
        roh_qualitativ[b.id] = anteil
        faehigkeiten_je_id[b.id] = faehigkeiten
        aspekt_je_id[b.id] = aspekt_info
        qual_quelle[b.id] = q
    z_qualitativ = rollenwissen.rollen_z(roh_qualitativ)

    ergebnis = {}
    for b in kandidaten:
        m = messungen.get(b.id)
        qual = z_qualitativ.get(b.id)
        if m is None and qual is None:
            ergebnis[b.id] = Auskunft()
            continue

        if m is not None:
            nenner = config.STAERKE_FELD_K * (streuung ** 2 + m["sd"] ** 2) ** 0.5
            mess_wert = klemme(m["differenz"] / nenner) if nenner > 0 else 0.0
            w = m["spiele"] / (m["spiele"] + config.OBJECTIVE_EVIDENZ_K)
        else:
            mess_wert, w = 0.0, 0.0

        qual_anteil = (1.0 - w) * config.OBJECTIVE_FACHWISSEN_DAEMPFUNG
        wert = klemme(w * mess_wert + qual_anteil * (qual or 0.0))

        faehigkeiten = faehigkeiten_je_id.get(b.id, ())
        if m is not None and w >= 0.5:
            quelle = MESSUNG
            richtung = "besser" if m["differenz"] >= 0 else "schlechter"
            text = (f"läuft in diesem Modus {richtung} als sonst "
                    f"({m['modus_rate']:.0%} gegen {m['global_rate']:.0%} insgesamt, "
                    f"{m['spiele']} Partien)")
            if m["map_spiele"] and abs(m["map_diff"]) > 0.005:
                wohin = "noch besser" if m["map_diff"] > 0 else "schlechter"
                text += (f"; auf dieser Map {wohin} "
                         f"({m['map_spiele']} Partien)")
        elif m is not None:
            quelle = quellen.schwaechste(
                [MESSUNG, qual_quelle.get(b.id, quellen.FACHWISSEN)])
            text = (f"{m['spiele']} Partien in diesem Modus - zu wenig für eine "
                    f"eigene Aussage, mit dem Fachwissen gemischt")
        else:
            quelle = qual_quelle.get(b.id, quellen.FACHWISSEN)
            text = (f"{b.draft_rolle_label} berührt das Ziel dieses Modus"
                    if b.draft_rolle_label else "gepflegtes Fachwissen zum Ziel")
            if faehigkeiten:
                text += f"; gepflegt: {', '.join(faehigkeiten)}"

        aspekt_name, erfuellung = aspekt_je_id.get(b.id, (None, {}))
        if aspekt_name:
            text += f"; stark als: {aspekt_name}"
        ergebnis[b.id] = Auskunft(
            aspekt=aspekt_name or "", aspekte=erfuellung,
            wert=wert, quelle=quelle, verfuegbar=True,
            differenz=m["differenz"] if m else None,
            modus_rate=m["modus_rate"] if m else None,
            global_rate=m["global_rate"] if m else None,
            modus_spiele=m["spiele"] if m else 0,
            map_diff=m["map_diff"] if m else None,
            map_spiele=m["map_spiele"] if m else 0,
            faehigkeiten=faehigkeiten, mess_anteil=w, qualitativ=qual,
            text=text,
        )
    return ergebnis


# --- Abgeleitete Zielgroessen (nur Erklaerung, kein eigener Score) -------
def objective_sustain(brawler):
    """Kann er ein Ziel nicht nur treffen, sondern auch abtragen?

    Ein Safe faellt nicht von einem Burst. Abgeleitet, kein neues
    Attribut - None, wenn kein Profil vorliegt.
    """
    if not brawler.hat_profil:
        return None
    return min(brawler.wert("objective_damage"), brawler.wert("sustained_damage"))


def objective_defense(brawler):
    """Wert beim VERTEIDIGEN des eigenen Ziels.

    Zonenkontrolle plus die Faehigkeit, davor stehen zu bleiben.
    Abgeleitet aus vorhandenen Eigenschaften.
    """
    if not brawler.hat_profil:
        return None
    halten = max(brawler.wert("survivability"), brawler.wert("frontline"))
    return min(1.0, 0.6 * brawler.wert("zone_control") + 0.4 * halten)
