"""Der Coach: aus Struktur werden Saetze.

Kein Textbaustein-Lager und kein Sprachmodell. Jeder Satz entsteht aus
Werten, die anderswo berechnet wurden - Rollenprofil, Teamluecke,
Matchup-Vorteil, Map-Merkmal. Das hat zwei Folgen, die beide erwuenscht
sind:

1. Der Coach kann nichts behaupten, was die Bewertung nicht hergibt.
   Erklaerung und Score koennen nicht auseinanderlaufen.
2. Neue Brawler brauchen keine neuen Texte. Wer Attribute pflegt,
   bekommt die Saetze umsonst.

Die Sprache bleibt bewusst konkret ("halte Buster aus den Chokes")
statt allgemein ("spiele gut") - allgemeine Ratschlaege bringen einem
Spieler nichts bei, und Draften beibringen ist der Zweck des Werkzeugs.
"""

from itertools import permutations

from drafter import attributes as attr
from drafter.models import BrawlerItem
from drafter.services.counters import bestes_matchup, schlechtestes_matchup, vorteil

LANES = ("Links", "Mitte", "Rechts")


# =========================================================================
# Einzelner Brawler
# =========================================================================

def rolle_im_team(brawler, analyse=None):
    """Was dieser Brawler in diesem Team konkret ist.

    Nicht die Klasse aus dem Katalog, sondern die Aufgabe: derselbe
    Controller ist neben einem Tank etwas anderes als neben zwei
    Snipern. Deshalb fliesst ein, welche Luecke er hier schliesst.
    """
    if not brawler.hat_profil:
        # Kein Profil, keine Rolle - nichts behaupten, was die Daten nicht hergeben.
        return "Ohne Profil"
    haupt = attr.ROLLEN_LABEL.get(brawler.role, brawler.role)
    staerken = brawler.staerken(grenze=65, anzahl=2)

    if analyse is not None:
        zuwachs = analyse.zuwachs(brawler)
        wichtig = sorted(
            ((k, analyse.bedarf.get(k, 0) * v) for k, v in zuwachs.items()),
            key=lambda p: -p[1],
        )
        if wichtig and wichtig[0][1] > 0.06:
            key = wichtig[0][0]
            return f"{haupt} / {attr.EIGENSCHAFT_NACH_KEY[key].label}"

    if staerken:
        return f"{haupt} / {staerken[0].label}"
    return haupt


