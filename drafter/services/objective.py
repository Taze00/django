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

**Quellenprioritaet, streng von oben nach unten:**

    1. gemessene Modus-Eignung      (Belege)
    2. gepflegte Faehigkeiten       (Fachquelle, qualitativ)
    3. Draft-Rolle                  (Fachquelle, noch groeber)
    4. Unknown                      (nicht verfuegbar)

Eine Stufe wird nur benutzt, wenn die darueber nichts liefert. Gemessene
Evidenz schlaegt gepflegtes Wissen - das ist der ganze Punkt.

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
    faehigkeiten: tuple = ()
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
            "faehigkeiten": list(self.faehigkeiten),
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
    return {
        "differenz": (rate_modus - rate_global) * gewicht,
        "modus_rate": rate_modus,
        "global_rate": rate_global,
        "sd": sd_modus,
        "spiele": int(n_modus),
    }


def _qualitativ(brawler, anforderungen):
    """(Anteil, belegte Faehigkeiten) - ohne einen Zahlenwert zu erfinden.

    Der Anteil kommt aus `rollenwissen.deckt()`: Rolle UND gepflegte
    Faehigkeiten gemeinsam. Eine markierte Faehigkeit sagt "kann er",
    nicht "wie gut"; der Betrag kommt ausschliesslich aus dem
    Anforderungsgewicht des Modus. COLT traegt `wallbreak` - verlangt der
    Modus Waende brechen, zaehlt das, und es wird trotzdem nie eine Zahl
    wie 0.8 daraus.
    """
    anteil = rollenwissen.anforderungsdeckung(brawler, anforderungen)
    if anteil is None:
        return None, ()
    treffer = tuple(sorted(
        f for f in (brawler.draft_faehigkeiten or ())
        if any(anforderungen.get(k, 0.0) > 0
               for k in config.FAEHIGKEIT_ATTRIBUTE.get(f, ()))
    ))
    return anteil, treffer


def fuer_pool(kandidaten, raum, anforderungen, patch=None):
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
    roh_qualitativ, faehigkeiten_je_id = {}, {}
    for b in kandidaten:
        if b.id in messungen:
            continue
        anteil, faehigkeiten = _qualitativ(b, anforderungen)
        if anteil is not None:
            roh_qualitativ[b.id] = anteil
            faehigkeiten_je_id[b.id] = faehigkeiten
    z_qualitativ = rollenwissen.rollen_z(roh_qualitativ)

    ergebnis = {}
    for b in kandidaten:
        m = messungen.get(b.id)
        if m is not None:
            nenner = config.STAERKE_FELD_K * (streuung ** 2 + m["sd"] ** 2) ** 0.5
            wert = klemme(m["differenz"] / nenner) if nenner > 0 else 0.0
            richtung = "besser" if wert >= 0 else "schlechter"
            ergebnis[b.id] = Auskunft(
                wert=wert, quelle=MESSUNG, verfuegbar=True,
                differenz=m["differenz"], modus_rate=m["modus_rate"],
                global_rate=m["global_rate"], modus_spiele=m["spiele"],
                text=(f"läuft in diesem Modus {richtung} als sonst "
                      f"({m['modus_rate']:.0%} gegen {m['global_rate']:.0%} "
                      f"insgesamt, {m['spiele']} Partien)"),
            )
        elif b.id in z_qualitativ:
            faehigkeiten = faehigkeiten_je_id.get(b.id, ())
            text = (f"{b.draft_rolle_label} berührt das Ziel dieses Modus"
                    if b.draft_rolle_label else "gepflegtes Fachwissen zum Ziel")
            if faehigkeiten:
                text += f"; gepflegt: {', '.join(faehigkeiten)}"
            ergebnis[b.id] = Auskunft(
                wert=z_qualitativ[b.id], quelle=quellen.FACHWISSEN, verfuegbar=True,
                faehigkeiten=faehigkeiten, text=text,
            )
        else:
            ergebnis[b.id] = Auskunft()
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
