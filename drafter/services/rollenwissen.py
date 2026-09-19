# -*- coding: utf-8 -*-
"""Was sich aus Rolle und Faehigkeiten ableiten laesst - und was nicht.

Rund 101 Brawler haben eine gepflegte Draft-Rolle (`draft_rolle`) und
markierte Faehigkeiten (`draft_faehigkeiten`), aber nur etwa 20 ein
volles Attributprofil. Bisher fielen damit fuer 86 Brawler saemtliche
Draft-Fit-Komponenten aus - sie konnten praktisch nie oben stehen, egal
wie gut sie liefen. Ein fehlendes Profil heisst aber "wir wissen weniger
ueber ihn", nicht "er ist schlechter".

**Die Regel dieses Moduls: die Rolle liefert die Richtung, nie die Zahl.**

    anti_tank  ->  "kann Tank-Abdeckung liefern"      JA
    anti_tank  ->  attributes["anti_tank"] = 0.85     NEIN

Der Betrag kommt deshalb immer von der anderen Seite der Rechnung, die
gemessen oder gepflegt vorliegt:

* beim Map-Fit aus den **Anforderungsgewichten der Map** (gepflegt),
* beim Teambedarf aus der **Dringlichkeit der Luecken unseres Teams**
  (aus den Profilen der bereits gepickten Brawler gerechnet),
* bei der Redundanz aus der **Zahl gleichrollige Picks** (gezaehlt).

Der Kandidat steuert nur ein Ja oder Nein bei. Es entsteht keine Zahl,
die vorher nicht dastand.

Zusaetzlich ist der Ausschlag gedeckelt (`FACHWISSEN_MAX_AUSSCHLAG`): eine
Rolle ist eine Schublade, ein Profil eine Beschreibung. Wer nur in einer
Schublade liegt, soll nicht denselben Ausschlag bekommen koennen wie
jemand, dessen Eigenschaften einzeln gepflegt sind.
"""

from drafter import config
from drafter.services.scoring import klemme, z_werte


def rolle(brawler):
    return (getattr(brawler, "draft_rolle", "") or "") or None


def deckt(brawler):
    """Die Eigenschaften, die dieser Brawler qualitativ adressiert.

    Rolle UND gepflegte Faehigkeiten, als Vereinigung. Die Faehigkeiten
    ERSETZEN die Rolle nicht - sonst konnte ein gepflegtes `wallbreak`
    den Wert sogar senken, weil die Rolle mehr Posten beruehrt als eine
    einzelne Faehigkeit. Eine zusaetzlich belegte Faehigkeit darf nie
    schlechter sein als keine.

    Weiterhin entsteht kein Zahlenwert: hier steht nur, WELCHE Posten er
    beruehrt. Wie schwer die wiegen, sagt der Modus.
    """
    keys = set(config.ROLLE_DECKT.get(rolle(brawler), ()))
    return keys | faehigkeiten_keys(brawler)


def faehigkeiten_keys(brawler):
    """Eigenschaften, die aus gepflegten Faehigkeiten belegt sind."""
    keys = set()
    for faehigkeit in (getattr(brawler, "draft_faehigkeiten", None) or ()):
        keys.update(config.FAEHIGKEIT_ATTRIBUTE.get(faehigkeit, ()))
    return keys


def hat_fachwissen(brawler):
    """Gibt es ueberhaupt gepflegtes Fachwissen - Rolle oder Faehigkeit?"""
    return bool(deckt(brawler))


def anforderungsdeckung(brawler, anforderungen):
    """Anteil des Anforderungsgewichts, den diese Rolle adressiert (0-1).

    Das Gewicht stammt aus der Map, die Rolle sagt nur, welche Posten sie
    beruehrt. Ohne Anforderungen gibt es keine Aussage.
    """
    gesamt = sum(anforderungen.values())
    if gesamt <= 0 or not hat_fachwissen(brawler):
        return None
    abgedeckt = deckt(brawler)
    return sum(w for k, w in anforderungen.items() if k in abgedeckt) / gesamt


def lueckendeckung(brawler, luecken):
    """Anteil der Luecken-Dringlichkeit, den diese Rolle adressiert (0-1).

    `luecken` ist [(Eigenschaft, Dringlichkeit)] aus der Teamanalyse - die
    Dringlichkeit kommt aus den Profilen der schon gepickten Brawler.
    """
    if not hat_fachwissen(brawler) or not luecken:
        return None
    gesamt = sum(d for _, d in luecken)
    if gesamt <= 0:
        return None
    abgedeckt = deckt(brawler)
    return sum(d for e, d in luecken if e.key in abgedeckt) / gesamt


def rollen_z(werte):
    """Die Rohanteile im Feld der Rollen-Kandidaten zentrieren und deckeln.

    Eigenes Bezugsfeld, aber bei 0 zentriert wie das Profilfeld: keine
    der beiden Gruppen bekommt dadurch einen Vorsprung. Der Deckel haelt
    den Ausschlag unter dem eines gepflegten Profils.
    """
    z = z_werte(werte)
    grenze = config.FACHWISSEN_MAX_AUSSCHLAG
    return {k: klemme(v, -grenze, grenze) for k, v in z.items()}


def gleiche_rolle(kandidat, brawler_liste):
    """Wie viele der genannten Brawler haben dieselbe Draft-Rolle?"""
    eigene = rolle(kandidat)
    if eigene is None:
        return 0
    return sum(1 for b in brawler_liste if rolle(b) == eigene)


def faehigkeiten_gruende(kandidat, anforderungen):
    """Saetze, die sich aus markierten Faehigkeiten belegen lassen.

    Nur dort, wo die Map die Eigenschaft ueberhaupt verlangt - sonst waere
    es eine Aufzaehlung statt einer Begruendung.
    """
    saetze = []
    for faehigkeit, keys in config.FAEHIGKEIT_ATTRIBUTE.items():
        if not kandidat.kann(faehigkeit):
            continue
        treffer = [k for k in keys if anforderungen.get(k, 0.0) >= 0.4]
        if treffer:
            saetze.append((faehigkeit, treffer))
    return saetze
