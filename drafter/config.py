"""Alle Stellschrauben des Drafters an einem Ort.

Warum eine eigene Datei: die Gewichte sind **Annahmen, keine Wahrheit**.
Sie stehen hier als Startwerte, weil noch keine Matchdaten existieren,
aus denen man sie lernen koennte. Sobald es sie gibt, wird genau diese
Datei durch gelernte Werte ersetzt oder ueberschrieben - deshalb darf
keine dieser Zahlen im Engine-Code verstreut auftauchen.

Wer hier etwas aendert, aendert das Verhalten des gesamten Drafters.
Wer im Engine-Code eine Zahl schreibt, macht sie unauffindbar.
"""

from django.conf import settings


# =========================================================================
# Draft-Phasen
# =========================================================================
# Die Phase bestimmt, welche Gewichte gelten. Ein Brawler ist nicht
# "gut" oder "schlecht" - er ist gut *an dieser Stelle des Drafts*.

PHASE_BAN = "ban"
PHASE_FIRST_PICK = "first_pick"
PHASE_EARLY = "early"
PHASE_MID = "mid"
PHASE_LAST = "last"

PHASEN_LABEL = {
    PHASE_BAN: "Ban-Phase",
    PHASE_FIRST_PICK: "First Pick",
    PHASE_EARLY: "Früher Pick",
    PHASE_MID: "Mittlerer Pick",
    PHASE_LAST: "Last Pick",
}


# =========================================================================
# Score-Komponenten
# =========================================================================
# Jede Komponente liefert einen Wert in [-1, +1]. Das ist der Vertrag,
# auf den sich die gesamte Engine verlaesst (siehe services/scoring.py).
# Roh-Winrates, 0-100-Attribute und Prozentwerte werden NIE direkt
# addiert - jede Komponente normalisiert selbst.

K_MAP_MODE = "map_mode"
K_META = "meta"
K_COUNTER = "counter"
K_SYNERGY = "synergy"
K_TEAM_NEED = "team_need"
K_DRAFT_POSITION = "draft_position"
K_PERSONAL = "personal"
K_FLEXIBILITY = "flexibility"
K_REDUNDANCY = "redundancy"
K_WEAKNESS = "weakness"
K_UNCERTAINTY = "uncertainty"

KOMPONENTEN_LABEL = {
    K_MAP_MODE: "Map & Modus",
    K_META: "Meta",
    K_COUNTER: "Counter",
    K_SYNERGY: "Synergie",
    K_TEAM_NEED: "Teambedarf",
    K_DRAFT_POSITION: "Draft-Position",
    K_PERSONAL: "Deine Sicherheit",
    K_FLEXIBILITY: "Flexibilität",
    K_REDUNDANCY: "Redundanz",
    K_WEAKNESS: "Angreifbarkeit",
    K_UNCERTAINTY: "Datenlage",
}

# Komponenten, die nur abziehen koennen: ihr WERT liegt in [-1, 0],
# ihr GEWICHT ist wie bei allen anderen ein positiver Betrag.
STRAF_KOMPONENTEN = (K_REDUNDANCY, K_WEAKNESS, K_UNCERTAINTY)

# Reihenfolge der Aufschluesselung in der Oberflaeche.
#
# Bewusst fest und NICHT nach Betrag sortiert: die Tabelle soll bei
# jedem Brawler dieselben Zeilen an denselben Stellen haben, sonst kann
# man zwei Empfehlungen nicht vergleichen. Erst Bewertung, dann Strafen,
# Datenlage zuletzt - sie bewertet die anderen Komponenten.
#
# Das ist reine Darstellung. Die Gewichte stehen unveraendert oben; an
# dieser Liste zu drehen aendert nichts am Score.
KOMPONENTEN_REIHENFOLGE = (
    K_MAP_MODE, K_META, K_COUNTER, K_SYNERGY, K_TEAM_NEED,
    K_DRAFT_POSITION, K_FLEXIBILITY, K_PERSONAL,
    K_REDUNDANCY, K_WEAKNESS, K_UNCERTAINTY,
)