def aufgaben(brawler, ctx, analyse, raum, zugewiesener_gegner=None):
    """Was dieser Spieler tun soll - in der Reihenfolge der Wichtigkeit.

    `zugewiesener_gegner` kommt aus der Team-Zuordnung. Ohne ihn sucht
    sich jeder Spieler sein bestes Matchup selbst - und dann bekommen
    zwei Spieler denselben Gegner zugewiesen, waehrend der dritte
    unbeaufsichtigt bleibt. Der Teamplan sagt dann etwas anderes als die
    Spielerkarte daneben. Im fertigen Matchplan wird deshalb die
    abgestimmte Zuordnung durchgereicht.
    """
    saetze = []

    # 1. Die Luecke, die er schliesst, ist sein Hauptauftrag.
    if analyse is not None and analyse.brawler:
        zuwachs = analyse.zuwachs(brawler)
        kritisch = analyse.kritische_luecken(mindestens=0.15)
        for eigenschaft, _ in kritisch[:1]:
            if zuwachs.get(eigenschaft.key, 0) > 0.15:
                saetze.append(
                    # Label NICHT kleinschreiben: die Beschriftungen sind
                    # Substantive ("Lange Reichweite"), und .lower() macht
                    # daraus mitten im Satz einen Rechtschreibfehler.
                    f"Du bist unsere Antwort auf {eigenschaft.label} - "
                    "das fällt sonst niemandem im Team zu."
                )

    # 2. Sein bevorzugtes Matchup.
    if zugewiesener_gegner is not None:
        wert = vorteil(brawler, zugewiesener_gegner, raum)[0]
        saetze.append(
            f"Nimm dir {zugewiesener_gegner.name} vor - dieses Matchup gewinnst du."
            if wert > 0.05 else
            f"Du stehst gegen {zugewiesener_gegner.name} - das Matchup ist nicht "
            "geschenkt, halte es offen, statt es zu erzwingen."
        )
    else:
        bestes = bestes_matchup(brawler, list(ctx.enemy_picks), raum)
        if bestes:
            saetze.append(
                f"Nimm dir {bestes['gegner']} vor - dieses Matchup gewinnst du."
            )

    # 3. Schutzauftrag fuer empfindliche Mitspieler.
    #
    # Steht bewusst VOR dem Map-Hinweis: die Liste wird auf drei Saetze
    # gekuerzt, und "halte Piper den Ruecken frei" ist eine Anweisung,
    # die im Spiel etwas aendert - "Buschkontrolle zaehlt hier viel" ist
    # eine Beobachtung. Bei begrenztem Platz gewinnt die Anweisung.
    for mitspieler in ctx.own_picks:
        if mitspieler.id == brawler.id:
            continue
        bedarf = mitspieler.wert_oder("long_range") * (1 - mitspieler.wert_oder("survivability"))
        if bedarf > 0.4 and max(brawler.wert_oder("peel"), brawler.wert_oder("anti_assassin")) > 0.55:
            saetze.append(
                f"Halte {mitspieler.name} den Rücken frei - allein wird "
                f"{mitspieler.name} schnell zum ersten Ziel."
            )
            break

    # 4. Was die Map von seinen Staerken verlangt.
    if ctx.brawl_map is not None:
        anforderungen = ctx.brawl_map.anforderungs_vektor()
        passend = sorted(
            ((k, w * brawler.wert_oder(k)) for k, w in anforderungen.items()),
            key=lambda p: -p[1],
        )
        if passend and passend[0][1] > 0.35:
            key = passend[0][0]
            saetze.append(
                f"{attr.EIGENSCHAFT_NACH_KEY[key].label} ist auf "
                f"{ctx.brawl_map.name} entscheidend - dafür bist du da."
            )

    return saetze[:3]


def vermeiden(brawler, ctx, raum):
    """Was dieser Spieler NICHT tun soll - genauso wichtig wie die Aufgabe."""
    saetze = []

    schlecht = schlechtestes_matchup(brawler, list(ctx.enemy_picks), raum)
    if schlecht:
        saetze.append(
            f"Such nicht den direkten Kampf mit {schlecht['gegner']} - "
            "das Matchup verlierst du."
        )

    # Wer wenig Mobilitaet hat, darf sich nicht verrennen.
    if brawler.wert_oder("mobility") < 0.3 and brawler.wert_oder("long_range") > 0.55:
        saetze.append("Geh nicht zu weit nach vorn - du kommst allein nicht zurück.")

    # Wer vom Team lebt, soll nicht allein losziehen.
    if brawler.wert_oder("survivability") < 0.4 and brawler.wert_oder("engage") > 0.55:
        saetze.append("Geh nicht ohne dein Team rein - du hältst keinen Fokus aus.")

    # Ressourcen nicht am Falschen verbrennen.
    harmlos = [
        g for g in ctx.enemy_picks
        if vorteil(g, brawler, raum)[0] < -0.15 and g.wert_oder("mobility") > 0.6
    ]
    if harmlos:
        saetze.append(
            f"Verschwende keine Zeit damit, {harmlos[0].name} zu jagen - "
            "die Verfolgung geht selten auf und du fehlst anderswo."
        )

    return saetze[:3]


