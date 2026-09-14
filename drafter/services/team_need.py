"""Die drei teambezogenen Komponenten: Bedarf, Redundanz, Angreifbarkeit.

Sie stehen zusammen in einer Datei, weil sie dieselbe `Teamanalyse`
lesen und drei Seiten derselben Frage sind:

    Bedarf         - was fehlt uns, und schliesst er es?
    Redundanz      - haben wir davon schon genug?
    Angreifbarkeit - was bleibt offen, und kann der Gegner es ausnutzen?

Getrennt gerechnet, aber gemeinsam gedacht: ein Kandidat kann eine
Luecke schliessen (Bedarf +) und trotzdem eine andere offen lassen, die
das gegnerische Team gerade bestraft (Angreifbarkeit -).
"""

from drafter import attributes as attr
from drafter import config
from drafter.services.scoring import Grund, Komponente, klemme, z_werte


def _nutzen(analyse, kandidat):
    """Wie viel vom offenen Bedarf deckt dieser Kandidat wirklich ab?

    Multipliziert Dringlichkeit mit dem **Zuwachs** am Teamprofil, nicht
    mit dem Eigenwert des Kandidaten. Das ist der ganze Unterschied:
    ein zweiter Anti-Tank hat denselben Eigenwert wie der erste, aber
    fast keinen Zuwachs.
    """
    gesamt_bedarf = sum(analyse.bedarf.values())
    if gesamt_bedarf <= 0:
        return 0.0, {}
    zuwachs = analyse.zuwachs(kandidat)
    nutzen = sum(analyse.bedarf[k] * zuwachs.get(k, 0.0) for k in attr.ATTRIBUT_KEYS)
    return nutzen / gesamt_bedarf, zuwachs


def komponenten_fuer_pool(kandidaten, analyse, ctx):
    """Bedarfs-Komponente fuer alle Kandidaten.

    Feldrelativ **und** absolut: der z-Wert sagt, wer von den
    Verfuegbaren am meisten hilft, der absolute Anteil verhindert, dass
    bei einem vollstaendig gedeckten Team trotzdem jemand als grosse
    Hilfe erscheint.
    """
    roh = {}
    zuwaechse = {}
    for b in kandidaten:
        wert, zuwachs = _nutzen(analyse, b)
        roh[b.id] = wert
        zuwaechse[b.id] = zuwachs

    z = z_werte(roh)
    kritisch = analyse.kritische_luecken()

    ergebnis = {}
    for b in kandidaten:
        komp = Komponente(key=config.K_TEAM_NEED)
        absolut = klemme(roh[b.id] * 2.5)
        komp.wert = klemme(0.6 * z.get(b.id, 0.0) + 0.4 * absolut)

        # Begruendet wird nur ueber die kritischen Luecken - das sind die,
        # deren Fehlen ein Team tatsaechlich verliert.
        zuwachs = zuwaechse[b.id]
        for eigenschaft, dringlichkeit in kritisch[:2]:
            if zuwachs.get(eigenschaft.key, 0.0) >= 0.25:
                komp.gruende.append(Grund(
                    text=f"schließt unsere Lücke bei {eigenschaft.label}",
                    positiv=True, staerke=0.75 + dringlichkeit * 0.25,
                ))
        if not komp.gruende and komp.wert > 0.3:
            grosse = analyse.groesste_luecken(anzahl=2)
            for eigenschaft, _ in grosse:
                if zuwachs.get(eigenschaft.key, 0.0) >= 0.2:
                    komp.gruende.append(Grund(
                        text=f"bringt {eigenschaft.label}, was dem Team noch fehlt",
                        positiv=True, staerke=0.6,
                    ))
                    break
        if komp.wert < -0.3 and kritisch:
            komp.gruende.append(Grund(
                text=f"hilft nicht bei {kritisch[0][0].label} - unserer größten Lücke",
                positiv=False, staerke=0.55,
            ))
        ergebnis[b.id] = komp
    return ergebnis


