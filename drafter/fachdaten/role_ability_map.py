# -*- coding: utf-8 -*-
"""Role & Ability Map - gepflegte Fachquelle, uebernommen am 2026-09-18.

Woher: eine von Hand gepflegte Uebersicht, die Brawler nach ihrer AUFGABE
im Draft einteilt und fuenf Zusatzfaehigkeiten farbig markiert. Die Quelle
nennt 101 Brawler.

**Was hier NICHT drinsteht:** wie stark ein Brawler gerade ist. Die Map
beschreibt stabile Eigenschaften ("Gale hat Rueckstoss"), keine Meta.
Winrates und Counter kommen ausschliesslich aus gemessenen Partien.

Farb-Legende der Quelle:
    Gelb  -> good_hyper       (gute Hypercharge)
    Rot   -> knockback_stun   (Rueckstoss / Betaeubung)
    Gruen -> wallbreak        (Waende brechen)
    Blau  -> pierce           (durchdringender Schaden)
    Cyan  -> special          (besondere Faehigkeit)
    Weiss -> keine der hervorgehobenen Faehigkeiten (leere Liste)

Die Namen stehen hier GENAU so wie in der Quelle. Kurzformen werden
ueber ALIASE auf den Katalog abgebildet - jede einzelne ist unten
aufgefuehrt und wird beim Import mitgemeldet, damit sie pruefbar bleibt.
Was sich nicht eindeutig zuordnen laesst, wird gemeldet und NICHT geraten.
"""

ROLLEN = {
    "thrower": [
        "Barley", "Dyna", "Larry", "Tick", "Sprout", "Grom", "Ziggy", "Sirius",
        "Juju", "Willow", "Berry",
    ],
    "tank": [
        "Trunk", "Draco", "Frank", "Fang", "Buster", "Primo", "Hank", "Jacky",
        "Rosa", "Ash",
    ],
    "space_maker": [
        "Bull", "Bibi", "Ollie", "Kenji", "Mortis", "Shade", "Mina", "Buzz",
        "Allie", "Carl", "Edgar", "Kaze", "Lily", "Mico", "Sam", "Chuck",
        "Gigi", "Melodie", "Darryl",
    ],
    "anti_tank": [
        "Chester", "Nita", "Moe", "Rico", "Tara", "Emz", "Lou", "Finx", "Ruffs",
        "Sandy", "Otis", "Lumi", "Shelly", "Surge", "Charlie", "Gale", "Spike",
        "Cord", "Maisie", "Colt", "Griff", "Crow", "8-Bit", "Clancy", "Colette",
        "Meg",
    ],
    "support": ["Kit", "Max", "Gray", "Poco", "Jae-Yong", "Doug", "Glowy"],
    "sniper": [
        "Mandy", "RT", "Gus", "Piper", "Brock", "Byron", "Angelo", "Pierce",
        "Nani", "Belle", "Bea",
    ],
    "control": [
        "Amber", "Meeple", "Leon", "Pam", "Bo", "Pearl", "Gene", "Stu", "Janet",
        "Penny", "Jessie", "Squeak", "Eve", "Lola", "Naija", "Bonnie", "Mr. P",
    ],
}

FAEHIGKEITEN = {
    "good_hyper": [
        "Barley", "Trunk", "Draco", "Bull", "Bibi", "Ollie", "Kenji", "Mortis",
        "Shade", "Chester", "Nita", "Moe", "Rico", "Tara", "Emz", "Lou", "Finx",
        "Ruffs", "Sandy", "Kit", "Max", "Mandy", "RT", "Amber", "Meeple", "Leon",
        "Pam", "Bo",
    ],
    "knockback_stun": [
        "Dyna", "Mina", "Buzz", "Otis", "Lumi", "Shelly", "Surge", "Charlie",
        "Gale", "Spike", "Cord", "Maisie", "Gus", "Piper", "Pearl", "Gene",
    ],
    "wallbreak": ["Frank", "Colt", "Griff", "Gray", "Brock", "Stu"],
    "pierce": [
        "Larry", "Tick", "Sprout", "Grom", "Ziggy", "Sirius", "Juju", "Fang",
        "Allie", "Carl", "Edgar", "Kaze", "Lily", "Mico", "Sam", "Poco",
        "Jae-Yong", "Doug", "Byron", "Janet", "Penny", "Jessie", "Squeak",
    ],
    "special": [
        "Willow", "Berry", "Chuck", "Gigi", "Melodie", "Crow", "Glowy",
        "Angelo", "Pierce",
    ],
}

# Kurzformen und Schreibweisen der Quelle -> Katalogname. Jede Zeile ist
# eine Entscheidung, die der Import ausweist; keine Heuristik.
ALIASE = {
    "dyna": "DYNAMIKE",
    "larry": "LARRY & LAWRIE",
    "primo": "EL PRIMO",
    "allie": "ALLI",
    "cord": "CORDELIUS",
    "rt": "R-T",
    # Die Quelle schreibt "Naija", der Katalog (und die offizielle API)
    # "NAJIA". Buchstabendreher - hier ausdruecklich festgehalten.
    "naija": "NAJIA",
}

# Brawler, die im Ranked-Modus derzeit nicht waehlbar sind. Steht hier und
# nicht im Code, weil Supercell das aendert. Quelle: Angabe des Betreibers
# vom 2026-09-18.
NICHT_RANKED = ["COSMO", "VINCE"]


def alle_namen():
    return [name for namen in ROLLEN.values() for name in namen]