def warnungen(brawler, ctx, raum, katalog=None):
    """Worauf dieser Spieler achten muss - konkrete Gefahren des Gegners.

    `katalog` ist optional. Er lohnt sich, sobald mehrere Kandidaten
    hintereinander bewertet werden: die gegnerische Ausruestung ist fuer
    alle dieselbe und wuerde sonst je Kandidat neu abgefragt.
    """
    hinweise = []

    for gegner in ctx.enemy_picks:
        wert, _, _ = vorteil(gegner, brawler, raum)
        if wert > 0.2:
            hinweise.append(f"{gegner.name} bestraft dich hart, wenn du offen stehst.")

    # Gepflegte gegnerische Gadgets/Star Powers als konkrete Gefahr.
    # Nur wenn wirklich etwas gepflegt ist - nichts erfinden.
    gefaehrlich = (BrawlerItem.Kind.GADGET, BrawlerItem.Kind.STAR_POWER)
    if katalog is not None:
        gefahren = [
            g for gegner in ctx.enemy_picks
            for g in katalog.fuer(gegner) if g.kind in gefaehrlich
        ][:3]
    else:
        gefahren = list(BrawlerItem.objects.filter(
            brawler__in=list(ctx.enemy_picks),
            kind__in=list(gefaehrlich),
            is_active=True,
        ).select_related("brawler")[:3])
    for gegenstand in gefahren:
        if gegenstand.description:
            hinweise.append(
                f"{gegenstand.brawler.name}: {gegenstand.name} - {gegenstand.description}"
            )

    if ctx.brawl_map is not None and ctx.brawl_map.trait("bush_density", 0) > 65:
        if brawler.wert_oder("bush_control") < 0.35:
            hinweise.append(
                f"Viele Büsche auf {ctx.brawl_map.name} - lauf nicht blind hinein."
            )

    return hinweise[:4]


# =========================================================================
# Ganzes Team
# =========================================================================

def matchup_zuordnung(eigene, gegner, raum):
    """Wer nimmt sich wen vor - global optimal, nicht greedy.

    Geprueft wird JEDE injektive Zuordnung, gewaehlt die mit der besten
    Gesamtsumme. Bei 3v3 sind das genau die sechs Permutationen. Das
    beste Einzelmatchup zuerst zu vergeben (greedy) kann die beiden
    anderen Spieler in hoffnungslose Duelle schicken.

    Die kleinere Seite wird vollstaendig zugeordnet, aus der groesseren
    werden alle geordneten Auswahlen passender Laenge probiert. Frueher
    wurden nur Permutationen der GEGNER gebildet - bei drei eigenen gegen
    zwei gegnerische Picks blieb der dritte eigene Spieler dadurch nie
    beruecksichtigt (nachgemessen: 192 von 300 Zufallsdrafts
    suboptimal). 3v3 und 2v3 waren nicht betroffen.
    """
    if not eigene or not gegner:
        return []

    # Vorteile einmal rechnen statt je Permutation erneut.
    # Unbekannte Paare (kein Profil, keine Messung) gehen mit 0 in die
    # Summe ein und werden als "bekannt: False" ausgewiesen - eine Zuordnung
    # braucht jeder Spieler, eine Vorteilsbehauptung nicht.
    matrix, bekannt = {}, {}
    for a in eigene:
        for b in gegner:
            wert, _, quelle = vorteil(a, b, raum)
            matrix[(a.id, b.id)] = wert
            bekannt[(a.id, b.id)] = quelle is not None

    if len(eigene) <= len(gegner):
        varianten = ((eigene, auswahl) for auswahl in permutations(gegner, len(eigene)))
    else:
        varianten = ((auswahl, gegner) for auswahl in permutations(eigene, len(gegner)))

    beste = None
    bester_wert = None
    for unsere, ihre in varianten:
        paare = [(a, b, matrix[(a.id, b.id)]) for a, b in zip(unsere, ihre)]
        summe = sum(w for _, _, w in paare)
        # Bei Gleichstand bleibt die zuerst gefundene - deterministisch.
        if bester_wert is None or summe > bester_wert + 1e-12:
            bester_wert = summe
            beste = paare

    # In Teamreihenfolge ausgeben, damit die Liste zur Aufstellung passt.
    reihenfolge = {b.id: i for i, b in enumerate(eigene)}
    beste.sort(key=lambda paar: reihenfolge[paar[0].id])

    return [
        {
            "unser": a.name, "unser_slug": a.slug,
            "gegner": b.name, "gegner_slug": b.slug,
            "vorteil": round(w, 2),
            "bekannt": bekannt[(a.id, b.id)],
        }
        for a, b, w in beste
    ]


