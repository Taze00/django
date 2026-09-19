# -*- coding: utf-8 -*-
"""Demo-Datensatz des Drafters.

**Alles hier sind gepflegte Einschaetzungen, keine gemessenen Werte.**
Jeder Datensatz traegt `source="demo"`, die Oberflaeche weist darauf hin,
und die Confidence ist entsprechend gedeckelt (siehe
services/confidence.py). Sobald echte Matchdaten vorliegen, treten sie
neben diese Zeilen, nicht an ihre Stelle - die Kontextfelder der
Stat-Tabellen sind genau dafuer da.

Die Einschaetzungen stammen aus dem verbreiteten Spielverstaendnis zu
diesen Brawlern (wer ist Tank, wer hat Reichweite, wer bestraft wen).
Sie sind gut genug, damit die Engine sinnvolle Empfehlungen gibt, und
ausdruecklich nicht gut genug, um als Statistik durchzugehen.

Nicht angegebene Eigenschaften sind 0, nicht angegebene Draftwerte 50.
Das haelt die Tabellen lesbar: eingetragen wird, was den Brawler
ausmacht.
"""

# =========================================================================
# Brawler
# =========================================================================
# Reihenfolge der Felder: name, rolle, tags, farbe, attribute, draftwerte
BRAWLER = [
    {
        "name": "Gale", "slug": "gale", "role": "controller", "tags": ["support"],
        "color": "#4a9eda",
        "attributes": {
            "mid_range": 75, "close_range": 40, "sustained_damage": 45, "poke": 60,
            "area_control": 80, "lane_control": 70, "mid_control": 65, "zone_control": 85,
            "crowd_control": 80, "knockback": 95, "slow": 70,
            "anti_tank": 90, "anti_assassin": 92, "anti_thrower": 30,
            "survivability": 55, "disengage": 75, "peel": 95,
            "mobility": 30, "wallbreak": 20, "support": 80,
        },
        "draft_values": {
            "blind_pick_value": 72, "early_pick_value": 70, "last_pick_value": 80,
            "counter_pick_value": 85, "flexibility_value": 78, "counterability": 40,
        },
        "notes": "Antwort auf alles, was herankommen will.",
    },
    {
        "name": "Belle", "slug": "belle", "role": "marksman", "tags": ["sniper"],
        "color": "#c86fd6",
        "attributes": {
            "long_range": 88, "mid_range": 70, "safe_poke": 80, "poke": 85,
            "sustained_damage": 60, "lane_control": 80, "mid_control": 78,
            "zone_control": 60, "slow": 40, "backline_pressure": 55,
            "anti_tank": 55, "survivability": 40, "mobility": 25, "vision": 40,
        },
        "draft_values": {
            "blind_pick_value": 68, "early_pick_value": 72, "last_pick_value": 65,
            "counter_pick_value": 55, "flexibility_value": 70, "counterability": 60,
        },
    },
    {
        "name": "Max", "slug": "max", "role": "support", "tags": ["aggro"],
        "color": "#e8734a",
        "attributes": {
            "mid_range": 70, "sustained_damage": 65, "poke": 55,
            "mid_control": 60, "lane_control": 55, "backline_pressure": 80,
            "anti_thrower": 75, "anti_assassin": 45,
            "survivability": 60, "disengage": 85, "peel": 55,
            "mobility": 95, "engage": 75, "support": 90,
        },
        "draft_values": {
            "blind_pick_value": 70, "early_pick_value": 68, "last_pick_value": 72,
            "counter_pick_value": 70, "flexibility_value": 80, "counterability": 45,
        },
    },
    {
        "name": "Buster", "slug": "buster", "role": "tank", "tags": ["support"],
        "color": "#6d7a8c",
        "attributes": {
            "close_range": 85, "mid_range": 45, "burst_damage": 60,
            "objective_damage": 70, "area_control": 70, "zone_control": 80,
            "lane_control": 60, "knockback": 40,
            "tankiness": 85, "frontline": 92, "survivability": 80, "peel": 88,
            "engage": 65, "mobility": 35, "wallbreak": 55, "support": 70,
        },
        "draft_values": {
            "blind_pick_value": 65, "early_pick_value": 70, "last_pick_value": 60,
            "counter_pick_value": 65, "flexibility_value": 60, "counterability": 65,
        },
        "notes": "Sein Super schluckt Projektile - gegen Reichweitencomps stark.",
    },
    {
        "name": "Gene", "slug": "gene", "role": "controller", "tags": ["support"],
        "color": "#8b5fd6",
        "attributes": {
            "long_range": 65, "mid_range": 80, "safe_poke": 60, "poke": 65,
            "area_control": 55, "mid_control": 70, "crowd_control": 85,
            "anti_tank": 40, "anti_assassin": 55, "backline_pressure": 70,
            "survivability": 45, "peel": 70, "healing": 35, "support": 85,
            "mobility": 25,
        },
        "draft_values": {
            "blind_pick_value": 62, "early_pick_value": 65, "last_pick_value": 72,
            "counter_pick_value": 75, "flexibility_value": 68, "counterability": 55,
        },
    },
    {
        "name": "Tick", "slug": "tick", "role": "thrower", "tags": ["controller"],
        "color": "#7fb069",
        "attributes": {
            "mid_range": 70, "safe_poke": 85, "poke": 80, "burst_damage": 55,
            "area_control": 95, "zone_control": 90, "lane_control": 75,
            "objective_damage": 60, "bush_control": 70,
            "survivability": 20, "mobility": 20,
        },
        "draft_values": {
            "blind_pick_value": 55, "early_pick_value": 60, "last_pick_value": 58,
            "counter_pick_value": 65, "flexibility_value": 45, "counterability": 80,
        },
    },
    {
        "name": "Colette", "slug": "colette", "role": "damage", "tags": ["aggro"],
        "color": "#d65f8f",
        "attributes": {
            "mid_range": 80, "close_range": 55, "sustained_damage": 70, "poke": 70,
            "lane_control": 65, "mid_control": 60, "backline_pressure": 65,
            "anti_tank": 95, "objective_damage": 55,
            "survivability": 55, "engage": 70, "mobility": 60, "wallbreak": 35,
        },
        "draft_values": {
            "blind_pick_value": 60, "early_pick_value": 62, "last_pick_value": 82,
            "counter_pick_value": 90, "flexibility_value": 55, "counterability": 55,
        },
        "notes": "Schaden nach Prozent - der klassische Tank-Counter.",
    },
    {
        "name": "Piper", "slug": "piper", "role": "sniper", "tags": ["marksman"],
        "color": "#e8a0c0",
        "attributes": {
            "long_range": 95, "burst_damage": 90, "safe_poke": 75, "poke": 80,
            "lane_control": 85, "mid_control": 60, "backline_pressure": 40,
            "survivability": 20, "disengage": 60, "mobility": 30,
        },
        "draft_values": {
            "blind_pick_value": 55, "early_pick_value": 60, "last_pick_value": 62,
            "counter_pick_value": 60, "flexibility_value": 45, "counterability": 85,
        },
    },
    {
        "name": "Mortis", "slug": "mortis", "role": "assassin", "tags": ["aggro"],
        "color": "#5a5a8c",
        "attributes": {
            "close_range": 90, "burst_damage": 70, "sustained_damage": 50,
            "backline_pressure": 95, "objective_damage": 45,
            "survivability": 50, "disengage": 80,
            "mobility": 95, "engage": 95, "bush_control": 45,
        },
        "draft_values": {
            "blind_pick_value": 35, "early_pick_value": 40, "last_pick_value": 70,
            "counter_pick_value": 85, "flexibility_value": 35, "counterability": 90,
        },
        "notes": "Großer Unterschied zwischen gutem und schlechtem Matchup.",
    },
    {
        "name": "Bull", "slug": "bull", "role": "tank", "tags": ["aggro"],
        "color": "#c17f4a",
        "attributes": {
            "close_range": 95, "burst_damage": 85, "objective_damage": 65,
            "tankiness": 88, "frontline": 85, "survivability": 75,
            "engage": 90, "mobility": 60, "wallbreak": 85, "bush_control": 60,
        },
        "draft_values": {
            "blind_pick_value": 50, "early_pick_value": 55, "last_pick_value": 65,
            "counter_pick_value": 70, "flexibility_value": 45, "counterability": 75,
        },
    },
    {
        "name": "Darryl", "slug": "darryl", "role": "tank", "tags": ["aggro"],
        "color": "#8c6f4a",
        "attributes": {
            "close_range": 90, "burst_damage": 80, "sustained_damage": 60,
            "objective_damage": 70, "backline_pressure": 75,
            "tankiness": 82, "frontline": 80, "survivability": 70, "disengage": 70,
            "engage": 92, "mobility": 80, "wallbreak": 60,
        },
        "draft_values": {
            "blind_pick_value": 55, "early_pick_value": 58, "last_pick_value": 68,
            "counter_pick_value": 72, "flexibility_value": 55, "counterability": 70,
        },
    },
    {
        "name": "Sandy", "slug": "sandy", "role": "controller", "tags": ["support"],
        "color": "#d6c48f",
        "attributes": {
            "mid_range": 75, "sustained_damage": 60, "poke": 60, "safe_poke": 55,
            "area_control": 88, "zone_control": 85, "mid_control": 80, "lane_control": 70,
            "slow": 60, "crowd_control": 55, "anti_assassin": 50,
            "survivability": 60, "peel": 65, "vision": 90, "bush_control": 75,
            "support": 80, "mobility": 40,
        },
        "draft_values": {
            "blind_pick_value": 75, "early_pick_value": 78, "last_pick_value": 65,
            "counter_pick_value": 55, "flexibility_value": 82, "counterability": 40,
        },
    },
    {
        "name": "Surge", "slug": "surge", "role": "damage", "tags": ["aggro"],
        "color": "#4ad6c8",
        "attributes": {
            "mid_range": 78, "long_range": 45, "burst_damage": 75, "sustained_damage": 65,
            "lane_control": 60, "mid_control": 65, "backline_pressure": 70,
            "anti_assassin": 40, "survivability": 55, "disengage": 75,
            "mobility": 85, "engage": 70, "objective_damage": 50,
        },
        "draft_values": {
            "blind_pick_value": 58, "early_pick_value": 60, "last_pick_value": 70,
            "counter_pick_value": 65, "flexibility_value": 62, "counterability": 60,
        },
        "notes": "Wird im Spielverlauf stärker - braucht eine Anfangsphase.",
    },
    {
        "name": "Stu", "slug": "stu", "role": "assassin", "tags": ["aggro"],
        "color": "#e8d04a",
        "attributes": {
            "close_range": 80, "mid_range": 60, "burst_damage": 65, "sustained_damage": 60,
            "backline_pressure": 88, "objective_damage": 55,
            "survivability": 45, "disengage": 90,
            "mobility": 92, "engage": 85, "wallbreak": 70,
        },
        "draft_values": {
            "blind_pick_value": 52, "early_pick_value": 55, "last_pick_value": 72,
            "counter_pick_value": 78, "flexibility_value": 55, "counterability": 70,
        },
    },
    {
        "name": "Poco", "slug": "poco", "role": "support", "tags": ["controller"],
        "color": "#d64a6f",
        "attributes": {
            "mid_range": 78, "sustained_damage": 55, "poke": 65, "safe_poke": 60,
            "area_control": 65, "lane_control": 60,
            "anti_assassin": 60, "survivability": 65, "peel": 75,
            "healing": 95, "support": 95, "mobility": 35, "bush_control": 50,
        },
        "draft_values": {
            "blind_pick_value": 68, "early_pick_value": 70, "last_pick_value": 62,
            "counter_pick_value": 60, "flexibility_value": 72, "counterability": 50,
        },
    },
    {
        "name": "Brock", "slug": "brock", "role": "marksman", "tags": ["sniper"],
        "color": "#e85a3a",
        "attributes": {
            "long_range": 90, "burst_damage": 85, "safe_poke": 70, "poke": 75,
            "lane_control": 80, "area_control": 55, "objective_damage": 80,
            "zone_control": 60, "survivability": 25, "mobility": 30, "wallbreak": 95,
        },
        "draft_values": {
            "blind_pick_value": 58, "early_pick_value": 62, "last_pick_value": 60,
            "counter_pick_value": 58, "flexibility_value": 55, "counterability": 80,
        },
    },
    {
        "name": "Pam", "slug": "pam", "role": "support", "tags": ["tank"],
        "color": "#d68f4a",
        "attributes": {
            "mid_range": 70, "close_range": 65, "sustained_damage": 80,
            "area_control": 60, "lane_control": 65, "zone_control": 60,
            "tankiness": 70, "frontline": 65, "survivability": 75, "peel": 60,
            "healing": 90, "support": 90, "mobility": 35, "objective_damage": 55,
        },
        "draft_values": {
            "blind_pick_value": 62, "early_pick_value": 65, "last_pick_value": 58,
            "counter_pick_value": 55, "flexibility_value": 65, "counterability": 55,
        },
    },
    {
        "name": "Frank", "slug": "frank", "role": "tank", "tags": ["controller"],
        "color": "#7a4ad6",
        "attributes": {
            "close_range": 88, "mid_range": 50, "burst_damage": 75,
            "area_control": 70, "zone_control": 75, "crowd_control": 80, "stun": 90,
            "objective_damage": 60, "wallbreak": 80,
            "tankiness": 92, "frontline": 90, "survivability": 78, "peel": 50,
            "engage": 70, "mobility": 25,
        },
        "draft_values": {
            "blind_pick_value": 48, "early_pick_value": 52, "last_pick_value": 60,
            "counter_pick_value": 62, "flexibility_value": 45, "counterability": 78,
        },
    },
    {
        "name": "Barley", "slug": "barley", "role": "thrower", "tags": ["controller"],
        "color": "#6fa8d6",
        "attributes": {
            "mid_range": 72, "safe_poke": 88, "poke": 85, "sustained_damage": 70,
            "area_control": 92, "zone_control": 92, "lane_control": 80,
            "objective_damage": 55, "bush_control": 65,
            "survivability": 25, "mobility": 25,
        },
        "draft_values": {
            "blind_pick_value": 58, "early_pick_value": 62, "last_pick_value": 60,
            "counter_pick_value": 68, "flexibility_value": 50, "counterability": 78,
        },
    },
    {
        "name": "Rosa", "slug": "rosa", "role": "tank", "tags": ["controller"],
        "color": "#5fb06f",
        "attributes": {
            "close_range": 85, "sustained_damage": 65, "objective_damage": 55,
            "area_control": 60, "zone_control": 70, "bush_control": 92,
            "tankiness": 80, "frontline": 82, "survivability": 85, "peel": 65,
            "engage": 75, "mobility": 50, "anti_assassin": 55,
        },
        "draft_values": {
            "blind_pick_value": 55, "early_pick_value": 58, "last_pick_value": 62,
            "counter_pick_value": 68, "flexibility_value": 58, "counterability": 62,
        },
    },
]