# =========================================================================
# Gewichtungsprofile je Phase
# =========================================================================
# Lies das als: "wie viel Prozent der Entscheidung macht das aus".
#
# ALLE Gewichte sind Betraege, auch die der Strafkomponenten. Das
# Vorzeichen steckt im Wert der Komponente: Redundanz, Angreifbarkeit und
# Datenlage liefern Werte in [-1, 0] und ziehen dadurch von selbst ab.
# Waeren Gewicht UND Wert negativ, wuerde aus jeder Strafe ein Bonus -
# ein Fehler, der beim Lesen des Codes nicht auffaellt, weil die Zahlen
# einzeln richtig aussehen.
#
# Die Bewertungsgewichte summieren sich je Profil auf 1.0, die Strafen
# kommen obendrauf - ein Kandidat kann also unter 0 fallen.
#
# Der Verlauf ueber die Phasen ist die eigentliche Aussage:
#   Counter   0.02 -> 0.30   (am Anfang kennt man niemanden)
#   Team Need 0.10 -> 0.26   (am Ende weiss man, was fehlt)
#   Flexibel  0.14 -> 0.02   (der letzte Pick muss sich nicht offenhalten)

PHASEN_GEWICHTE = {
    PHASE_FIRST_PICK: {
        K_MAP_MODE: 0.34,
        K_META: 0.22,
        K_COUNTER: 0.02,
        K_SYNERGY: 0.04,
        K_TEAM_NEED: 0.10,
        K_DRAFT_POSITION: 0.09,
        K_PERSONAL: 0.05,
        K_FLEXIBILITY: 0.14,
        K_REDUNDANCY: 0.10,
        K_WEAKNESS: 0.20,
        K_UNCERTAINTY: 0.10,
    },
    PHASE_EARLY: {
        K_MAP_MODE: 0.28,
        K_META: 0.17,
        K_COUNTER: 0.12,
        K_SYNERGY: 0.10,
        K_TEAM_NEED: 0.15,
        K_DRAFT_POSITION: 0.07,
        K_PERSONAL: 0.05,
        K_FLEXIBILITY: 0.06,
        K_REDUNDANCY: 0.15,
        K_WEAKNESS: 0.22,
        K_UNCERTAINTY: 0.10,
    },
    PHASE_MID: {
        K_MAP_MODE: 0.24,
        K_META: 0.12,
        K_COUNTER: 0.20,
        K_SYNERGY: 0.13,
        K_TEAM_NEED: 0.18,
        K_DRAFT_POSITION: 0.04,
        K_PERSONAL: 0.05,
        K_FLEXIBILITY: 0.04,
        K_REDUNDANCY: 0.20,
        K_WEAKNESS: 0.25,
        K_UNCERTAINTY: 0.10,
    },
    PHASE_LAST: {
        K_MAP_MODE: 0.20,
        K_META: 0.07,
        K_COUNTER: 0.29,
        K_SYNERGY: 0.11,
        K_TEAM_NEED: 0.24,
        K_DRAFT_POSITION: 0.02,
        K_PERSONAL: 0.05,
        K_FLEXIBILITY: 0.02,
        K_REDUNDANCY: 0.22,
        K_WEAKNESS: 0.28,
        K_UNCERTAINTY: 0.10,
    },
}


# =========================================================================
# Ban-Bewertung
# =========================================================================
# Ein Ban bewertet nicht "wie gut ist der Brawler fuer uns", sondern
# "wie teuer wird es, wenn ihn der Gegner bekommt".

BAN_GEWICHTE = {
    "map_strength": 0.30,      # Wie stark ist er auf genau dieser Map
    "meta_strength": 0.18,     # Allgemeine Staerke im aktuellen Patch
    "pick_order_threat": 0.16, # Gefahr aus der Pick-Reihenfolge
    "counter_threat": 0.14,    # Wie hart bestraft er unsere Lieblingspicks
    "flexibility": 0.12,       # Passt er in jede Comp, ist er schwerer einzuplanen
    "uncounterability": 0.10,  # Was man nicht kontern kann, muss man bannen
}

# Hat der GEGNER First Pick, sind universelle Selbstlaeufer gefaehrlich:
# er nimmt sie blind, und wir muessen reagieren.
# Hat er LAST Pick, sind spitze Counter gefaehrlicher: er sieht unser
# Team fertig und bestraft gezielt.
BAN_FOKUS_GEGNER_FIRST = {"flexibility": 1.35, "uncounterability": 1.30, "counter_threat": 0.75}
BAN_FOKUS_GEGNER_LAST = {"counter_threat": 1.45, "pick_order_threat": 1.20, "flexibility": 0.85}

# So viele Ban-Vorschlaege liefert die API.
BAN_VORSCHLAEGE = 6


# =========================================================================
# Team Coverage
# =========================================================================

# Ab welchem Deckungsgrad eine Eigenschaft als "erfuellt" gilt.
# Darunter ist es eine Luecke, darueber zaehlt Mehr nicht mehr viel.
COVERAGE_ZIEL = 0.62

