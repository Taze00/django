# -*- coding: utf-8 -*-
"""Die Mechanikschicht: was ein Brawler objektiv HAT - fuer alle 106.

Der Unterschied zu `attributes`: dort steht eine Meinung auf einer Skala
von 0 bis 100 ("zone_control 85"), hier steht eine Tatsache ("hat
Wallbreak: ja"). Tatsachen lassen sich nachschlagen, ueberleben Patches
und gelten fuer jeden Brawler gleich - Meinungen gibt es nur fuer die
zwanzig, die am 2026-09-14 von Hand eingetragen wurden.

**Gepflegt wird nichts doppelt.** Die Fachquelle (`draft_rolle`,
`draft_faehigkeiten` aus `fachdaten/role_ability_map.py`) traegt einen
Teil dieser Information bereits; dieses Modul liest sie und normalisiert
sie, statt eine zweite Tabelle zu verlangen. `Brawler.mechanik` steht
daneben fuer das, was spaeter von Hand nachgetragen wird - heute leer.

**Was die Quelle nicht sagt, bleibt Unknown.** Die Faehigkeitslisten
nennen, WER etwas hat; ob sie vollstaendig sind, ist nicht belegt. Ein
nicht genannter Brawler gilt deshalb als "unbekannt", nicht als "hat es
nicht". Das ist der Unterschied zwischen einer Liste und einem
Verzeichnis, und er entscheidet, ob aus Unwissen eine Behauptung wird.
"""

from drafter import attributes as attr

# --- Das Vokabular der Schicht -------------------------------------------
BOOLESCH = (
    "has_healing", "has_wallbreak", "has_knockback", "has_stun", "has_slow",
    "has_pierce", "has_shield",
)
KATEGORIEN = {
    "range_category": ("short", "medium", "long", "sniper"),
    "engage_mechanic": ("none", "dash", "jump", "teleport", "other"),
    "mobility_category": ("low", "medium", "high"),
}
SCHLUESSEL = tuple(BOOLESCH) + tuple(KATEGORIEN)

# Welche dieser Angaben objektiv nachschlagbar sind (Stufe MECHANIK) und
# welche eine Einordnung bleiben (Stufe FACHQUELLE).
OBJEKTIV = frozenset(BOOLESCH) | {"range_category"}

# --- Ableitung aus der Fachquelle ----------------------------------------
# Jede Zeile ist eine DEFINITORISCHE Gleichsetzung, keine Schaetzung:
# wer in der Faehigkeitsliste "wallbreak" steht, bricht Waende.
AUS_FAEHIGKEIT = {
    "wallbreak": {"has_wallbreak": True},
    "pierce": {"has_pierce": True},
}
# knockback_stun nennt zwei Mechaniken in einem Eintrag. Welche der
# beiden gemeint ist, sagt die Quelle nicht - beide einzeln blieben also
# Unknown. Festgehalten wird nur, was wirklich dasteht.
AUS_FAEHIGKEIT_UNSCHARF = {"knockback_stun": ("has_knockback", "has_stun")}

AUS_ROLLE = {
    "sniper": {"range_category": "sniper"},
}

# Welche Eigenschaft des alten Vokabulars dieselbe Sache meint - nur dort,
# wo die Gleichsetzung eindeutig ist. `healing > 0` heisst "heilt", und
# ein ausdrueckliches 0 heisst "heilt nicht".
ATTRIBUT_ZU_MECHANIK = {
    "healing": "has_healing",
    "wallbreak": "has_wallbreak",
    "knockback": "has_knockback",
    "stun": "has_stun",
    "slow": "has_slow",
}
MECHANIK_ZU_ATTRIBUT = {v: k for k, v in ATTRIBUT_ZU_MECHANIK.items()}

# Wie stark eine bloss bejahte Mechanik im alten 0-1-Raum zaehlt. Bewusst
# in der Mitte: "hat es" ist etwas anderes als "ist darin herausragend",
# und mehr sagt eine Ja/Nein-Angabe nicht her.
VORHANDEN = 0.55


