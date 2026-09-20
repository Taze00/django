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
from drafter.services import quellen, rollenwissen
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

    **Ohne eigenen Pick gibt es keinen Teambedarf.** Bis zum 2026-09-18
    rechnete diese Komponente auch bei leerem Team - und dann ist
    `bedarf` exakt der Anforderungsvektor der Map und `zuwachs` exakt das
    Profil des Kandidaten. Das Ergebnis war dasselbe Skalarprodukt, das
    Map & Modus ohnehin bildet: BUSTER bekam +10,36 aus Map & Modus und
    +3,83 aus Teambedarf, beides aus denselben zwei Vektoren. 44 % des
    Bewertungsgewichts aus einer einzigen gepflegten Zahlenreihe.
    Jetzt beantwortet die Komponente wieder ihre eigene Frage: was fehlt
    dem, was schon steht.

    Feldrelativ **und** absolut: der z-Wert sagt, wer von den
    Verfuegbaren am meisten hilft, der absolute Anteil verhindert, dass
    bei einem vollstaendig gedeckten Team trotzdem jemand als grosse
    Hilfe erscheint.
    """
    if not ctx.own_picks and not ctx.enemy_picks:
        # Nicht anwendbar - fuer jeden Kandidaten gleich, also Wert 0 und
        # ohne Anspruch auf Sicherheit.
        #
        # Die Bedingung ist bewusst eng: schon ein GEGNERISCHER Pick
        # erzeugt echten Bedarf (zwei Tanks verlangen Anti-Tank), und der
        # steht nicht im Anforderungsvektor der Map. Doppelt gezaehlt wird
        # nur im voellig leeren Draft - dort und nur dort sind
        # Map-Anforderung und Teambedarf dieselbe Rechnung.
        leer = {}
        for b in kandidaten:
            komp = Komponente(key=config.K_TEAM_NEED)
            komp.anwendbar = False
            komp.quelle = quellen.PROFILE if b.hat_profil else quellen.UNKNOWN
            komp.gruende.append(Grund(
                text="noch kein eigener Pick - Teambedarf entsteht erst danach",
                positiv=True, staerke=0.2,
            ))
            leer[b.id] = komp
        return leer

    roh = {}
    zuwaechse = {}
    for b in kandidaten:
        if not b.hat_profil:
            continue
        wert, zuwachs = _nutzen(analyse, b)
        roh[b.id] = wert
        zuwaechse[b.id] = zuwachs

    z = z_werte(roh)
    kritisch = analyse.kritische_luecken()

    # Ohne Profil, aber mit Draft-Rolle: welche unserer Luecken beruehrt
    # diese Rolle ueberhaupt? Die Dringlichkeit kommt aus der Teamanalyse,
    # also aus den Profilen der schon gepickten Brawler - die Rolle sagt
    # nur, ob sie zum Thema gehoert (services/rollenwissen.py).
    luecken = analyse.groesste_luecken(anzahl=5)
    roh_rolle = {}
    for b in kandidaten:
        if b.hat_profil:
            continue
        anteil = rollenwissen.lueckendeckung(b, luecken)
        if anteil is not None:
            roh_rolle[b.id] = anteil
    z_rolle = rollenwissen.rollen_z(roh_rolle)

    ergebnis = {}
    for b in kandidaten:
        komp = Komponente(key=config.K_TEAM_NEED)
        if not b.hat_profil:
            if b.id not in z_rolle:
                # Weder Eigenschaften noch Rolle: unbekannt, nicht 0.
                komp.verfuegbar = False
                ergebnis[b.id] = komp
                continue
            komp.wert = z_rolle[b.id]
            komp.quelle = quellen.FACHWISSEN
            if komp.wert > 0.1 and luecken:
                getroffen = [e.label for e, _ in luecken
                             if e.key in rollenwissen.deckt(b)][:1]
                if getroffen:
                    komp.gruende.append(Grund(
                        text=f"{b.draft_rolle_label} - deckt das Thema "
                             f"{getroffen[0]}, das uns fehlt (Rolle, kein Profil)",
                        positiv=True, staerke=0.5, quelle="fachquelle",
                    ))
            elif komp.wert < -0.1 and luecken:
                komp.gruende.append(Grund(
                    text=f"{b.draft_rolle_label} trifft unsere größte Lücke "
                         f"({luecken[0][0].label}) nicht",
                    positiv=False, staerke=0.45, quelle="fachquelle",
                ))
            ergebnis[b.id] = komp
            continue
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
    if not kandidat.hat_profil:
        # Ohne Eigenschaften laesst sich nicht sagen, WOVON wir zu viel
        # haetten - aber sehr wohl, ob dieselbe Draft-Rolle schon einmal
        # steht. Der Betrag kommt aus der Zahl der Picks, nicht aus einer
        # Einschaetzung. Ohne Rolle bleibt es unbekannt.
        if not rollenwissen.hat_fachwissen(kandidat) or not ctx.own_picks:
            komp.verfuegbar = False
            return komp
        doppelt = rollenwissen.gleiche_rolle(kandidat, ctx.own_picks)
        komp.wert = -klemme(doppelt * config.ROLLEN_REDUNDANZ_JE_PICK, 0.0, 1.0)
        komp.quelle = quellen.FACHWISSEN
        if doppelt:
            komp.gruende.append(Grund(
                text=f"wir haben schon {doppelt}x {kandidat.draft_rolle_label} "
                     "im Team (Rolle, kein Profil)",
                positiv=False, staerke=0.4 + 0.1 * doppelt, quelle="fachquelle",
            ))
        return komp
    strafe = 0.0

    # 1. Eigenschaften, die das Team bereits ueberdeckt.
    ueberdeckt = sum(
        analyse.ueberschuss.get(k, 0.0) * kandidat.wert_oder(k) for k in attr.ATTRIBUT_KEYS
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
    if not kandidat.hat_profil:
        # Welche Luecke nach ihm offen bleibt, haengt an seinen
        # Eigenschaften - unbekannt, also keine Strafe, die behauptet wird.
        komp.verfuegbar = False
        return komp
    if not ctx.enemy_picks:
        # Ohne bekannte Gegner gibt es keine belegbare Angreifbarkeit.
        # Die Gefahr steckt dann in der Konterbarkeit (draft_position).
        return komp

    nach_pick = analyse.__class__.bauen(
        analyse.brawler + [kandidat], analyse.anforderungen
    )

    # Luecke -> was beim Gegner sie ausnutzt
    paarungen = [
        ("anti_tank", lambda g: g.wert_oder("tankiness"), "Tanks"),
        ("anti_assassin", lambda g: max(g.wert_oder("engage"), g.wert_oder("mobility"))
            if "assassin" in g.alle_rollen or "aggro" in g.alle_rollen else 0.0, "Aggro"),
        ("anti_thrower", lambda g: 1.0 if "thrower" in g.alle_rollen else 0.0, "Thrower"),
        ("long_range", lambda g: g.wert_oder("long_range"), "Reichweite"),
    ]

    strafe = 0.0
    for key, bedrohung, bezeichnung in paarungen:
        offen = max(0.0, config.COVERAGE_ZIEL - nach_pick.profil.get(key, 0.0))
        if offen <= 0.05:
            continue
        # Nur Gegner mit Profil: eine unbekannte Bedrohung ist keine 0,
        # aber auch keine belegbare Gefahr.
        gegner_staerke = max(
            (bedrohung(g) for g in ctx.enemy_picks if g.hat_profil), default=0.0
        )
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