# Wie stark ein Team eine Eigenschaft ueberdeckt haben muss, bevor
# weiterer Zuwachs als Redundanz gilt.
REDUNDANZ_SCHWELLE = 0.80

# Das Teamprofil ist nicht die Summe, sondern eine weiche Obergrenze:
# zwei halbe Anti-Tanks sind kein ganzer. Der beste Wert im Team zaehlt
# voll, jeder weitere nur noch anteilig.
ZWEITBESTER_ANTEIL = 0.45
DRITTBESTER_ANTEIL = 0.20

# Wie viele Rollen derselben Art erlaubt sind, bevor es Abzug gibt.
ROLLEN_OBERGRENZE = {
    "tank": 1,
    "assassin": 1,
    "thrower": 1,
    "sniper": 1,
    "support": 1,
    "controller": 2,
    "marksman": 2,
    "damage": 2,
    "aggro": 2,
}


# =========================================================================
# Persoenliche Sicherheit
# =========================================================================
# Wichtigste Leitplanke des Systems: die eigene Uebung darf einen
# objektiv schlechten Pick nicht gut machen. Der Modifikator ist
# deshalb hart gedeckelt.
#
# +-0.08 im Score-Raum [-1, +1] entspricht rund +-4 Punkten auf der
# 0-100-Anzeige. Genug, um bei zwei gleichwertigen Picks den zu
# waehlen, den man beherrscht - zu wenig, um Platz 12 auf Platz 1 zu
# heben.
PERSOENLICH_MAX_AUSSCHLAG = 0.08
PERSOENLICH_NEUTRAL = 50        # Confidence-Wert ohne Angabe
PERSOENLICH_VERMEIDEN_ABZUG = 0.06   # zusaetzlich bei "spiele ich nicht"
PERSOENLICH_FAVORIT_BONUS = 0.02


# =========================================================================
# Statistik: Alter, Patch, Stichprobe
# =========================================================================

# Halbwertszeit der Aktualitaet in Tagen. Ein 14 Tage altes Match zaehlt
# halb so viel wie ein heutiges.
ZEIT_HALBWERTSZEIT_TAGE = 14.0

# Wie stark eine Balanceaenderung alte Daten entwertet.
# 1.0 = alte Daten bleiben voll gueltig, 0.0 = wertlos.
PATCH_GEWICHT = {
    "none": 1.00,
    "small": 0.75,
    "medium": 0.50,
    "large": 0.20,
    "rework": 0.05,
}

# Bayes-Prior: wie viele Spiele die Vorannahme "50 %" wert ist.
# Eine 62-%-Quote aus 20 Spielen wird damit auf rund 55 % gezogen,
# dieselbe Quote aus 5000 Spielen bleibt praktisch stehen.
PRIOR_STAERKE = 120
PRIOR_RATE = 0.50

# Ab wie vielen Spielen eine Statistik als belastbar gilt (Confidence 1.0).
CONFIDENCE_VOLL_AB = 1500
CONFIDENCE_STUFEN = (
    (0.75, "Hoch"),
    (0.45, "Mittel"),
    (0.20, "Niedrig"),
    (0.00, "Sehr niedrig"),
)

# Rang-Pools. Bronze bis Gold interessiert nicht - die Meta dort hat mit
# kompetitivem Draften wenig zu tun.
RANG_POOLS = [
    ("legendary", "Legendary+"),
    ("masters", "Masters"),
    ("pro", "Pro / Competitive"),
    ("alle", "Alle Ränge"),
]
RANG_POOL_GEWICHT = {
    "legendary": 0.85,   # breite Basis, ordentliches Niveau
    "masters": 1.00,     # Referenzpool
    "pro": 0.90,         # beste Qualitaet, wenigste Daten
    "alle": 0.40,
}
RANG_POOL_STANDARD = "masters"

# Zeitfenster fuer spaetere Aggregationen (Tage). "seit Patch" wird
# dynamisch aus dem Patchdatum berechnet.
ZEITFENSTER = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
}


# =========================================================================
# Datenquellen, Import und Aggregation
# =========================================================================
# Keine dieser Zahlen ist ein Scoring-Gewicht. Sie bestimmen, wie aus
# Rohmatches Statistiken werden - nicht, wie die Engine sie gewichtet.

# Welcher StatProvider die Engine versorgt (services/providers/registry.py).
#   "auto"        - gemessene Statistiken, wenn vorhanden, sonst Demo
#   "demo"        - immer die gepflegten Demo-Daten
#   "gemessen"    - nur aus echten Matches aggregierte Statistiken
#   "synthetisch" - nur aus synthetischen Fixtures (Pipeline-Tests)
STAT_PROVIDER = getattr(settings, "DRAFTER_STAT_PROVIDER", "auto")