def ist_objektiv(schluessel):
    """Ist diese Angabe nachschlagbar (MECHANIK) oder eine Einordnung?

    Nimmt sowohl einen Mechanikschluessel (`has_healing`) als auch den
    alten Attributnamen (`healing`) - uebersetzt wird vom Attribut zur
    Mechanik, nicht umgekehrt.
    """
    return ATTRIBUT_ZU_MECHANIK.get(schluessel, schluessel) in OBJEKTIV


def mechaniken(brawler):
    """Alles, was ueber die Mechanik dieses Brawlers bekannt ist.

    {schluessel: True/False/"kategorie"} - **nur bekannte Eintraege**.
    Was fehlt, ist unbekannt; es steht bewusst nicht mit None drin,
    damit niemand versehentlich darueber iteriert.
    """
    bekannt = {}

    # 1. Von Hand gepflegte Mechanik hat Vorrang - heute leer, spaeter
    #    der Ort, an dem Nachgetragenes steht.
    for k, v in (getattr(brawler, "mechanik", None) or {}).items():
        if k in SCHLUESSEL and v is not None:
            bekannt[k] = v

    # 2. Fachquelle: Faehigkeiten und Rolle.
    faehigkeiten = set(brawler.draft_faehigkeiten or [])
    for name, eintraege in AUS_FAEHIGKEIT.items():
        if name in faehigkeiten:
            for k, v in eintraege.items():
                bekannt.setdefault(k, v)
    for name, paar in AUS_FAEHIGKEIT_UNSCHARF.items():
        if name in faehigkeiten:
            # Eines von beiden - welches, sagt die Quelle nicht.
            bekannt.setdefault("hat_knockback_oder_stun", True)
    for k, v in AUS_ROLLE.get(brawler.draft_rolle or "", {}).items():
        bekannt.setdefault(k, v)

    # 3. Das alte Profil, aber nur als Ja/Nein - nie als Zahl.
    for attribut, schluessel in ATTRIBUT_ZU_MECHANIK.items():
        if brawler.bekannt(attribut):
            bekannt.setdefault(schluessel, brawler.wert(attribut) > 0)
    return bekannt


def sagt_etwas_zu(brawler, attribut_key):
    """Weiss die Mechanikschicht etwas ueber diese alte Eigenschaft?"""
    schluessel = ATTRIBUT_ZU_MECHANIK.get(attribut_key)
    return bool(schluessel) and schluessel in mechaniken(brawler)


def attributwert(brawler, attribut_key):
    """Die Mechanik als Wert im alten 0-1-Raum - oder None.

    Uebersetzt nur, was eindeutig uebersetzbar ist: eine bejahte
    Mechanik wird `VORHANDEN`, eine verneinte 0.0. Fuer alles andere
    gibt es hier nichts, und das ist richtig so - eine Rolle sagt nicht,
    wie gut jemand eine Zone haelt.
    """
    schluessel = ATTRIBUT_ZU_MECHANIK.get(attribut_key)
    if not schluessel:
        return None
    wert = mechaniken(brawler).get(schluessel)
    if wert is None:
        return None
    return VORHANDEN if wert else 0.0


def luecken(brawler):
    """Welche Mechanikangaben fehlen diesem Brawler noch?"""
    bekannt = mechaniken(brawler)
    return [k for k in SCHLUESSEL if k not in bekannt]


def uebersicht(brawler):
    """Zeile fuer die Audit-Matrix: Rolle, Faehigkeiten, Mechanik, Luecken."""
    return {
        "slug": brawler.slug,
        "name": brawler.name,
        "rolle": brawler.draft_rolle or "",
        "faehigkeiten": list(brawler.draft_faehigkeiten or []),
        "mechanik": mechaniken(brawler),
        "fehlt": luecken(brawler),
    }