# =========================================================================
# Modi und Maps
# =========================================================================
MODI = [
    {
        "name": "Gem Grab", "slug": "gem-grab", "order": 1,
        "description": "Zehn Edelsteine halten, Countdown überleben.",
        "win_condition": "Mid kontrollieren und den Träger schützen",
        # Drei Aufgaben, nicht eine: Mid halten, Gems tragen koennen, den
        # gegnerischen Traeger unter Druck setzen. Bis 2026-09-19 kannte
        # das Profil nur Kontrolle - "wer traegt" und "wer holt sie
        # zurueck" kamen darin nicht vor. Die Aspekte dazu stehen in
        # config.MODUS_ZIELASPEKTE.
        "base_requirements": {
            "mid_control": 85, "area_control": 65, "zone_control": 60,
            "survivability": 65, "peel": 60, "lane_control": 55,
            "disengage": 55, "engage": 50, "backline_pressure": 45,
        },
    },
    {
        "name": "Brawl Ball", "slug": "brawl-ball", "order": 2,
        "description": "Zwei Tore, ein Ball.",
        "win_condition": "Raum für den Ballführenden schaffen",
        # Das TOR kam im Ziel dieses Modus bis 2026-09-19 nicht vor:
        # `objective_damage` stand nur auf einer einzelnen Map. Jetzt
        # steht es oben, daneben der Weg dorthin (mobility, engage) und
        # der Raum, den es dafuer braucht (frontline, peel).
        "base_requirements": {
            "objective_damage": 85, "frontline": 75, "engage": 70,
            "mobility": 70, "crowd_control": 60, "peel": 60,
            "wallbreak": 55, "close_range": 55, "burst_damage": 50,
        },
    },
    {
        "name": "Knockout", "slug": "knockout", "order": 3,
        "description": "Kein Respawn - jeder Fehler zählt doppelt.",
        "win_condition": "Keinen Spieler verlieren und Vorteile ausspielen",
        "base_requirements": {
            "long_range": 70, "safe_poke": 75, "poke": 70, "survivability": 65,
            "vision": 55, "bush_control": 50, "disengage": 55,
        },
    },
    {
        "name": "Heist", "slug": "heist", "order": 4,
        "description": "Gegnerischen Safe knacken, eigenen halten.",
        "win_condition": "Druck auf den Safe erzeugen, ohne die Lane zu verlieren",
        # Das Ziel des Modus, aus vorhandenen Begriffen zusammengesetzt:
        # den Safe treffen (objective_damage), ihn auch halten koennen
        # (sustained_damage - fehlte bis 2026-09-18 vollstaendig, obwohl
        # ein Safe nicht von einem Burst faellt), an ihn herankommen
        # (mobility, wallbreak, survivability) und den eigenen verteidigen
        # (zone_control, lane_control).
        "base_requirements": {
            "objective_damage": 90, "sustained_damage": 75, "lane_control": 70,
            "zone_control": 60, "wallbreak": 55, "burst_damage": 55,
            "survivability": 55, "mobility": 50,
        },
    },
    {
        "name": "Hot Zone", "slug": "hot-zone", "order": 6,
        "description": "Zonen besetzen und halten.",
        "win_condition": "Laenger auf der Zone stehen als der Gegner",
        # Das Ziel ist Zeit auf der Zone, nicht Kills. Aus vorhandenem
        # Vokabular zusammengesetzt: die Zone verweigern (zone_control,
        # area_control), darauf bleiben koennen (survivability, frontline,
        # healing), Gegner herunterdruecken (crowd_control), sie erreichen
        # (mobility) und Tanks beantworten, die sich daraufstellen
        # (anti_tank). "zone_time" und "sustain" entstehen daraus als
        # Kombination - keine eigenen Felder.
        #
        # Aufgenommen am 2026-09-19: Hot Zone war mit 2 240 gezaehlten
        # Partien der meistgespielte Modus und hatte keine einzige
        # Anforderung, keine aktive Map und keinen Draft.
        "base_requirements": {
            "zone_control": 85, "survivability": 80, "area_control": 70,
            "frontline": 60, "healing": 60, "crowd_control": 55,
            "anti_tank": 50, "mobility": 45,
        },
    },
    {
        "name": "Bounty", "slug": "bounty", "order": 5,
        "description": "Sterne sammeln, eigene nicht verschenken.",
        "win_condition": "Vorsprung halten statt Kills erzwingen",
        "base_requirements": {
            "long_range": 85, "safe_poke": 80, "poke": 75, "survivability": 60,
            "bush_control": 60, "vision": 65, "disengage": 60,
        },
    },
]

