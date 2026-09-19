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

# =========================================================================
# Drei Arten von Aussage - streng getrennt
# =========================================================================
# CURRENT STRENGTH  Wie gut laeuft er gerade? Kommt NUR aus gemessenen
#                   (ersatzweise gepflegten) Siegquoten.
# DRAFT FIT         Passt er in DIESEN Draft? Map, Gegner, Team, Position.
#                   Speist sich aus gepflegtem WISSEN (Attribute, Rollen,
#                   Faehigkeiten) und aus gemessenen Paarwerten.
# PERSOENLICH       Wie sicher beherrscht der Spieler ihn? Freiwillig.
#
# Wissen ist keine Staerke: dass ein Brawler Waende bricht, sagt nichts
# darueber, ob er im aktuellen Patch gewinnt. Frueher liefen beide in
# eine Zahl und Profilwissen konnte eine fehlende Messung ersetzen - bei
# GALE standen +0,594 aus Wissen gegen +0,014 aus Messung, ohne dass man
# das der Zahl ansah. Die Gruppen stehen deshalb einzeln in der Ausgabe.
G_CURRENT_STRENGTH = "current_strength"
G_DRAFT_FIT = "draft_fit"
G_PERSOENLICH = "persoenlich"

KOMPONENTEN_GRUPPE = {
    K_META: G_CURRENT_STRENGTH,
    K_PERSONAL: G_PERSOENLICH,
    K_MAP_MODE: G_DRAFT_FIT,
    K_COUNTER: G_DRAFT_FIT,
    K_SYNERGY: G_DRAFT_FIT,
    K_TEAM_NEED: G_DRAFT_FIT,
    K_DRAFT_POSITION: G_DRAFT_FIT,
    K_FLEXIBILITY: G_DRAFT_FIT,
    K_REDUNDANCY: G_DRAFT_FIT,
    K_WEAKNESS: G_DRAFT_FIT,
    K_UNCERTAINTY: G_DRAFT_FIT,
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
# Datenstufen: was ueber einen Brawler bekannt ist
# =========================================================================
# Vier Stufen, von der Engine je Anfrage bestimmt (Datenraum.stufe):
#
#   profil     - gepflegtes Eigenschaftsprofil (32 Attribute, Rolle,
#                Draft-Werte). Alle Komponenten berechenbar.
#   gemessen   - kein Profil, aber mindestens EINE gemessene soloRanked-
#                Partie in einem anwendbaren Kontext. Bewertet wird, was
#                die Messung hergibt, plus was die Rolle qualitativ sagt.
#   fachwissen - weder Profil noch Messung, aber eine gepflegte
#                Draft-Rolle. Kein CURRENT STRENGTH (dafuer braucht es
#                Beobachtung), aber ein Draft-Fit aus der Fachquelle.
#   katalog    - nichts davon. Waehl- und bannbar, bekommt KEINEN Score.
#
# **Es gibt keine Mindestzahl von Partien mehr.** Bis zum 2026-09-18 stand
# hier PROFIL_MESS_MINDESTSPIELE = 20, und acht Ranked-Brawler (HANK,
# SAM, BONNIE, MR. P, DRACO, ZIGGY, CLANCY, JACKY) bekamen deshalb gar
# keinen Score - obwohl Messwerte vorlagen. Die Grenze stammte aus einer
# Zeit ohne Shrinkage: damals konnte eine Zahl aus 6 Partien ungebremst
# in den Score laufen, und der Ausschluss war die einzige Bremse.
#
# Inzwischen bremst das Modell selbst, an drei Stellen gleichzeitig:
# der Beta-Binomial-Posterior zieht 6 Partien praktisch vollstaendig zum
# Prior, die eigene Streuung steht im Nenner der Feldskalierung, und die
# Statistical Confidence weist die Unsicherheit getrennt aus. Eine feste
# Schwelle obendrauf waere eine zweite Antwort auf dieselbe Frage - und
# eine schlechtere, weil sie am Stichtag springt statt zu verlaufen.
#
# Was bleibt, ist die Grenze zwischen "beobachtet" und "nicht beobachtet":
# n = 0 heisst Unknown, nicht 50 %. Ein Prior ist eine Annahme, keine
# Messung.

# Datenabdeckung = Anteil der Bewertungsgewichte (ohne persoenliche
# Sicherheit), dessen Komponenten fuer diesen Brawler berechenbar sind.
# Fehlende Komponenten zaehlen nicht als 0 - sie fallen heraus, und die
# vorhandenen werden auf die volle Gewichtssumme hochgerechnet. Die
# Abdeckung sagt, auf wie viel davon der Score tatsaechlich beruht.
DATENABDECKUNG_STUFEN = (
    (0.80, "Hoch"),
    (0.50, "Mittel"),
    (0.00, "Niedrig"),
)


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
#   "auto"        - gemessene Statistiken, wenn vorhanden UND freigegeben,
#                   sonst Demo (siehe GEMESSENE_STATS_FREIGEGEBEN)
#   "demo"        - immer die gepflegten Demo-Daten
#   "gemessen"    - nur aus echten Matches aggregierte Statistiken
#   "synthetisch" - nur aus synthetischen Fixtures (Pipeline-Tests)
STAT_PROVIDER = getattr(settings, "DRAFTER_STAT_PROVIDER", "auto")

# Wo mitgeschnittene Rohantworten und Fixture-Dateien liegen. Das
# Verzeichnis ist gitignored: echte Antworten enthalten Spieler-Tags.
FIXTURE_VERZEICHNIS = getattr(
    settings, "DRAFTER_FIXTURE_VERZEICHNIS", settings.BASE_DIR / "data" / "brawl_api_raw"
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

# Deduplizierung - NUR der Fallback.
#
# Vorrang hat die Partie-ID der Quelle. Liefert eine Quelle keine ID, wird
# die Partie aus Zeit, Map und Teams rekonstruiert.
#
# 0 = sekundengenau, keine Toleranz. GEMESSEN am 2026-09-16: steht dieselbe
# Partie in den Battlelogs zweier Spieler, ist `battleTime` exakt gleich -
# es gibt kein Zittern, fuer das man eine Toleranz braeuchte.
#
# Die frueheren 60 Sekunden waren eine Schaetzung und haben aktiv geschadet:
# dieselben sechs Spieler spielen mit denselben Brawlern Serien auf
# derselben Map, oft nur 100-160 s auseinander. Von 298 echten Partien
# wurden dadurch 8 zusammengefasst (also verloren) und 2 als
# "widerspruechliches Ergebnis" markiert, obwohl beide Ergebnisse stimmten.
# Wer den Wert wieder anhebt, muss zuerst zeigen, dass Zeitstempel
# tatsaechlich auseinanderlaufen.
MATCH_ZEITTOLERANZ_SEKUNDEN = 0

# Wie stark eine gemessene Build-Statistik die regelbasierte Build-Wahl
# verschiebt, je Punkt Vorteil und gewichtet mit ihrer Confidence. Wirkt
# nur, wenn Build-Statistiken existieren - mit Demo-Daten nie.
BUILD_STAT_EINFLUSS = 0.35

# Gemessene Statistiken produktiv nutzen? Solange False, nimmt "auto" die
# Demo-Daten, auch wenn aggregierte Messwerte vorliegen. Erste echte
# Aggregationen beruhen auf kleinen Stichproben; sie gehoeren zuerst in
# einen Vergleichsbericht (python manage.py vergleiche_brawl_stats) und
# erst dann - bewusst - auf die Seite.
GEMESSENE_STATS_FREIGEGEBEN = getattr(settings, "DRAFTER_GEMESSENE_STATS_FREIGEGEBEN", False)

# Welche Partietypen (battle.type der offiziellen API) in Draft-Statistiken
# eingehen. Beobachtet am 2026-09-15: "soloRanked" ist der Ranked-Modus mit
# Draft, "ranked" die Trophaeen-Rangliste ohne Draft. Trophaeen-Partien
# werden gespeichert, aber nie mitgezaehlt.
DRAFT_STATISTIK_BATTLE_TYPEN = ("soloRanked",)

# Wo Vergleichsberichte landen (gitignored).
BERICHT_VERZEICHNIS = getattr(
    settings, "DRAFTER_BERICHT_VERZEICHNIS", settings.BASE_DIR / "data" / "brawl_reports"
)


# =========================================================================
# Aktuelle Staerke (services/staerke.py)
# =========================================================================
# CURRENT STRENGTH ist die einzige empirische Groesse der Engine: wie gut
# laeuft ein Brawler MESSBAR gerade. Sie kommt nie aus Profilwissen.
#
# Geschaetzt wird als Beta-Binomial-Posterior. Kleine Stichproben ziehen
# stark zum Prior, grosse ueberstimmen ihn - ohne harte Schwelle:
#
#     mittel = (siege + a) / (spiele + a + b)
#
# Die Hierarchie global -> Modus -> Map laeuft als Kette: die groebere
# Ebene ist der Prior der feineren. Gerechnet wird auf ROHZAEHLUNGEN
# (games/wins), nicht auf `adjusted_rate` - die Aggregation hat dort
# bereits einmal geschrumpft (aggregator._brawler_prior), ein zweites Mal
# waere doppelt.

# Sicherheit einer Paaraussage, die nur auf Eigenschaften beruht
# (Counter/Synergie ohne jede Zeile). Bewusst niedrig: sie ist eine
# Herleitung, keine Beobachtung.
HEURISTIK_PAAR_CONFIDENCE = 0.25

# Prior-Staerke der obersten Ebene, in "gedachten Spielen" zu 50 %.
STAERKE_PRIOR_GLOBAL = 120
# Wie viel eine Partie einer GROEBEREN Ebene zaehlt, je Stufe Abstand
# zur feinsten vorhandenen. Eine Map-Partie zaehlt voll, eine Partie, die
# nur fuer den Modus vorliegt, halb, eine nur globale ein Viertel.
#
# Warum nicht die Ketten-Form (jede Ebene als Prior der naechsten): dort
# konnte eine duenne Map-Zeile die Schaetzung VERSCHLECHTERN - 4 Partien
# auf der Map zogen den Wert um 3 Punkte und senkten die effektive
# Stichprobe von 164 auf 64, weil die feinere Ebene die Praezision der
# groeberen wegwarf. Mehr Daten duerfen nie weniger Gewissheit ergeben.
STAERKE_EBENEN_ABSCHLAG = 0.5

# Feldrelative Skalierung
# -----------------------
# Der Score-Vertrag verlangt [-1, +1], aber echte Siegquoten leben
# zwischen 45 und 58 %. `(rate - 0.5) * 2` liefert damit nur -0.10 bis
# +0.16: 22 % nominelles Gewicht wurden real zu etwa 1 %. Gemessen an
# 106 Ranked-Brawlern (2026-09-18) hatte die Komponente eine Streuung von
# 0.042 - der ganze Unterschied zwischen dem besten und dem schlechtesten
# Brawler des Feldes war ein einziger Scorepunkt.
#
# Also wird am FELD gemessen, nicht an einer festen 50-%-Marke:
#
#     wert = (rate - Median des Feldes) / (K * sqrt(Feldstreuung^2 + sd^2))
#
# Drei Gruende fuer genau diese Form:
#
# * **Median und MAD statt Mittelwert und sd** - ein einzelner extremer
#   Brawler verschiebt den Bezugspunkt sonst fuer alle anderen mit.
# * **Der Bezugspunkt ist nicht 50 %.** Ist das ganze beobachtete Feld
#   verschoben (Sampling, Banphase, Patch), waere eine feste Marke eine
#   Behauptung ueber Daten, die wir nicht haben.
# * **Die eigene Unsicherheit steht im Nenner.** Die Feldstreuung der
#   Posterior-Raten (robust 0.012) ist KLEINER als die typische
#   Einzelunsicherheit (0.041). Wer nur durch die Feldstreuung teilt,
#   macht aus Rauschen Signal: z-Score, MAD und Perzentil gaben GALE mit
#   44 Partien +1.00, +1.00 und +0.98 - Vollausschlag aus einer
#   Stichprobe, die 14 Prozentpunkte Spielraum hat. Mit der eigenen
#   Streuung im Nenner bekommt GUS (1131 Partien) +0.54 und GALE +0.33.
#
# K = 2 heisst "zwei kombinierte Streuungen sind Vollausschlag" - dieselbe
# Konvention wie in scoring.z_werte.
STAERKE_FELD_K = 2.0
# Untergrenze der Feldstreuung. Ohne sie teilte ein sehr einheitliches
# Feld (oder eines aus zwei Brawlern) durch fast null.
STAERKE_FELD_MIN_STREUUNG = 0.01

# Selection Bias: wer selten gespielt wird, wird von Spezialisten
# gespielt. Das macht die Rate nicht falsch, aber weniger uebertragbar -
# es senkt die SICHERHEIT, nie den Schaetzwert.
STAERKE_PICKRATE_REFERENZ = 0.05     # ab hier gilt ein Brawler als normal verbreitet
STAERKE_BIAS_MAX_ABZUG = 0.40        # hoechstens so viel Sicherheit kostet das


# =========================================================================
# Was eine Draft-Rolle qualitativ adressiert (services/rollenwissen.py)
# =========================================================================
# Die sieben Rollen der Fachquelle, uebersetzt in die Eigenschaften, die
# ihrer DEFINITION nach zu ihnen gehoeren. Das ist eine Zuordnung, keine
# Bewertung: hier steht, WOVON ein Thrower handelt, nicht wie gut er
# darin ist. Die Betraege kommen immer von der anderen Seite - Map-
# Anforderung oder Team-Luecke. Siehe den Kopf von services/rollenwissen.py.
#
# **Audit vom 2026-09-18.** Die erste Fassung enthielt Zuordnungen, die
# nur plausibel klangen. Auf Safe Zone (Heist) hatte das eine sichtbare
# Folge: `objective_damage` haengte allein an `thrower`, und weil
# objective_damage dort 20 % des gesamten Anforderungsgewichts traegt,
# liefen ALLE Thrower in den Deckel - WILLOW und SPROUT standen auf den
# Plaetzen 4 und 5, ohne eine einzige gemessene Heist-Partie.
#
# Geprueft wurde jede Zeile nach einer Frage: folgt das aus der
# Rollendefinition, oder ist es eine Beobachtung ueber einzelne Brawler?
#
#   behalten (logisch inhaerent)
#     thrower     -> area_control, zone_control, safe_poke
#                    (er wirft ueber Deckung in Flaechen - das IST die Rolle)
#     tank        -> frontline, tankiness, engage
#     space_maker -> engage, mobility, backline_pressure
#     anti_tank   -> anti_tank            (definitorisch)
#     support     -> support, peel
#     sniper      -> long_range, poke, lane_control
#     control     -> area_control, zone_control, mid_control
#
#   ENTFERNT (nur Heuristik oder fragwuerdig)
#     thrower     -> objective_damage   Wurfschaden am Safe ist eine
#                                       Eigenschaft einzelner Brawler,
#                                       nicht der Rolle. Ursache des
#                                       Safe-Zone-Fehlers.
#     tank        -> peel               manche Tanks tauchen, statt zu schuetzen
#     space_maker -> anti_assassin      beschreibt eine Antwort, keine Aufgabe
#     anti_tank   -> burst_damage, poke COLETTE macht prozentualen
#                                       Dauerschaden, COLT Dauerschaden -
#                                       die Rolle sagt nichts ueber die Art
#     support     -> healing            nicht jeder Support heilt
#     support     -> survivability      Beobachtung, keine Aufgabe
#     sniper      -> backline_pressure  Reichweite ist nicht Druck
#
# Was dadurch wegfaellt, ist nicht verloren: es kommt jetzt aus der
# gemessenen Modus-Eignung (services/objective.py) oder aus gepflegten
# Faehigkeiten - beides Belege statt Vermutungen.
ROLLE_DECKT = {
    "thrower":     ("area_control", "zone_control", "safe_poke"),
    "tank":        ("frontline", "tankiness", "engage"),
    "space_maker": ("engage", "mobility", "backline_pressure"),
    "anti_tank":   ("anti_tank",),
    "support":     ("support", "peel"),
    "sniper":      ("long_range", "poke", "lane_control"),
    # `mid_control` ist am 2026-09-19 gestrichen worden: "Control" ist ein
    # Spielstil, "Mid" eine Position auf der Map. Die Zuordnung trug in
    # Gem Grab allein 37,9 % des Anforderungsgewichts - derselbe Fehler
    # wie `thrower -> objective_damage` bei Heist, nur groesser.
    # Ableiten laesst sie sich nicht: wer Mid haelt, braucht Eigenschaften,
    # und die haben Brawler ohne Profil nicht. Also lieber unbekannt.
    "control":     ("area_control", "zone_control"),
}

# Die zwei Haelften der Komponente "Map & Modus" (services/map_fit.py):
#
#   allgemein  - passt sein Koennen zu dem, was hier gefordert ist
#   objective  - ist er im ZIEL dieses Modus messbar besser als sonst
#
# Bewusst gleich stark. Die erste Haelfte ist gepflegtes Wissen, die
# zweite Beleg; ein Profil soll einen Modus-Fit nicht mehr allein
# behaupten koennen (BROCK: Profil sagte perfekt, 221 Partien auf der
# Map sagten 40,7 %). Fehlt eine Haelfte, zaehlt sie 0 - nicht
# hochgerechnet, dieselbe Regel wie im Gesamtscore.
MAP_FIT_ANTEIL_ALLGEMEIN = 0.5
MAP_FIT_ANTEIL_OBJECTIVE = 0.5

# Wie weit eine rein qualitative Auskunft ausschlagen darf. Eine Rolle ist
# eine Schublade, ein Profil eine Beschreibung - wer nur eingeordnet ist,
# bekommt hoechstens die Haelfte des Ausschlags, den ein gepflegtes Profil
# erreichen kann.
FACHWISSEN_MAX_AUSSCHLAG = 0.5

# Wie stark ein zweiter Brawler derselben Rolle im eigenen Team zaehlt.
# Der Betrag kommt aus der Zahl der Picks, nicht aus einer Einschaetzung.
ROLLEN_REDUNDANZ_JE_PICK = 0.3


# =========================================================================
# Abgeleitete Signale (services/faehigkeiten.py)
# =========================================================================
# KEINE Scoring-Gewichte. Diese Zahlen uebersetzen gepflegtes Wissen in
# abgeleitete Groessen, die der Coach lesen kann - sie gehen (noch) in
# keinen Score ein.

# Welche Zusatzfaehigkeit der Role-&-Ability-Map welchen Attributen
# entspricht. Liegt ein Profil vor, gilt der gemessene/gepflegte
# Attributwert; sonst sagt die Map nur "kann das" - ohne Staerke.
FAEHIGKEIT_ATTRIBUTE = {
    "wallbreak": ("wallbreak",),
    "knockback_stun": ("knockback", "stun"),
    # Fuer diese drei gibt es im 32er-Vokabular keine Entsprechung. Sie
    # bleiben qualitativ: "hat es" oder "hat es nicht".
    "pierce": (),
    "good_hyper": (),
    "special": (),
}

# Wie sehr eine Draft-Rolle typischerweise von Waenden lebt, 0-1.
# ANNAHMEN, keine Messung - sie stehen hier, damit sie an einer Stelle
# korrigierbar sind. Thrower brauchen Waende (sie werfen darueber),
# Sniper und Anti-Tank brauchen Sichtlinien.
WANDABHAENGIGKEIT_ROLLE = {
    "thrower": 0.85,
    "space_maker": 0.60,
    "tank": 0.50,
    "support": 0.50,
    "control": 0.45,
    "anti_tank": 0.30,
    "sniper": 0.15,
}

# Welche Attribute dieselbe Frage aus dem Profil beantworten, mit
# Vorzeichen: Nahkampf und Flaechenkontrolle sprechen fuer Waende,
# Reichweite dagegen.
WANDABHAENGIGKEIT_ATTRIBUTE = {
    "close_range": 0.5,
    "area_control": 0.5,
    "long_range": -0.5,
}


# =========================================================================
# Priorisierung der Spielerauswahl (services/prioritaet.py)
# =========================================================================
# Welchen Spieler als naechsten abrufen? Nicht "irgendeinen", sondern den,
# dessen bekannte Historie die groessten Luecken beruehrt. Keine dieser
# Zahlen steht im Code - wer die Strategie aendern will, aendert sie hier.
#
# WICHTIG: Ein Defizit > 0 heisst nur "hier fehlen Daten", nicht "diese
# Daten gelten jetzt als belastbar". Die Confidence-Stufen
# (CONFIDENCE_VOLL_AB, CONFIDENCE_STUFEN) bleiben davon unberuehrt.

# Zielstichprobe je Einheit - vorlaeufig, nur fuer die Priorisierung.
# =========================================================================
# Was ein Modus von einem Brawler WILL - in Aspekten statt in einer Summe
# =========================================================================
# Der flache Anforderungsvektor beantwortet nur eine Frage: "wie viel von
# allem bringt er mit". Ein Modus verlangt aber verschiedene Dinge, und
# **kein Brawler muss alle koennen** - ein starker Gem-Traeger, der keinen
# Druck macht, ist trotzdem ein guter Pick.
#
# Deshalb hat ein Modus benannte Aspekte, jeder ein Buendel vorhandener
# Eigenschaften mit Gewichten. Bewertet wird der BESTE erfuellte Aspekt,
# nicht der Durchschnitt: Spezialisierung zaehlt, Mittelmass in allem
# nicht. Keine Mindestanforderung, keine neuen Felder.
#
# Die Tabelle ist Daten, kein Code - services/objective.py liest sie und
# kennt keinen einzigen Modusnamen.
MODUS_ZIELASPEKTE = {
    # Gem Grab: Gems tragen, Mid halten, den gegnerischen Traeger jagen.
    # Bis 2026-09-19 kannte das Profil nur Kontrolle - "wer traegt" und
    # "wer holt sie zurueck" kamen darin gar nicht vor.
    "gem-grab": {
        "carrier": {"survivability": 1.0, "disengage": 0.9, "safe_poke": 0.6},
        "mid_lane": {"mid_control": 1.0, "lane_control": 0.8, "area_control": 0.7,
                     "zone_control": 0.7, "peel": 0.6},
        "druck_auf_traeger": {"engage": 0.9, "backline_pressure": 0.9,
                              "burst_damage": 0.7, "mobility": 0.7},
    },
    # Brawl Ball: das Tor ist das Ziel. `objective_damage` fehlte im
    # Modusprofil vollstaendig - nur eine einzelne Map nannte es.
    "brawl-ball": {
        "abschluss": {"objective_damage": 1.0, "mobility": 0.8, "engage": 0.8,
                      "frontline": 0.6, "wallbreak": 0.6},
        "ballzugang": {"mobility": 1.0, "engage": 0.9, "close_range": 0.5},
        "raum": {"frontline": 1.0, "peel": 0.8, "crowd_control": 0.7,
                 "close_range": 0.6},
        "teamwipe": {"burst_damage": 1.0, "crowd_control": 0.8},
    },
}


# Wie sich Messung und Fachwissen im OBJECTIVE FIT mischen
# (services/objective.py).
#
# Bis zum 2026-09-19 galt eine harte Prioritaet: gibt es eine Messung,
# zaehlt nur sie; sonst nur das Fachwissen. Das hatte eine unangenehme
# Folge - die qualitative Obergrenze (+-0.5 -> +-4.25 Punkte) war GROESSER
# als fast jedes gemessene Signal. MR. P stand auf Gem Grab mit null
# Modus-Partien auf Rang 5 (+4.2), waehrend AMBER mit 313 gemessenen
# Partien -1.2 bekam. "Keine Daten" schlug "gemessen".
#
# Jetzt mischt es stetig mit der Stichprobe:
#
#     w    = n / (n + K)
#     wert = w * Messung + (1 - w) * Daempfung * Fachwissen
#
# K = 120 ist dieselbe Groessenordnung wie der Prior der Staerke: bei 20
# Partien traegt die Messung 14 %, bei 200 63 %, bei 1000 89 %. Eine
# harte Mindestzahl braucht es nicht - das Fachwissen zieht sich von
# selbst zurueck. Die Daempfung haelt die rein qualitative Aussage
# bewusst konservativ: ohne jede Partie sind hoechstens +-2.1 Punkte
# erreichbar statt +-4.25.
#
# Die Messung selbst ist zusaetzlich schon in sich geschrumpft (die
# Differenz laeuft bei kleiner Stichprobe gegen null) - beides zusammen
# ergibt genau die gewuenschte Staffelung.
OBJECTIVE_EVIDENZ_K = 120
OBJECTIVE_FACHWISSEN_DAEMPFUNG = 0.5

# Gemessene Ableitung fuer Draft-Position und Flexibilitaet
# (services/draft_position.py). Beides sind Rauschgrenzen, keine
# Qualitaetsaussagen: unterhalb davon gibt es keine Auskunft statt einer
# geratenen. Der Betrag selbst kommt aus der Streuung, nicht aus einer
# Schwelle.
DRAFTLAGE_MIN_PAARE = 8            # gemessene Matchups fuer eine Streuungsaussage
DRAFTLAGE_MIN_MODUS_PARTIEN = 30   # je Modus, damit eine Modus-Rate zaehlt


# =========================================================================
# Welche Maps der Drafter anbietet
# =========================================================================
# Nicht mehr allein die von Hand freigeschalteten: am 2026-09-19 lagen
# 10 188 gezaehlte Ranked-Partien auf 30 Maps, angeboten wurden 8 aus dem
# Demo-Seed - 20 % Deckung, bei Bounty und Hot Zone null. Eine Map, die in
# aktuellen Ranked-Partien vorkommt, ist Teil der Rotation, ob jemand sie
# gepflegt hat oder nicht.
#
# `is_active` bleibt daneben bestehen und wird nie automatisch geloescht:
# gepflegte Maps sollen nicht verschwinden, nur weil die Rotation sie
# gerade aussetzt. Historie bleibt vollstaendig erhalten.
RANKED_MAP_FENSTER_TAGE = 14
# Rauschgrenze, keine Qualitaetsaussage: eine einzelne falsch zugeordnete
# Partie soll keine Map in die Auswahl heben. Alle 30 beobachteten Maps
# liegen deutlich darueber (kleinste: 44 Partien).
RANKED_MAP_MIN_PARTIEN = 10

# Ab wann gilt ein Brawler dem COLLECTOR als datenarm? Das ist eine
# Reihenfolge fuer Abfragen, keine Aussage ueber seine Bewertung - hier
# darf eine runde Zahl stehen, weil sie nur bestimmt, wen wir als
# naechstes fragen. Mit dem Scoring hat sie nichts zu tun.
COLLECTOR_DATENARM_UNTER = 20

PRIORITAET_ZIELE = {
    "brawler_global": 195,   # Wilson ±7 pp
    "brawler_modus": 80,     # Wilson ±11 pp
    "counter": 390,          # Paare messen eine Differenz: rund doppelte Streuung
    "synergie": 390,
}

# Was ein Beitrag wiegt. Die Map-Ebene steht bewusst auf 0: 1474 Zeilen,
# Median 5 Partien - sie wuerde die Auswahl mit Rauschen steuern.
PRIORITAET_GEWICHTE = {
    "brawler_global": 1.00,
    "brawler_modus": 0.50,
    "counter": 0.20,
    "synergie": 0.15,
    "brawler_map": 0.00,
    # Brawler ohne gepflegtes Profil UND ohne belastbare Messung
    # (Stufe "katalog") zaehlen zusaetzlich: dort fehlt nicht eine Zahl,
    # sondern jede.
    #
    # Die Hoehe ist nachgerechnet, nicht geraten: ein Spieler mit lauter
    # mittelhaeufigen Brawlern kommt ueber die Kappung auf hoechstens
    # 3 x ~0,8 = 2,4 Punkte aus `brawler_global`. Ein einzelner
    # Catalog-Only-Brawler bringt ~0,95 x (1,0 + 4,0) = 4,75 - er steht
    # damit sicher vor der Breite, wie gefordert.
    "katalog_bonus": 4.00,
    # Nur Gleichstandsentscheid: hohe Trophaeen deuten auf aktives Spiel.
    # Bewusst winzig - Rang ist kein Ranked-Rang (die API kennt keinen).
    "rang": 0.05,
}

# Wie viele Beitraege je Kategorie hoechstens zaehlen - die groessten
# zuerst. Ohne diese Kappung gewaenne allein, wer viele Partien in der
# Historie hat: breite Vielspieler statt gezielter Luecken.
PRIORITAET_MAX_BEITRAEGE = {
    "brawler_global": 3,
    "brawler_modus": 5,
    "counter": 8,
    "synergie": 8,
}


# =========================================================================
# Offizielle API: Wiederholen, Pausen, Collector
# =========================================================================
# Die Dokumentation nennt kein Ratenlimit, und die Antworten tragen keine
# Rate-Limit-Header (geprueft am 2026-09-15). Diese Werte sind deshalb
# vorsichtige Annahmen - keine bekannten Grenzen der API.

# Abstand zwischen zwei Anfragen desselben Clients.
API_MINDESTABSTAND_SEKUNDEN = 0.25
# Versuche je Anfrage bei 429, 5xx und Zeitueberschreitung (1 = nie wiederholen).
API_VERSUCHE = 4
# Exponentielle Pause: 1 s, 2 s, 4 s ... hoechstens bis zur Obergrenze.
API_BACKOFF_BASIS_SEKUNDEN = 1.0
API_BACKOFF_MAX_SEKUNDEN = 30.0
# Nennt eine 429-Antwort Retry-After, gilt dieser Wert - hoechstens so lange.
API_RETRY_AFTER_MAX_SEKUNDEN = 120.0

# Auswahlstrategie des Collectors:
#   "standard" - Tiefe, dann Ranglistenplatz (die bisherige Reihenfolge)
#   "luecken"  - nach Datenluecken, siehe services/prioritaet.py
#   "broad_high_rank" - breite Stichprobe belegter High-Rank-Spieler,
#                       ohne Auswahl nach Brawler (services/stichprobe.py)
COLLECTOR_STRATEGIEN = ("standard", "luecken", "broad_high_rank")

# Ab welchem belegten Ranked-Rang ein Spieler als "high rank" gilt.
#
# NUMERISCH, nicht benannt: der Wert steht so in `brawler.trophies` von
# soloRanked-Partien (beobachtet 2026-09-17: durchgehend 3 bis 22, Power
# immer 11; zum Vergleich tragen Trophaeen-Partien dort 5 bis 5882).
# Welche Stufe welcher Zahl entspricht, ist NICHT aus der API belegt -
# die Vermutung 16-18 = Legendary, 19+ = Masters steht bewusst nur als
# Kommentar und nirgends als Label in der Oberflaeche.
BROAD_MIN_RANG = 16

# Wie viele Spieler je bereits bekannter Partie hoechstens ausgewaehlt
# werden. 1 heisst: von sechs Mitspielern derselben Partie holt ein Lauf
# hoechstens einen - sonst importiert er dieselbe Partie mehrfach.
# Gemessen: 1434 von 2596 Partien enthalten mehr als einen Kandidaten.
BROAD_MAX_JE_PARTIE = 1
COLLECTOR_STRATEGIE = "standard"

# Battlelogs je Collector-Lauf. Klein halten: ein Lauf soll ueberschaubar
# bleiben und jederzeit abbrechbar sein.
COLLECTOR_MAX_SPIELER = 25
# Wie weit von der Saat (Rangliste/manuell = Tiefe 0) entdeckt wird. 1 heisst:
# deren Mitspieler werden abgerufen, deren Mitspieler nicht einmal gespeichert.
COLLECTOR_MAX_TIEFE = 1
COLLECTOR_TIEFE_OBERGRENZE = 2
# Denselben Spieler fruehestens nach so vielen Stunden erneut abrufen.
COLLECTOR_ABRUF_ABSTAND_STUNDEN = 6
# Aus welchen Partietypen Mitspieler entdeckt werden - nur aus Draft-Partien.
COLLECTOR_ENTDECKEN_AUS_TYPEN = DRAFT_STATISTIK_BATTLE_TYPEN
# 404: den Tag gibt es (nicht mehr) - so lange nicht erneut versuchen.
COLLECTOR_404_PAUSE_TAGE = 7
# 5xx/Netz nach allen Wiederholungen: Pause je Spieler 1 h, 2 h, 4 h ... bis hierhin.
COLLECTOR_FEHLER_PAUSE_STUNDEN_MAX = 48
# So viele solcher Fehler in Folge beenden den Lauf.
COLLECTOR_ABBRUCH_NACH_FEHLERN = 3


# =========================================================================
# Counter: gepflegt, gemessen, geschaetzt
# =========================================================================
# Abzug der Gegenrichtung fuer GEPFLEGTE (Demo, manuell) und HEURISTISCHE
# Counter. Dort sind beide Richtungen eigenstaendige Einschaetzungen -
# "Gale stoesst Bull weg" und "Bull kommt an Gale nicht heran" ergaenzen
# sich, ohne dasselbe zu sagen - und duerfen asymmetrisch sein.
#
# Unveraendert 0,8: beide Werte standen bisher als Zahl im Engine-Code
# (services/counters.py) und sind nur hierher umgezogen. Keine Anpassung.
#
# Fuer GEMESSENE Counter gilt KEIN Faktor. Dort ist die Gegenrichtung
# exakt das Negativ derselben Messung; ein Abzug wuerde dasselbe Matchup
# 1,8-fach zaehlen (a + 0,8 * a).
GEPFLEGTER_COUNTER_GEGENRICHTUNG = 0.8
HEURISTISCHER_COUNTER_GEGENRICHTUNG = 0.8


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