def lane_vorschlag(eigene, ctx):
    """Oeffnungspositionen - ausdruecklich als Vorschlag, nicht als Gesetz.

    Lanes wechseln im Spiel staendig. Der Vorschlag sagt nur, wo man
    *anfaengt*: wer Mid halten kann, geht nach Mitte, der Rest verteilt
    sich. Wer daraus eine feste Regel macht, spielt schlechter.
    """
    # Nur wer ein Profil hat, bekommt eine Lane - fuer die anderen ist
    # nicht bekannt, ob sie Mid halten oder allein zurechtkommen.
    eigene = [b for b in eigene if b.hat_profil]
    if not eigene:
        return []

    nach_mid = sorted(eigene, key=lambda b: -(b.wert_oder("mid_control") + b.wert_oder("area_control")))
    mitte = nach_mid[0]
    rest = [b for b in eigene if b.id != mitte.id]

    # Die aeusseren Lanes nach Eigenstaendigkeit verteilen: wer allein
    # zurechtkommt, geht auf die Seite, die weiter vom Team weg liegt.
    rest.sort(key=lambda b: -(b.wert_oder("survivability") + b.wert_oder("mobility")))

    zuordnung = [{"lane": "Mitte", "brawler": mitte.name, "slug": mitte.slug,
                  "grund": "beste Mid-Kontrolle im Team"}]
    gruende = ("kommt auf der Seite allein zurecht", "bleibt nah am Team")
    for lane, b, grund in zip(("Links", "Rechts"), rest, gruende):
        zuordnung.append({"lane": lane, "brawler": b.name, "slug": b.slug, "grund": grund})
    return zuordnung


def win_condition(ctx, analyse, raum):
    """Ein Satz, wie dieses Team gewinnt."""
    if not ctx.own_picks:
        return ""

    teile = []
    # Nicht die groesste Staerke nennen, sondern die groesste Staerke,
    # die hier auch zaehlt: eine hohe Deckung in etwas, das die Map gar
    # nicht verlangt, ist keine Win Condition.
    staerken = sorted(
        analyse.staerken(anzahl=5),
        key=lambda paar: -(paar[1] * analyse.anforderungen.get(paar[0].key, 0.0)),
    )
    bekannte = [b for b in ctx.own_picks if b.hat_profil]
    if staerken and bekannte:
        eigenschaft = staerken[0][0]
        traeger = max(bekannte, key=lambda b: b.wert_oder(eigenschaft.key))
        teile.append(f"{traeger.name} setzt {eigenschaft.label} durch")

    zuordnung = matchup_zuordnung(list(ctx.own_picks), list(ctx.enemy_picks), raum)
    bestes = max(zuordnung, key=lambda z: z["vorteil"]) if zuordnung else None
    if bestes and bestes["vorteil"] > 0.1:
        teile.append(f"{bestes['unser']} neutralisiert {bestes['gegner']}")

    if ctx.game_mode is not None and ctx.game_mode.win_condition:
        teile.append(ctx.game_mode.win_condition.rstrip("."))

    return ". ".join(teile) + "." if teile else ""


def gefahren(ctx, analyse, raum):
    """Was dieses Team verliert, wenn es schiefgeht."""
    punkte = []
    for eigenschaft, dringlichkeit in analyse.kritische_luecken(mindestens=0.2)[:2]:
        punkte.append(
            f"{eigenschaft.label} fehlt uns - der Gegner kann das ausspielen."
        )
    for gegner in ctx.enemy_picks:
        schlimm = [
            b for b in ctx.own_picks if vorteil(gegner, b, raum)[0] > 0.25
        ]
        if len(schlimm) >= 2:
            punkte.append(
                f"{gegner.name} ist gegen mehrere von uns im Vorteil - nicht einzeln stellen."
            )
    return punkte[:4]