# Fruehere Katalogschluessel, die umbenannt wurden. Die Map heisst im Spiel
# "Hard Rock Mine"; der Katalog fuehrte sie als "Hart Rock Mine". Solange
# nur Demo-Daten existierten, fiel das nicht auf - echte Partien waeren nie
# auf diese Map abgebildet worden, weil der Import ueber den Schluessel geht.
MAP_UMBENENNUNGEN = {
    "hart-rock-mine": "hard-rock-mine",
}

MAPS = [
    {
        "name": "Hard Rock Mine", "slug": "hard-rock-mine", "mode": "gem-grab",
        "requirements": {
            "mid_control": 90, "area_control": 75, "zone_control": 70,
            "anti_tank": 60, "wallbreak": 55, "bush_control": 45,
            "long_range": 55, "peel": 65,
        },
        "traits": {"openness": 45, "wall_density": 70, "bush_density": 40,
                   "choke_points": 70, "lane_count": 3},
        "notes": "Halb offen, klare Chokes um die Mine.",
    },
    {
        "name": "Undermine", "slug": "undermine", "mode": "gem-grab",
        "requirements": {
            "mid_control": 85, "area_control": 80, "zone_control": 80,
            "wallbreak": 75, "anti_thrower": 70, "long_range": 35,
            "close_range": 60, "bush_control": 55,
        },
        "traits": {"openness": 25, "wall_density": 85, "bush_density": 55,
                   "choke_points": 85, "lane_count": 3},
        "notes": "Eng, viele Wände - Thrower fühlen sich wohl.",
    },
    {
        "name": "Backyard Bowl", "slug": "backyard-bowl", "mode": "brawl-ball",
        "requirements": {
            "frontline": 70, "mobility": 80, "long_range": 65, "engage": 65,
            "peel": 60, "crowd_control": 60, "wallbreak": 35, "objective_damage": 50,
        },
        "traits": {"openness": 75, "wall_density": 30, "bush_density": 30,
                   "choke_points": 30, "lane_count": 3},
        "notes": "Offen - lange Sichtlinien, wenig Deckung.",
    },
    {
        "name": "Center Stage", "slug": "center-stage", "mode": "brawl-ball",
        "requirements": {
            "frontline": 85, "anti_tank": 80, "wallbreak": 85, "bush_control": 70,
            "crowd_control": 75, "close_range": 70, "engage": 70, "long_range": 35,
            "peel": 65,
        },
        "traits": {"openness": 25, "wall_density": 80, "bush_density": 70,
                   "choke_points": 80, "lane_count": 3},
        "notes": "Eng und verwinkelt - hier entscheiden Tanks und Wandbrecher.",
    },
    {
        "name": "Belle's Rock", "slug": "belles-rock", "mode": "knockout",
        "requirements": {
            "long_range": 90, "safe_poke": 80, "poke": 80, "survivability": 65,
            "disengage": 60, "vision": 55, "close_range": 25, "mobility": 45,
        },
        "traits": {"openness": 80, "wall_density": 35, "bush_density": 25,
                   "choke_points": 35, "lane_count": 3},
        "notes": "Weite Sichtlinien - Nahkampf hat es schwer.",
    },
    {
        "name": "Goldarm Gulch", "slug": "goldarm-gulch", "mode": "knockout",
        "requirements": {
            "bush_control": 90, "vision": 85, "area_control": 70, "poke": 65,
            "survivability": 60, "long_range": 50, "close_range": 55, "anti_assassin": 60,
        },
        "traits": {"openness": 35, "wall_density": 45, "bush_density": 90,
                   "choke_points": 50, "lane_count": 3},
        "notes": "Buschlastig - wer nichts sieht, verliert Spieler.",
    },
    {
        "name": "Safe Zone", "slug": "safe-zone", "mode": "heist",
        # Nur die ABWEICHUNGEN vom Heist-Grundprofil: zwei lange Lanes mit
        # Waenden dazwischen. Was hier frueher stand (objective_damage 95,
        # zone_control 55, burst 70), war eine Kopie des Modus - dadurch
        # sah eine Modusfrage wie eine Mapfrage aus.
        "requirements": {
            "lane_control": 75, "mobility": 70, "wallbreak": 60, "long_range": 45,
        },
        "traits": {"openness": 45, "wall_density": 60, "bush_density": 35,
                   "choke_points": 60, "lane_count": 2},
    },
    {
        "name": "Snake Prairie", "slug": "snake-prairie", "mode": "bounty",
        "requirements": {
            "long_range": 80, "bush_control": 85, "vision": 80, "safe_poke": 70,
            "survivability": 60, "poke": 65, "disengage": 60,
        },
        "traits": {"openness": 40, "wall_density": 30, "bush_density": 85,
                   "choke_points": 40, "lane_count": 3},
    },
]


