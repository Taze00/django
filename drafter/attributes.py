"""Das Vokabular des Drafters.

Eine Liste, drei Verwendungen - das ist die zentrale Entwurfsentscheidung
dieser App:

1. **Brawler** tragen zu jedem Schluessel einen Wert 0-100
   ("wie stark bin ich darin").
2. **Maps** tragen zu denselben Schluesseln einen Wert 0-100
   ("wie wichtig ist das hier").
3. **Teams** bekommen daraus ein Profil und einen Bedarf
   ("was fehlt uns noch").

Dadurch ist Map-Fit ein gewichtetes Skalarprodukt, Team-Coverage ein
Vergleich zweier Vektoren und Redundanz ein Ueberschuss im selben Raum.
Waeren das drei getrennte Vokabulare, muesste jede Kombination von Hand
verdrahtet werden.

Neue Eigenschaft? Hier eintragen, sonst nirgends. Modelle validieren
gegen diese Liste, das Admin baut daraus seine Formulare, die Engine
iteriert darueber. Ein Tippfehler in einem JSONField faellt damit beim
Speichern auf und nicht erst in einer stillen Fehlempfehlung.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Eigenschaft:
    """Ein Schluessel des Vokabulars.

    `label` ist Anzeigetext (UI, Admin, Coach-Saetze), `gruppe` sortiert
    die Darstellung, `knapp` markiert Eigenschaften, bei denen *Fehlen*
    ein Team hart bestraft - daran haengt die Coverage-Luecken-Logik.
    """

    key: str
    label: str
    gruppe: str
    knapp: bool = False
    beschreibung: str = ""


# --- Reichweite ----------------------------------------------------------
# Bewusst drei Baender statt einer Zahl: ein Brawler kann auf mittlerer
# Distanz stark und auf kurzer wehrlos sein. Eine einzelne "range"-Zahl
# koennte das nicht ausdruecken.
_REICHWEITE = [
    Eigenschaft("long_range", "Lange Reichweite", "Reichweite", knapp=True),
    Eigenschaft("mid_range", "Mittlere Reichweite", "Reichweite"),
    Eigenschaft("close_range", "Nahkampf", "Reichweite"),
]

# --- Schaden -------------------------------------------------------------
_SCHADEN = [
    Eigenschaft("burst_damage", "Burst-Schaden", "Schaden"),
    Eigenschaft("sustained_damage", "Dauerschaden", "Schaden"),
    Eigenschaft("objective_damage", "Schaden aufs Ziel", "Schaden",
                beschreibung="Safe, Tresor, Ball, Heist-Objekte"),
    # Hiess bis zum 2026-09-18 "safe_damage". Der Name war gefaehrlich:
    # in einem Spiel mit einem Modus namens Heist las sich "safe damage"
    # wie "Schaden am Safe" - gemeint war immer das Gegenteil, naemlich
    # Schaden, den man selbst gefahrlos austeilt. Schaden am Heist-Safe
    # heisst `objective_damage`.
    Eigenschaft("safe_poke", "Sicherer Schaden", "Schaden",
                beschreibung="Schaden aus sicherer Position, ohne eigenes Risiko"),
    Eigenschaft("poke", "Poke", "Schaden"),
]

# --- Kontrolle -----------------------------------------------------------
_KONTROLLE = [
    Eigenschaft("area_control", "Flächenkontrolle", "Kontrolle", knapp=True),
    Eigenschaft("lane_control", "Lane-Kontrolle", "Kontrolle"),
    Eigenschaft("mid_control", "Mid-Kontrolle", "Kontrolle", knapp=True),
    Eigenschaft("zone_control", "Zonen verweigern", "Kontrolle"),
    Eigenschaft("crowd_control", "Crowd Control", "Kontrolle"),
    Eigenschaft("knockback", "Rückstoß", "Kontrolle"),
    Eigenschaft("slow", "Verlangsamung", "Kontrolle"),
    Eigenschaft("stun", "Betäubung", "Kontrolle"),
]

# --- Antworten auf gegnerische Archetypen --------------------------------
# Diese vier sind der Kern des "drei Tanks sind kein Team"-Problems:
# fehlen sie, hat der Gegner eine Gewinnbedingung, auf die wir keine
# Antwort haben. Alle sind deshalb `knapp`.
_ANTWORTEN = [
    Eigenschaft("anti_tank", "Anti-Tank", "Antworten", knapp=True),
    Eigenschaft("anti_assassin", "Anti-Assassin", "Antworten", knapp=True),
    Eigenschaft("anti_thrower", "Anti-Thrower", "Antworten", knapp=True),
    Eigenschaft("backline_pressure", "Druck auf die Backline", "Antworten", knapp=True),
]

# --- Ueberleben und Raum halten ------------------------------------------
_ROBUSTHEIT = [
    Eigenschaft("tankiness", "Robustheit", "Robustheit"),
    Eigenschaft("frontline", "Frontline", "Robustheit", knapp=True),
    Eigenschaft("survivability", "Überlebensfähigkeit", "Robustheit"),
    Eigenschaft("disengage", "Lösen aus Kämpfen", "Robustheit"),
    Eigenschaft("peel", "Peel für Mitspieler", "Robustheit", knapp=True),
]

# --- Bewegung ------------------------------------------------------------
_BEWEGUNG = [
    Eigenschaft("mobility", "Mobilität", "Bewegung", knapp=True),
    Eigenschaft("engage", "Angriff einleiten", "Bewegung"),
]

# --- Werkzeuge -----------------------------------------------------------
_WERKZEUG = [
    Eigenschaft("wallbreak", "Wände brechen", "Werkzeuge"),
    Eigenschaft("bush_control", "Buschkontrolle", "Werkzeuge"),
    Eigenschaft("vision", "Sicht verschaffen", "Werkzeuge"),
    Eigenschaft("healing", "Heilung", "Werkzeuge"),
    Eigenschaft("support", "Support", "Werkzeuge"),
]

EIGENSCHAFTEN = (
    _REICHWEITE + _SCHADEN + _KONTROLLE + _ANTWORTEN
    + _ROBUSTHEIT + _BEWEGUNG + _WERKZEUG
)

# Nachschlagewerke - einmal gebaut, ueberall benutzt.
EIGENSCHAFT_NACH_KEY = {e.key: e for e in EIGENSCHAFTEN}
ATTRIBUT_KEYS = tuple(e.key for e in EIGENSCHAFTEN)
KNAPPE_KEYS = tuple(e.key for e in EIGENSCHAFTEN if e.knapp)
GRUPPEN = tuple(dict.fromkeys(e.gruppe for e in EIGENSCHAFTEN))


# --- Draft-Werte ---------------------------------------------------------
# Kein Teil des Coverage-Vokabulars: diese Werte beschreiben nicht, was
# ein Brawler im Kampf kann, sondern wie er sich im *Draft* verhaelt.
# Sie gehen in die Pick-Order-Komponente ein, nie in Map-Fit oder
# Coverage - ein Brawler soll keine Teamluecke schliessen, nur weil er
# ein guter Blind Pick ist.

@dataclass(frozen=True)
class Draftwert:
    key: str
    label: str
    beschreibung: str = ""


DRAFTWERTE = [
    Draftwert("blind_pick_value", "Blind Pick",
              "Wie sicher ist er, wenn noch nichts vom Gegner bekannt ist"),
    Draftwert("early_pick_value", "Früher Pick",
              "Wert in den ersten Picks, wenn noch wenig feststeht"),
    Draftwert("last_pick_value", "Last Pick",
              "Wert als letzter Pick mit voller Information"),
    Draftwert("counter_pick_value", "Counter Pick",
              "Wie stark bestraft er gezielt bestimmte Picks"),
    Draftwert("flexibility_value", "Flexibilität",
              "Wie viele Rollen und Maps er abdecken kann"),
    Draftwert("counterability", "Konterbarkeit",
              "Wie leicht ihn der Gegner selbst kontern kann - hoch = leicht konterbar"),
]

DRAFTWERT_NACH_KEY = {d.key: d for d in DRAFTWERTE}
DRAFTWERT_KEYS = tuple(d.key for d in DRAFTWERTE)

# Fehlt ein Draftwert, ist 50 die Annahme "durchschnittlich" - nicht 0.
# 0 hiesse "voellig unbrauchbar als Blind Pick" und wuerde jeden Brawler
# bestrafen, dessen Datensatz einfach noch unvollstaendig ist.
DRAFTWERT_STANDARD = 50


# --- Rollen --------------------------------------------------------------
# Grobe Archetypen. Sie ersetzen die Eigenschaften nicht, sondern
# buendeln sie fuer Anzeige, Filter und Redundanzpruefung ("schon zwei
# Assassinen im Team").
ROLLEN = [
    ("tank", "Tank"),
    ("assassin", "Assassin"),
    ("marksman", "Marksman"),
    ("sniper", "Sniper"),
    ("thrower", "Thrower"),
    ("controller", "Controller"),
    ("support", "Support"),
    ("damage", "Damage Dealer"),
    ("aggro", "Aggro"),
]

ROLLEN_KEYS = tuple(k for k, _ in ROLLEN)


# =========================================================================
# Draft-Rollen und Zusatzfaehigkeiten (gepflegte Fachquelle)
# =========================================================================
# Getrennt von ROLLEN, weil es eine andere Frage beantwortet: ROLLEN sind
# der Archetyp aus dem Katalog ("Marksman"), DRAFT_ROLLEN die Aufgabe im
# Draft aus der Role-&-Ability-Map ("Anti-Tank"). Beides nebeneinander zu
# fuehren ist Absicht - ein Marksman kann im Draft Anti-Tank sein.
#
# Diese Angaben sagen NICHTS darueber, wie stark ein Brawler gerade ist.
# Sie sind stabiles Draft-Wissen, keine Meta.

DRAFT_ROLLEN = [
    ("thrower", "Thrower"),
    ("tank", "Tank"),
    ("space_maker", "Space Maker / Assassin"),
    ("anti_tank", "Anti-Tank"),
    ("support", "Support"),
    ("sniper", "Sniper"),
    ("control", "Control"),
]
DRAFT_ROLLEN_KEYS = tuple(k for k, _ in DRAFT_ROLLEN)
DRAFT_ROLLEN_LABEL = dict(DRAFT_ROLLEN)

# Die Farblegende der Map. "weiss" ist keine Faehigkeit, sondern ihr
# Fehlen - es wird deshalb nicht gespeichert, sondern ist die leere Liste.
DRAFT_FAEHIGKEITEN = [
    ("good_hyper", "Gute Hypercharge"),
    ("knockback_stun", "Rückstoß / Betäubung"),
    ("wallbreak", "Wände brechen"),
    ("pierce", "Durchdringender Schaden"),
    ("special", "Besondere Fähigkeit"),
]
DRAFT_FAEHIGKEITEN_KEYS = tuple(k for k, _ in DRAFT_FAEHIGKEITEN)
DRAFT_FAEHIGKEITEN_LABEL = dict(DRAFT_FAEHIGKEITEN)


# =========================================================================
# Map-Merkmale
# =========================================================================
# Beschreibende Merkmale einer Map (0-100 bzw. Anzahl). Anders als die
# `requirements` sagen sie nicht, was hier ZAEHLT, sondern wie die Map
# AUSSIEHT - daraus leiten Coach, Builds und Ableitungen ab.
MAP_TRAITS = [
    ("openness", "Offenheit", "0 = verwinkelt, 100 = freies Feld"),
    ("wall_density", "Wanddichte", "Wie viel Deckung steht herum"),
    ("bush_density", "Buschdichte", "Sicht und Hinterhalte"),
    ("choke_points", "Engstellen", "Wie stark Wege gebuendelt sind"),
    ("lane_count", "Lanes", "Anzahl paralleler Wege, meist 2-3"),
]
MAP_TRAIT_KEYS = tuple(k for k, _, _ in MAP_TRAITS)
MAP_TRAIT_LABEL = {k: l for k, l, _ in MAP_TRAITS}


def pruefe_map_traits(werte):
    """Wie pruefe_attribute, aber fuer Map-Merkmale. Liste von Fehlertexten."""
    fehler = []
    if not isinstance(werte, dict):
        return ["traits: erwartet ein Objekt"]
    for key, wert in werte.items():
        if key not in MAP_TRAIT_KEYS:
            fehler.append(f"traits: unbekannter Schlüssel '{key}'")
            continue
        try:
            zahl = float(wert)
        except (TypeError, ValueError):
            fehler.append(f"traits.{key}: keine Zahl ({wert!r})")
            continue
        grenze = 10 if key == "lane_count" else 100
        if not 0 <= zahl <= grenze:
            fehler.append(f"traits.{key}: {zahl} liegt nicht zwischen 0 und {grenze}")
    return fehler
ROLLEN_LABEL = dict(ROLLEN)


# Alte Schluesselnamen -> heutige. Damit laesst sich eine Altdatei oder
# eine alte Fixture einlesen, ohne dass jemand von Hand sucht und ersetzt.
# Die Migration 0013 hat die Datenbank bereits umgestellt.
ALTE_SCHLUESSEL = {"safe_damage": "safe_poke"}


def umbenennen(werte):
    """Alte Attributschluessel auf die heutigen abbilden."""
    if not isinstance(werte, dict):
        return werte
    return {ALTE_SCHLUESSEL.get(k, k): v for k, v in werte.items()}


def pruefe_attribute(werte, erlaubt=ATTRIBUT_KEYS, feldname="attributes"):
    """Ein JSON-Dict gegen das Vokabular pruefen.

    Gibt eine Liste von Fehlertexten zurueck - leer heisst in Ordnung.
    Bewusst kein Exception-Wurf: Modelle wollen daraus ein
    ValidationError bauen, das Seed-Kommando lieber eine Warnung.
    """
    fehler = []
    if not isinstance(werte, dict):
        return [f"{feldname}: erwartet ein Objekt, bekommen {type(werte).__name__}"]

    for key, wert in werte.items():
        if key not in erlaubt:
            fehler.append(f"{feldname}: unbekannter Schlüssel '{key}'")
            continue
        if not isinstance(wert, (int, float)) or isinstance(wert, bool):
            fehler.append(f"{feldname}['{key}']: erwartet eine Zahl, bekommen {wert!r}")
            continue
        if not 0 <= wert <= 100:
            fehler.append(f"{feldname}['{key}']: {wert} liegt außerhalb 0-100")
    return fehler


def als_vektor(werte, keys=ATTRIBUT_KEYS, standard=0.0):
    """JSON-Dict zu vollstaendigem Vektor 0-1 in fester Reihenfolge.

    Fehlende Schluessel werden zu `standard`. Die feste Reihenfolge ist
    wichtig: die Engine rechnet spaeter paarweise ueber zwei Vektoren.
    """
    return {k: float(werte.get(k, standard)) / 100.0 for k in keys}