def redundanz(kandidat, analyse, ctx):
    """Strafkomponente: wovon wir schon genug haben. Immer <= 0."""
    komp = Komponente(key=config.K_REDUNDANCY)
    strafe = 0.0

    # 1. Eigenschaften, die das Team bereits ueberdeckt.
    ueberdeckt = sum(
        analyse.ueberschuss.get(k, 0.0) * kandidat.wert(k) for k in attr.ATTRIBUT_KEYS
    )
    teiler = max(1.0, sum(1 for v in analyse.ueberschuss.values() if v > 0))
    strafe += min(0.5, ueberdeckt / teiler * 2.0)

    # 2. Rollen. Eine dritte Nahkampfrolle ist auch dann ein Problem,
    #    wenn die Einzelwerte gut aussehen.
    zaehler = dict(analyse.rollen)
    for rolle in kandidat.alle_rollen:
        neu = zaehler.get(rolle, 0) + 1
        grenze = config.ROLLEN_OBERGRENZE.get(rolle, 2)
        if neu > grenze:
            ueber = neu - grenze
            strafe += 0.30 * ueber
            komp.gruende.append(Grund(
                text=(
                    f"wäre unser {neu}. {attr.ROLLEN_LABEL.get(rolle, rolle)} - "
                    "das Team wird einseitig"
                ),
                positiv=False, staerke=0.7 + 0.1 * ueber,
            ))

    # 3. Bringt er ueberhaupt etwas Neues?
    if analyse.brawler:
        zuwachs = analyse.zuwachs(kandidat)
        neues = max(zuwachs.values()) if zuwachs else 0.0
        if neues < 0.12:
            strafe += 0.25
            komp.gruende.append(Grund(
                text="fügt dem Team kaum etwas hinzu, was es nicht schon hat",
                positiv=False, staerke=0.6,
            ))

    komp.wert = -klemme(strafe, 0.0, 1.0)
    return komp


def angreifbarkeit(kandidat, analyse, ctx):
    """Strafkomponente: was nach diesem Pick offen bleibt - und ausnutzbar ist.

    Eine Luecke ist nur dann schlimm, wenn der Gegner sie bespielen kann.
    Fehlender Anti-Tank gegen ein Team ohne Tank kostet nichts; gegen
    Buster und Frank kostet er das Spiel. Deshalb wird jede Restluecke
    mit der Faehigkeit des Gegnerteams multipliziert, sie auszunutzen.

    Die Zuordnung Luecke -> gegnerische Bedrohung ist bewusst kurz und
    explizit gehalten: vier Paarungen, die im Spiel tatsaechlich
    entscheiden. Eine vollstaendige Matrix waere Scheingenauigkeit.
    """
    komp = Komponente(key=config.K_WEAKNESS)
    if not ctx.enemy_picks:
        # Ohne bekannte Gegner gibt es keine belegbare Angreifbarkeit.
        # Die Gefahr steckt dann in der Konterbarkeit (draft_position).
        return komp

    nach_pick = analyse.__class__.bauen(
        analyse.brawler + [kandidat], analyse.anforderungen
    )

    # Luecke -> was beim Gegner sie ausnutzt
    paarungen = [
        ("anti_tank", lambda g: g.wert("tankiness"), "Tanks"),
        ("anti_assassin", lambda g: max(g.wert("engage"), g.wert("mobility"))
            if "assassin" in g.alle_rollen or "aggro" in g.alle_rollen else 0.0, "Aggro"),
        ("anti_thrower", lambda g: 1.0 if "thrower" in g.alle_rollen else 0.0, "Thrower"),
        ("long_range", lambda g: g.wert("long_range"), "Reichweite"),
    ]

    strafe = 0.0
    for key, bedrohung, bezeichnung in paarungen:
        offen = max(0.0, config.COVERAGE_ZIEL - nach_pick.profil.get(key, 0.0))
        if offen <= 0.05:
            continue
        gegner_staerke = max((bedrohung(g) for g in ctx.enemy_picks), default=0.0)
        if gegner_staerke < 0.5:
            continue
        wichtig = analyse.anforderungen.get(key, 0.3)
        beitrag = offen * gegner_staerke * (0.5 + 0.5 * wichtig)
        strafe += beitrag
        if beitrag > 0.18:
            fehlt = attr.EIGENSCHAFT_NACH_KEY[key].label
            komp.gruende.append(Grund(
                text=f"danach fehlt uns weiter {fehlt} - der Gegner hat {bezeichnung}",
                positiv=False, staerke=0.55 + beitrag,
            ))

    komp.wert = -klemme(strafe, 0.0, 1.0)
    return komp