# =========================================================================
# Counter (gerichtet, -1 bis +1)
# =========================================================================
# Gelesen als: "brawler hat gegen gegner diesen Vorteil".
# Die Gegenrichtung wird NICHT automatisch erzeugt - wo sie zaehlt, steht
# sie als eigene Zeile.
COUNTER = [
    ("gale", "buster", 0.40, "hält ihn aus den Chokes, die er besetzen will"),
    ("gale", "bull", 0.45, "schiebt ihn aus der Reichweite, bevor er ankommt"),
    ("gale", "darryl", 0.40, "unterbricht seinen Ansturm"),
    ("gale", "mortis", 0.50, "stößt ihn aus dem Angriff heraus"),
    ("gale", "stu", 0.35, "nimmt ihm den Raum zum Nachsetzen"),
    ("gale", "frank", 0.42, "hält ihn dauerhaft auf Abstand"),
    ("gale", "rosa", 0.30, None),
    ("gale", "tick", -0.30, "kommt an ihn nicht heran"),
    ("gale", "piper", -0.25, "wird überschossen"),

    ("colette", "buster", 0.55, "prozentualer Schaden ignoriert seine Lebenspunkte"),
    ("colette", "frank", 0.55, "prozentualer Schaden ignoriert seine Lebenspunkte"),
    ("colette", "bull", 0.45, None),
    ("colette", "rosa", 0.40, None),
    ("colette", "pam", 0.35, None),
    ("colette", "piper", -0.35, "wird auf Distanz zerlegt"),
    ("colette", "belle", -0.20, None),

    ("piper", "mortis", -0.55, "verliert jeden Nahkampf"),
    ("piper", "stu", -0.50, None),
    ("piper", "buster", -0.40, "sein Super frisst die Kugeln"),
    ("piper", "belle", 0.25, "gewinnt das Fernduell"),
    ("piper", "tick", 0.45, "trifft ihn hinter seiner Fläche"),

    ("mortis", "piper", 0.60, "ist sofort an ihr dran"),
    ("mortis", "brock", 0.55, None),
    ("mortis", "tick", 0.55, "überspringt die Flächenkontrolle"),
    ("mortis", "belle", 0.40, None),
    ("mortis", "gale", -0.50, "wird herausgestoßen"),
    ("mortis", "rosa", -0.45, "kommt durch ihren Schild nicht durch"),
    ("mortis", "frank", -0.30, None),

    ("buster", "piper", 0.45, "sein Super schluckt ihre Schüsse"),
    ("buster", "brock", 0.45, None),
    ("buster", "belle", 0.35, None),
    ("buster", "colette", -0.50, None),
    ("buster", "gale", -0.35, "wird aus den Chokes geschoben"),

    ("belle", "gene", 0.25, "trifft ihn, bevor er ziehen kann"),
    ("belle", "tick", 0.35, None),
    ("belle", "buster", -0.30, None),
    ("belle", "mortis", -0.40, None),

    ("max", "tick", 0.50, "ist zu schnell für seine Flächen"),
    ("max", "barley", 0.50, None),
    ("max", "piper", 0.35, "schließt die Distanz sofort"),
    ("max", "brock", 0.35, None),
    ("max", "frank", 0.30, "läuft aus jedem Stun heraus"),

    ("stu", "tick", 0.50, None),
    ("stu", "barley", 0.45, None),
    ("stu", "piper", 0.45, None),
    ("stu", "gale", -0.35, None),

    ("tick", "bull", 0.35, "verweigert ihm die Annäherung"),
    ("tick", "frank", 0.35, None),
    ("tick", "rosa", 0.30, None),
    ("tick", "mortis", -0.55, None),
    ("tick", "max", -0.45, None),

    ("barley", "bull", 0.45, "hält ihn aus dem engen Raum"),
    ("barley", "buster", 0.35, None),
    ("barley", "rosa", 0.40, None),
    ("barley", "stu", -0.45, None),
    ("barley", "mortis", -0.50, None),

    ("gene", "mortis", 0.30, "zieht ihn aus dem Rückzug"),
    ("gene", "piper", 0.35, "zieht sie aus der Deckung"),
    ("gene", "belle", 0.25, None),

    ("frank", "piper", 0.40, "ein Stun genügt"),
    ("frank", "belle", 0.30, None),
    ("frank", "colette", -0.55, None),

    ("rosa", "mortis", 0.45, "ihr Schild hält seinen Burst aus"),
    ("rosa", "stu", 0.35, None),
    ("rosa", "piper", 0.30, None),
    ("rosa", "colette", -0.40, None),

    ("sandy", "piper", 0.35, "nimmt ihr die Sicht"),
    ("sandy", "brock", 0.35, None),
    ("sandy", "mortis", 0.25, None),

    ("brock", "buster", -0.45, None),
    ("brock", "mortis", -0.55, None),
    ("brock", "tick", 0.40, None),

    ("surge", "mortis", 0.35, None),
    ("surge", "stu", 0.30, None),
    ("surge", "piper", -0.30, None),

    ("poco", "mortis", 0.40, "heilt den Burst weg"),
    ("poco", "stu", 0.35, None),
    ("poco", "piper", -0.35, None),

    ("pam", "tick", 0.35, None),
    ("pam", "barley", 0.30, None),
    ("pam", "colette", -0.45, None),

    ("bull", "piper", 0.45, "ist mit einem Ansturm an ihr dran"),
    ("bull", "brock", 0.45, None),
    ("bull", "tick", -0.40, None),
    ("bull", "colette", -0.45, None),
    ("bull", "gale", -0.45, None),

    ("darryl", "piper", 0.50, None),
    ("darryl", "belle", 0.40, None),
    ("darryl", "gale", -0.40, None),
    ("darryl", "colette", -0.40, None),
]