# Wo mitgeschnittene Rohantworten und Fixture-Dateien liegen. Das
# Verzeichnis ist gitignored: echte Antworten enthalten Spieler-Tags.
FIXTURE_VERZEICHNIS = getattr(
    settings, "DRAFTER_FIXTURE_VERZEICHNIS", settings.BASE_DIR / "data" / "brawl_fixtures"
)

# Aggregationsfenster in Tagen. None = seit dem aktuellen Patch.
AGGREGATIONS_FENSTER = {**ZEITFENSTER, "seit_patch": None}

# Aus welchem Fenster der Prior fuer die kuerzeren Fenster stammt.
#
# Das ist die Umsetzung von "nach einem Patch alte Daten als Prior
# nutzen": eine 7-Tage-Statistik mit 80 Spielen wird nicht zu 50 %
# gezogen, sondern zur langfristigen Rate desselben Brawlers. Je mehr
# neue Spiele vorliegen, desto weniger zaehlt der Prior.
PRIOR_FENSTER = "90d"

# Welches Fenster der Datenraum nimmt, wenn fuer denselben Kontext
# mehrere vorliegen: aktuelle Meta vor langer Historie, gepflegte Werte
# ohne Fenster ("") zuletzt.
STAT_FENSTER_VORRANG = ("seit_patch", "7d", "30d", "90d", "")

# Bayes-Prior fuer Paare (Counter, Synergie). Paare haben um
# Groessenordnungen weniger Spiele als Einzelbrawler. Der Prior ist hier
# nicht 50 %, sondern die ERWARTETE Rate aus den Einzelstaerken - kleine
# Paar-Stichproben landen dadurch bei "kein besonderer Vorteil" statt bei
# einem Zufallswert.
PAAR_PRIOR_STAERKE = 60

# Auf welchen Kontexten gezaehlt wird. Counter und Synergien je Map waeren
# auf absehbare Zeit zu duenn besetzt, um mehr als Rauschen zu liefern.
AGGREGATIONS_EBENEN = {
    "brawler": ("global", "modus", "map"),
    "counter": ("global", "modus"),
    "synergy": ("global", "modus"),
    "build": ("global", "modus"),
}

# Deduplizierung: dieselbe Partie aus zwei Battlelogs kann mit leicht
# abweichendem Zeitstempel ankommen. Innerhalb dieser Toleranz gelten
# gleiche Teams auf gleicher Map als dasselbe Match. Ungeprueft, wie
# genau echte Zeitstempel uebereinstimmen - offene Datenfrage.
MATCH_ZEITTOLERANZ_SEKUNDEN = 60

# Wie stark eine gemessene Build-Statistik die regelbasierte Build-Wahl
# verschiebt, je Punkt Vorteil und gewichtet mit ihrer Confidence. Wirkt
# nur, wenn Build-Statistiken existieren - mit Demo-Daten nie.
BUILD_STAT_EINFLUSS = 0.35


# =========================================================================
# Win-Wahrscheinlichkeit (Heuristik)
# =========================================================================
# Die MVP-Schaetzung ist eine Heuristik, keine kalibrierte
# Wahrscheinlichkeit. Sie wird deshalb bewusst eng um 50 % gehalten:
# ein Draft-Vorteil verschiebt die Siegchance real selten ueber 65 %.
WIN_BASIS = 0.50
WIN_SPANNE = 0.18          # maximaler Ausschlag nach oben/unten
WIN_UNTERGRENZE = 0.20
WIN_OBERGRENZE = 0.80


# =========================================================================
# Anzeige
# =========================================================================
EMPFEHLUNGEN_ANZAHL = 8          # wie viele Vorschlaege das Panel zeigt
GRUENDE_MAX = 5                  # Stichpunkte je Empfehlung


def gewichte_fuer(phase):
    """Gewichtsprofil einer Phase - mit MID als Rueckfallebene.

    Spaeter kann hier eine Datenbank- oder ML-Quelle vorgeschaltet
    werden, ohne dass ein einziger Aufrufer sich aendert.
    """
    return dict(PHASEN_GEWICHTE.get(phase, PHASEN_GEWICHTE[PHASE_MID]))


def api_key():
    """Brawl-Stars-API-Key aus der Umgebung.

    Steht bewusst hier und nicht im Client: so gibt es genau eine
    Stelle, an der ein Key gelesen wird, und sie liest ihn aus der
    Umgebung - nie aus dem Repository.
    """
    return getattr(settings, "BRAWL_STARS_API_KEY", "") or ""