def team_schwaechen(ctx, analyse, raum):
    """Die wichtigsten Schwaechen des fertigen Teams - benannt und bewertet.

    Unterschied zu `gefahren()`: dort stehen Saetze fuer den Spieler,
    hier steht die Auswertung. Jede Schwaeche traegt mit, ob der Gegner
    sie ueberhaupt bespielen kann - eine Luecke, die niemand im
    gegnerischen Team ausnutzen kann, ist im Draft keine.
    """
    # Wer beim Gegner welche Luecke bestraft. Dieselben Paarungen wie in
    # services/team_need.py - sie stehen dort fuer die Bewertung, hier
    # fuer die Erklaerung.
    ausnutzer = {
        "anti_tank": lambda g: g.wert_oder("tankiness"),
        "anti_assassin": lambda g: max(g.wert_oder("engage"), g.wert_oder("mobility"))
            if {"assassin", "aggro"} & set(g.alle_rollen) else 0.0,
        "anti_thrower": lambda g: 1.0 if "thrower" in g.alle_rollen else 0.0,
        "long_range": lambda g: g.wert_oder("long_range"),
        "frontline": lambda g: g.wert_oder("frontline"),
        "mobility": lambda g: g.wert_oder("area_control"),
        "peel": lambda g: max(g.wert_oder("engage"), g.wert_oder("backline_pressure")),
    }

    schwaechen = []
    for eigenschaft, dringlichkeit in analyse.groesste_luecken(anzahl=6, mindestens=0.12):
        pruefung = ausnutzer.get(eigenschaft.key)
        bedrohung = None
        staerke = 0.0
        bekannte_gegner = [g for g in ctx.enemy_picks if g.hat_profil]
        if pruefung is not None and bekannte_gegner:
            bewertet = [(pruefung(g), g) for g in bekannte_gegner]
            staerke, kandidat = max(bewertet, key=lambda paar: paar[0])
            if staerke >= 0.5:
                bedrohung = kandidat

        schwaechen.append({
            "key": eigenschaft.key,
            "label": eigenschaft.label,
            "dringlichkeit": round(dringlichkeit * 100),
            "kritisch": eigenschaft.knapp,
            "ausgenutzt_von": bedrohung.name if bedrohung else None,
            "text": (
                f"{eigenschaft.label} fehlt - und {bedrohung.name} kann genau das bespielen."
                if bedrohung else
                f"{eigenschaft.label} fehlt, aber im gegnerischen Team steht niemand, "
                "der es ausnutzt."
            ),
        })

    # Ausnutzbare Schwaechen zuerst - sie kosten im Spiel tatsaechlich
    # etwas, die uebrigen sind Schoenheitsfehler.
    schwaechen.sort(key=lambda s: (s["ausgenutzt_von"] is None, -s["dringlichkeit"]))
    return schwaechen[:4]


def lane_tausch_plan(ctx, raum):
    """Was tun, wenn der Gegner die Lanes tauscht?

    Die eigentliche Aussage des Matchplans: ein Plan, der nur bei
    Stillhalten des Gegners funktioniert, ist keiner.
    """
    if len(ctx.own_picks) < 2 or len(ctx.enemy_picks) < 2:
        return []

    plan = []
    for gegner in ctx.enemy_picks:
        bewertet = sorted(
            ((vorteil(b, gegner, raum)[0], b) for b in ctx.own_picks),
            key=lambda p: -p[0],
        )
        bester = bewertet[0]
        schlechtester = bewertet[-1]
        if bester[0] - schlechtester[0] > 0.3:
            plan.append({
                "wenn": f"{gegner.name} geht auf {schlechtester[1].name}",
                "dann": (
                    f"{bester[1].name} übernimmt {gegner.name} - tauscht die Position"
                ),
            })
    return plan[:3]