# =========================================================================
# Synergien (Mehrwert ueber die Einzelleistung hinaus)
# =========================================================================
SYNERGIE = [
    ("gale", "belle", 0.45, "Gale hält Aggro von Belle fern, Belle liefert die Reichweite"),
    ("gale", "piper", 0.50, "Gale ist der Grund, warum Piper stehen bleiben darf"),
    ("gale", "brock", 0.40, None),
    ("gale", "buster", 0.30, "beide verweigern Raum - zusammen ist der Choke dicht"),
    ("gene", "bull", 0.40, "Gene zieht heran, Bull macht den Rest"),
    ("gene", "darryl", 0.35, None),
    ("gene", "colette", 0.35, "gezogene Ziele sind sicherer Prozentschaden"),
    ("frank", "belle", 0.35, "Stun und sicherer Schaden aus der Distanz"),
    ("frank", "piper", 0.40, None),
    ("poco", "bull", 0.40, "Heilung macht den Ansturm überlebbar"),
    ("poco", "darryl", 0.35, None),
    ("poco", "rosa", 0.35, None),
    ("pam", "buster", 0.35, "zwei Frontlinien, die sich gegenseitig halten"),
    ("sandy", "piper", 0.40, "Sicht und Verschleierung für eine empfindliche Backline"),
    ("sandy", "belle", 0.35, None),
    ("max", "mortis", 0.40, "Tempo macht aus einem Angriff zwei"),
    ("max", "stu", 0.35, None),
    ("max", "surge", 0.30, None),
    ("tick", "belle", 0.30, "Fläche plus Reichweite verweigert die ganze Lane"),
    ("barley", "belle", 0.30, None),
    ("buster", "piper", 0.45, "sein Super ist ihr Schutzschild"),
    ("buster", "brock", 0.40, None),
    ("rosa", "tick", 0.30, "Rosa hält die Front, Tick verweigert dahinter"),
    # Negativbeispiele - gleiche Aufgabe, doppelt besetzt
    ("tick", "barley", -0.35, "zwei Thrower decken dieselbe Fläche doppelt ab"),
    ("piper", "brock", -0.25, "zwei empfindliche Fernkämpfer ohne Frontlinie"),
    ("bull", "darryl", -0.30, "zwei Ansturm-Tanks ohne Reichweite dahinter"),
    ("mortis", "stu", -0.30, "zwei Assassinen, niemand hält Raum"),
]


