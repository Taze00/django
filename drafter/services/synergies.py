"""Synergie: was zwei Brawler zusammen koennen, das keiner allein kann.

Der haeufigste Fehler in Draft-Werkzeugen ist, gemeinsame Winrate als
Synergie zu lesen. Zwei starke Brawler gewinnen zusammen oft - nicht
weil sie sich ergaenzen, sondern weil beide stark sind. Synergie ist
deshalb hier als **Mehrwert ueber die Einzelleistung hinaus** definiert
(`SynergyStat.synergy`), und die Heuristik unten misst ebenfalls
Ergaenzung, nicht Summe.

Ergaenzung heisst konkret: der eine deckt, was der andere nicht kann.
Belle bringt Reichweite und ist wehrlos gegen Aggro; Gale bringt Peel.
Das Paar ist mehr als beide einzeln - zwei Belles waeren es nicht.
"""

from drafter import config
from drafter.services import quellen
from drafter.services.scoring import Grund, Komponente, klemme


def _beschuetzt(schuetzer, empfindlich):
    """Deckt `schuetzer` genau die Schwaeche von `empfindlich`?"""
    bedarf = empfindlich.wert("long_range") * (
        1.0 - max(empfindlich.wert("survivability"), empfindlich.wert("mobility"))
    )
    schutz = max(schuetzer.wert("peel"), schuetzer.wert("anti_assassin"))
    return bedarf * schutz


def heuristische_synergie(a, b):
    """Geschaetzte Ergaenzung zweier Brawler, [-1, +1], plus Begruendung."""
    signale = []

    # 1. Schutz fuer empfindliche Reichweite - in beide Richtungen pruefen.
    for schuetzer, geschuetzt in ((a, b), (b, a)):
        wert = _beschuetzt(schuetzer, geschuetzt)
        if wert > 0.25:
            signale.append((
                wert * 0.8,
                f"{schuetzer.name} schützt {geschuetzt.name} gegen Aggro",
            ))

    # 2. Kontrolle plus Schaden: wer festhaelt, braucht jemanden, der trifft.
    for halter, treffer in ((a, b), (b, a)):
        halten = max(halter.wert("crowd_control"), halter.wert("stun"), halter.wert("slow"))
        schaden = max(treffer.wert("burst_damage"), treffer.wert("objective_damage"))
        if halten > 0.5 and schaden > 0.6:
            signale.append((
                halten * schaden * 0.55,
                f"{halter.name} hält fest, {treffer.name} bestraft es",
            ))

    # 3. Frontline plus Backline: einer bindet, der andere wirkt aus der Distanz.
    for vorn, hinten in ((a, b), (b, a)):
        if vorn.wert("frontline") > 0.6 and hinten.wert("long_range") > 0.6:
            signale.append((
                vorn.wert("frontline") * hinten.wert("long_range") * 0.45,
                f"{vorn.name} bindet vorn, {hinten.name} wirkt aus der Distanz",
            ))

    # 4. Sicht und Buschkontrolle fuer jemanden, der davon lebt.
    for seher, nutzer in ((a, b), (b, a)):
        if seher.wert("vision") > 0.55 and nutzer.wert("long_range") > 0.6:
            signale.append((
                seher.wert("vision") * nutzer.wert("long_range") * 0.35,
                f"{seher.name} schafft Sicht für {nutzer.name}",
            ))

    # 5. Abzug fuer Gleichfoermigkeit: identische Profile ergaenzen nichts.
    # Nur die auffaelligen Rollen zaehlen, nicht jede geteilte Eigenschaft.
    gemeinsam = set(a.alle_rollen) & set(b.alle_rollen)
    if gemeinsam and len(gemeinsam) >= max(1, min(len(a.alle_rollen), len(b.alle_rollen))):
        signale.append((-0.25, f"{a.name} und {b.name} machen dasselbe"))

    if not signale:
        return 0.0, None
    gesamt = klemme(sum(w for w, _ in signale))
    staerkstes = max(signale, key=lambda p: abs(p[0]))
    return gesamt, (staerkstes[1] if abs(staerkstes[0]) > 0.12 else None)


def paar(a, b, raum):
    """Synergie eines Paares nach Quellenprioritaet (services/quellen.py).

    Gibt (wert, grund, quelle) zurueck; quelle None = nichts bekannt.
    """
    eintrag = raum.synergie(a, b)
    prior = raum.synergie_prior(a, b)
    gemessen = eintrag if (eintrag is not None and not eintrag.is_demo
                           and (eintrag.games or 0) > 0) else None
    if prior is None and eintrag is not None and gemessen is None:
        prior = eintrag    # reiner Demo-Provider oder synthetisch: gilt als gepflegt

    if gemessen is not None or prior is not None:
        n = float(gemessen.sample_size or gemessen.games or 0) if gemessen else 0.0
        wert, quelle = quellen.mischen(
            gemessen.synergy if gemessen else None,
            prior.synergy if prior else None,
            n, config.PAAR_PRIOR_STAERKE,
        )
        text = (prior.reason if prior is not None and gemessen is None else "") or (
            f"{a.name} und {b.name} ergänzen sich" if wert > 0
            else f"{a.name} und {b.name} beißen sich"
        )
        return klemme(wert), text, quelle
    if not (a.hat_profil and b.hat_profil):
        # Ergaenzung laesst sich ohne Eigenschaften nicht schaetzen.
        return 0.0, None, None
    wert, grund = heuristische_synergie(a, b)
    return wert, grund, quellen.PROFILE


def komponente(kandidat, ctx, raum):
    """Synergie-Komponente: wie gut passt der Kandidat zu unseren Picks."""
    komp = Komponente(key=config.K_SYNERGY)
    if not ctx.own_picks:
        komp.quelle = quellen.PROFILE if kandidat.hat_profil else quellen.UNKNOWN
        return komp

    werte = []
    herkunft = []
    for mitspieler in ctx.own_picks:
        wert, grund, quelle = paar(kandidat, mitspieler, raum)
        if quelle is None:
            continue
        werte.append(wert)
        herkunft.append(quelle)
        if grund and abs(wert) > 0.15:
            komp.gruende.append(Grund(
                text=grund, positiv=wert > 0, staerke=min(1.0, abs(wert) + 0.25),
                quelle=(
                    "heuristik" if raum.synergie(kandidat, mitspieler) is None
                    and raum.synergie_prior(kandidat, mitspieler) is None
                    else "daten" if quelle != quellen.PROFILE else "demo"
                ),
            ))

    if not werte:
        komp.verfuegbar = False
        komp.confidence = 0.0
        komp.quelle = quellen.UNKNOWN
        return komp
    komp.wert = klemme(sum(werte) / len(werte))
    komp.confidence = min(1.0, 0.5 + 0.25 * len(werte))
    komp.quelle = quellen.schwaechste(herkunft)
    return komp