# =========================================================================
# Meta-Statistiken (Demo!)
# =========================================================================
# win_rate ist eine EINSCHAETZUNG, keine Messung. games=0 sagt genau das,
# und die Confidence ist entsprechend niedrig.
META = {
    "gale": (0.545, 0.22), "belle": (0.535, 0.20), "max": (0.530, 0.18),
    "buster": (0.520, 0.16), "gene": (0.515, 0.15), "tick": (0.495, 0.14),
    "colette": (0.525, 0.17), "piper": (0.505, 0.16), "mortis": (0.480, 0.12),
    "bull": (0.490, 0.13), "darryl": (0.500, 0.13), "sandy": (0.540, 0.19),
    "surge": (0.510, 0.14), "stu": (0.515, 0.15), "poco": (0.505, 0.14),
    "brock": (0.485, 0.13), "pam": (0.495, 0.13), "frank": (0.475, 0.12),
    "barley": (0.500, 0.14), "rosa": (0.505, 0.14),
}


# =========================================================================
# Builds
# =========================================================================
# Generische Gears gelten fuer alle Brawler (brawler=None).
GENERISCHE_GEARS = [
    ("Damage Gear", "damage-gear", "Mehr Schaden bei wenig Leben", 0.55),
    ("Shield Gear", "shield-gear", "Schild bei wenig Leben", 0.55),
    ("Speed Gear", "speed-gear", "Schneller im Gras", 0.45),
    ("Vision Gear", "vision-gear", "Sicht ins Gras", 0.40),
    ("Gadget Gear", "gadget-gear", "Eine Gadget-Ladung mehr", 0.45),
    ("Health Gear", "health-gear", "Regeneration außerhalb des Kampfes", 0.40),
    ("Super Charge Gear", "super-charge-gear", "Super lädt schneller", 0.45),
]

# (brawler, kind, name, slug, beschreibung, grundwert)
ITEMS = [
    ("gale", "gadget", "Spring Ejector", "spring-ejector", "Federfalle stößt Gegner weg", 0.45),
    ("gale", "gadget", "Twister", "twister", "Wirbel stößt alle Gegner in der Nähe weg", 0.55),
    ("gale", "star_power", "Blustery Blow", "blustery-blow", "Super betäubt kurz", 0.5),
    ("gale", "star_power", "Freezing Snow", "freezing-snow", "Angriffe verlangsamen", 0.55),
    ("gale", "hypercharge", "Hypercharge: Gale", "hypercharge-gale", "Super wird größer und stärker", 0.5),

    ("belle", "gadget", "Nest Egg", "nest-egg", "Falle am Boden", 0.5),
    ("belle", "gadget", "Positive Feedback", "positive-feedback", "Schild für kurze Zeit", 0.5),
    ("belle", "star_power", "Positive Feedback SP", "belle-sp-schild", "Schild beim Treffen", 0.5),
    ("belle", "star_power", "Grounded", "grounded", "Markierte Gegner können nicht entkommen", 0.55),

    ("colette", "gadget", "Na-ah!", "na-ah", "Springt zurück und heilt", 0.55),
    ("colette", "gadget", "Gotcha!", "gotcha", "Zieht sich zum Gegner", 0.45),
    ("colette", "star_power", "Push It", "push-it", "Super läuft weiter", 0.55),
    ("colette", "star_power", "Mass Tax", "mass-tax", "Mehr Grundschaden", 0.45),

    ("piper", "gadget", "Homemade Recipe", "homemade-recipe", "Schaden auf kurze Distanz", 0.5),
    ("piper", "gadget", "Auto Aimer", "auto-aimer", "Zielsuchender Schuss", 0.5),
    ("piper", "star_power", "Ambush", "ambush", "Mehr Schaden aus dem Busch", 0.5),
    ("piper", "star_power", "Snappy Sniping", "snappy-sniping", "Nachladen bei Treffer", 0.55),

    ("buster", "gadget", "Utility Belt", "utility-belt", "Kurzzeitiger Schub", 0.5),
    ("buster", "gadget", "Slo-Mo Replay", "slo-mo-replay", "Verlangsamt Gegner in der Nähe", 0.5),
    ("buster", "star_power", "Blockbuster", "blockbuster", "Mehr Schaden bei voller Leiste", 0.5),
    ("buster", "star_power", "Kevlar Vest", "kevlar-vest", "Schild beim Super", 0.55),

    ("mortis", "gadget", "Combo Spinner", "combo-spinner", "Flächenangriff", 0.5),
    ("mortis", "gadget", "Survival Shovel", "survival-shovel", "Lädt Super sofort", 0.55),
    ("mortis", "star_power", "Creepy Harvest", "creepy-harvest", "Heilung bei Kill", 0.5),
    ("mortis", "star_power", "Coiled Snake", "coiled-snake", "Weiterer Sprung nach Wartezeit", 0.55),

    ("max", "gadget", "Phase Shifter", "phase-shifter", "Kurzer Sprung nach vorn", 0.55),
    ("max", "gadget", "Sneaky Sneakers", "sneaky-sneakers", "Tempo für das Team", 0.45),
    ("max", "star_power", "Run n' Gun", "run-n-gun", "Tempo beim Angreifen", 0.5),
    ("max", "star_power", "Supercharged", "supercharged", "Super lädt beim Laufen", 0.55),

    ("tick", "gadget", "Last Hurrah", "last-hurrah", "Kurzzeitig unverwundbar", 0.55),
    ("tick", "gadget", "Mine Mania", "mine-mania", "Drei Minen sofort", 0.5),
    ("tick", "star_power", "Automa-Tick Reload", "automa-tick-reload", "Schneller nachladen", 0.5),
    ("tick", "star_power", "Well Oiled", "well-oiled", "Schnellere Regeneration", 0.5),

    ("bull", "gadget", "T-Bone Injector", "t-bone-injector", "Sofortige Heilung", 0.55),
    ("bull", "gadget", "Stomper", "stomper", "Flächenschaden beim Landen", 0.45),
    ("bull", "star_power", "Berserker", "berserker", "Schneller nachladen bei wenig Leben", 0.55),
    ("bull", "star_power", "Tough Guy", "tough-guy", "Schild bei wenig Leben", 0.5),
]

# (item-slug, bedingung, gewicht, begruendung, prioritaet)
BUILD_REGELN = [
    ("twister", {"enemy_role_count": {"assassin": 1}}, 0.35,
     "{gegner} kommt auf kurze Distanz - der Wirbel schafft Abstand", 10),
    ("twister", {"enemy_role_count": {"tank": 2}}, 0.30,
     "Zwei Tanks im Gegnerteam - Wegstoßen ist hier mehr wert als eine Falle", 9),
    ("twister", {"map_trait_min": {"choke_points": 65}}, 0.25,
     "Viele Chokepoints auf {map} - der Wirbel räumt sie frei", 5),
    ("spring-ejector", {"map_trait_max": {"choke_points": 40}}, 0.25,
     "Offene Map - die Falle deckt den Raum besser ab als der Wirbel", 5),
    ("freezing-snow", {"enemy_role_count": {"tank": 1}}, 0.25,
     "Verlangsamung nimmt Tanks die Annäherung", 6),
    ("blustery-blow", {"mode": ["brawl-ball"]}, 0.25,
     "Im Brawl Ball unterbricht die Betäubung den Torlauf", 6),

    ("grounded", {"enemy_attr_min": {"mobility": 0.75}}, 0.30,
     "Der Gegner ist sehr beweglich - markierte Ziele kommen nicht mehr weg", 8),
    ("nest-egg", {"enemy_role_count": {"assassin": 1}}, 0.25,
     "Die Falle schützt gegen Angreifer, die auf dich zukommen", 6),

    ("na-ah", {"enemy_role_count": {"assassin": 1}}, 0.30,
     "Rückzug plus Heilung gegen Angreifer wie {gegner}", 8),
    ("push-it", {"enemy_role_count": {"tank": 2}}, 0.30,
     "Zwei Tanks - der durchlaufende Super trifft beide mehrfach", 8),

    ("homemade-recipe", {"enemy_role_count": {"assassin": 1}}, 0.35,
     "Dein größtes Problem kommt auf Nahdistanz - dagegen hilft nur das", 10),
    ("ambush", {"map_trait_min": {"bush_density": 65}}, 0.30,
     "Viele Büsche auf {map} - der Hinterhaltsbonus ist hier oft aktiv", 7),

    ("kevlar-vest", {"enemy_attr_min": {"long_range": 0.8}}, 0.30,
     "Gegen Fernkämpfer ist der Schild beim Super entscheidend", 8),
    ("slo-mo-replay", {"enemy_role_count": {"assassin": 1}}, 0.25,
     "Verlangsamung hält Angreifer von dir und deiner Backline fern", 6),

    ("survival-shovel", {"enemy_attr_min": {"peel": 0.8}}, 0.30,
     "Der Gegner kann dich wegstoßen - eine zusätzliche Super-Ladung rettet den Angriff", 8),
    ("coiled-snake", {"map_trait_max": {"openness": 40}}, 0.25,
     "Enge Map - der zusätzliche Sprung erreicht die Backline überhaupt erst", 6),

    ("phase-shifter", {"enemy_role_count": {"thrower": 1}}, 0.30,
     "Gegen Flächenkontrolle ist der Sprung der schnellste Weg hinein", 8),
    ("supercharged", {"mode": ["gem-grab", "brawl-ball"]}, 0.20,
     "Häufige Rotationen laden den Super von allein", 4),

    ("last-hurrah", {"enemy_role_count": {"assassin": 1}}, 0.35,
     "Du bist das erste Ziel jedes Angreifers - das Gadget rettet dich", 10),
    ("mine-mania", {"map_trait_min": {"choke_points": 65}}, 0.25,
     "Enge Wege auf {map} - drei Minen schließen sie sofort", 6),

    ("t-bone-injector", {"enemy_attr_min": {"burst_damage": 0.8}}, 0.30,
     "Gegen Burst-Schaden ist Sofortheilung mehr wert als Flächenschaden", 7),
    ("berserker", {"enemy_role_count": {"tank": 1}}, 0.20,
     "Im langen Nahkampf entscheidet die Nachladegeschwindigkeit", 5),

    # Generische Gears
    ("shield-gear", {"enemy_attr_min": {"burst_damage": 0.8}}, 0.20,
     "Viel Burst-Schaden im Gegnerteam", 4),
    ("vision-gear", {"map_trait_min": {"bush_density": 70}}, 0.25,
     "Buschlastige Map - Sicht ist hier ein eigener Vorteil", 5),
    ("speed-gear", {"map_trait_min": {"bush_density": 70}}, 0.15,
     "Im Gras bist du damit deutlich schneller unterwegs", 3),
    ("gadget-gear", {"enemy_role_count": {"assassin": 1}}, 0.15,
     "Eine Gadget-Ladung mehr gegen Angreifer", 3),
]
