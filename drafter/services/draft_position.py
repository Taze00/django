"""Die Pick-Reihenfolge als eigene Bewertung.

Derselbe Brawler ist an verschiedenen Stellen des Drafts verschieden
viel wert. Ein Spezialist, der eine bestimmte Comp zerlegt, ist als
letzter Pick hervorragend und als Blind Pick ein Risiko - weil der
Gegner dann noch drei Picks hat, um ihn zu bestrafen.

Die Komponente greift bewusst **nicht** auf Kampf-Eigenschaften zu: wie
gut jemand kaempft, ist Sache der anderen Komponenten. Hier geht es nur
um Informationsstand.

**Zwei Quellen, seit dem 2026-09-19.** Bis dahin las sie ausschliesslich
die gepflegten `draft_values` - und die hatten nur 20 von 106 Brawlern.
Draft-Position (Gewicht 0.09) und Flexibilitaet (0.14) waren damit fuer
86 Brawler dauerhaft nicht erreichbar: zusammen 23 % des
Bewertungsgewichts, das an der Existenz eines Demo-Profils hing.

    1. gepflegte `draft_values`      (direkte Aussage zur Frage)
    2. gemessene Ableitung           (Proxy, siehe unten)
    3. Unknown                       (neutral, kein Ersatz)

Die **Fachquelle fehlt in dieser Kette mit Absicht**: Rolle und
Faehigkeiten sagen nichts darueber, ob jemand einen guten Blind Pick
abgibt. Eine Tabelle "Rolle -> blind_pick_value" waere genau der Fehler,
den der Rollen-Audit bei `thrower -> objective_damage` gefunden hat.

**Die gemessene Ableitung.** Wie sehr haengt sein Ergebnis am Gegner?
Aus den gemessenen Countern laesst sich das direkt ablesen: die Streuung
seiner Matchup-Vorteile ueber alle Gegner, gewichtet mit der Stichprobe
des jeweiligen Paares. Das ist keine Analogie zum Blind Pick, sondern
seine Definition - wer stark vom Gegner abhaengt, ist blind riskant und
als letzter Pick wertvoll, weil man ihn dann gezielt setzen kann. Das
Vorzeichen dreht deshalb mit der Phase, der Betrag bleibt derselbe.

Fuer die Flexibilitaet gilt dasselbe eine Ebene hoeher: die Streuung
seiner MODUS-Eignungen sagt, wie sehr ein Pick uns auf einen Modus
festlegt. Beides aus vorhandenen Messungen, kein erfundener Wert.

**Beide Stufen werden im eigenen Feld zentriert.** Vorher rechnete die
Komponente absolut (`zentriere(draftwert)`), und weil gepflegte Profile
ueberdurchschnittliche Draftwerte tragen, war der blosse Besitz eines
Profils ein Bonus. Jetzt ist er eine Information: gemessen wird die Lage
im jeweiligen Feld, beide Felder liegen bei 0.
"""

from statistics import fmean

from drafter import config
from drafter.services import quellen
from drafter.services.scoring import Grund, Komponente, klemme, z_werte, zentriere

# Welcher Draftwert in welcher Phase zaehlt, und wie stark.
_PROFILE = {
    config.PHASE_FIRST_PICK: {"blind_pick_value": 0.65, "flexibility_value": 0.35},
    config.PHASE_EARLY: {"early_pick_value": 0.6, "flexibility_value": 0.25,
                         "blind_pick_value": 0.15},
    config.PHASE_MID: {"early_pick_value": 0.35, "counter_pick_value": 0.35,
                       "flexibility_value": 0.30},
    config.PHASE_LAST: {"last_pick_value": 0.6, "counter_pick_value": 0.4},
}


def gegnerabhaengigkeit(kandidat, raum):
    """Wie sehr haengt sein Ergebnis am Gegner? (0-1) oder None.

    Gewichtete Streuung seiner gemessenen Matchup-Vorteile. Jedes Paar
    zaehlt mit seiner eigenen Stichprobe; wer zu wenige gemessene
    Matchups hat, bekommt keine Auskunft statt einer geratenen.
    """
    werte, gewichte = [], []
    for gegner in raum.brawler:
        if gegner.id == kandidat.id:
            continue
        zeile = raum.counter(kandidat, gegner) or raum.counter(gegner, kandidat)
        if zeile is None or not zeile.ist_gemessen:
            continue
        n = float(zeile.sample_size or zeile.games or 0)
        if n <= 0:
            continue
        wert = zeile.advantage
        if raum.counter(kandidat, gegner) is None:
            wert = -wert          # Gegenrichtung ist das Negativ
        werte.append(wert)
        gewichte.append(n)
    gesamt = sum(gewichte)
    if len(werte) < config.DRAFTLAGE_MIN_PAARE or gesamt <= 0:
        return None
    mittel = sum(w * g for w, g in zip(werte, gewichte)) / gesamt
    varianz = sum(g * (w - mittel) ** 2 for w, g in zip(werte, gewichte)) / gesamt
    return varianz ** 0.5, gesamt, len(werte)


def modusbreite(kandidat, raum):
    """Wie gleichmaessig laeuft er ueber die Modi? (Streuung) oder None.

    Aus den gemessenen Modus-Zeilen: wer ueberall aehnlich abschneidet,
    legt uns nicht fest. Braucht mindestens zwei Modi mit Messung, sonst
    gibt es nichts zu vergleichen.
    """
    raten, gewichte = [], []
    for zeile in raum.modus_zeilen(kandidat):
        n = float(zeile.games or 0)
        rate = zeile.raw_rate if zeile.raw_rate is not None else zeile.adjusted_rate
        if n < config.DRAFTLAGE_MIN_MODUS_PARTIEN or rate is None:
            continue
        raten.append(rate)
        gewichte.append(n)
    if len(raten) < 2:
        return None
    gesamt = sum(gewichte)
    mittel = sum(r * g for r, g in zip(raten, gewichte)) / gesamt
    varianz = sum(g * (r - mittel) ** 2 for r, g in zip(raten, gewichte)) / gesamt
    return varianz ** 0.5, gesamt, len(raten)


def _felder(kandidaten, raum, roh_profil, roh_messung):
    """Beide Stufen je in ihrem eigenen Feld zentrieren.

    Getrennte Felder, beide bei 0: so ist der Besitz eines Profils eine
    Information ueber den Brawler und kein Vorsprung gegenueber allen,
    die keines haben.
    """
    return z_werte(roh_profil), z_werte(roh_messung)


def komponenten_fuer_pool(kandidaten, ctx, raum):
    """Draft-Position fuer alle Kandidaten - feldrelativ, zwei Quellen."""
    phase = ctx.phase
    anteile = _PROFILE.get(phase, _PROFILE[config.PHASE_MID])
    # Frueher Pick: Berechenbarkeit ist gut. Spaeter Pick: gerade die
    # Abhaengigkeit vom Gegner ist der Wert, weil man ihn jetzt kennt.
    richtung = -1.0 if ctx.gegner_restpicks > 0 else 1.0

    roh_profil, roh_messung, belege = {}, {}, {}
    for b in kandidaten:
        if b.hat_draftwerte:
            roh_profil[b.id] = sum(b.draftwert(key) * anteil
                                   for key, anteil in anteile.items())
            continue
        lage = gegnerabhaengigkeit(b, raum)
        if lage is not None:
            streuung, n, paare = lage
            roh_messung[b.id] = richtung * streuung
            belege[b.id] = (streuung, n, paare)
    z_profil, z_messung = _felder(kandidaten, raum, roh_profil, roh_messung)

    ergebnis = {}
    for b in kandidaten:
        komp = Komponente(key=config.K_DRAFT_POSITION)
        if b.id in z_profil:
            komp.wert = klemme(z_profil[b.id])
            komp.quelle = quellen.PROFILE
            _profiltexte(komp, b, ctx, phase)
        elif b.id in z_messung:
            komp.wert = klemme(z_messung[b.id])
            komp.quelle = quellen.MEASURED_PRIOR
            streuung, n, paare = belege[b.id]
            if abs(komp.wert) > 0.3:
                offen = ctx.gegner_restpicks
                komp.gruende.append(Grund(
                    text=(f"sein Ergebnis hängt stark vom Gegner ab "
                          f"({paare} gemessene Matchups)"
                          + (f" - und der Gegner hat noch {offen} Pick(s)"
                             if offen and komp.wert < 0 else
                             " - jetzt lässt er sich gezielt setzen")),
                    positiv=komp.wert > 0, staerke=0.4 + abs(komp.wert) * 0.2,
                    quelle="daten",
                ))
        else:
            komp.verfuegbar = False
        ergebnis[b.id] = komp
    return ergebnis


def flexibilitaet_fuer_pool(kandidaten, ctx, raum):
    """Flexibilitaet fuer alle Kandidaten - feldrelativ, zwei Quellen."""
    roh_profil, roh_messung, belege = {}, {}, {}
    for b in kandidaten:
        if b.hat_draftwerte:
            roh_profil[b.id] = b.draftwert("flexibility_value")
            continue
        breite = modusbreite(b, raum)
        if breite is not None:
            streuung, n, modi = breite
            # Kleine Streuung ueber die Modi = flexibel.
            roh_messung[b.id] = -streuung
            belege[b.id] = (streuung, n, modi)
    z_profil, z_messung = _felder(kandidaten, raum, roh_profil, roh_messung)

    ergebnis = {}
    for b in kandidaten:
        komp = Komponente(key=config.K_FLEXIBILITY)
        if b.id in z_profil:
            komp.wert = klemme(z_profil[b.id])
            komp.quelle = quellen.PROFILE
        elif b.id in z_messung:
            komp.wert = klemme(z_messung[b.id])
            komp.quelle = quellen.MEASURED_PRIOR
            if komp.wert > 0.35:
                _, _, modi = belege[b.id]
                komp.gruende.append(Grund(
                    text=f"läuft über {modi} Modi hinweg ähnlich - legt uns wenig fest",
                    positiv=True, staerke=0.4, quelle="daten",
                ))
        else:
            komp.verfuegbar = False
            ergebnis[b.id] = komp
            continue
        if komp.wert > 0.35 and ctx.unsere_restpicks > 1 and not komp.gruende:
            komp.gruende.append(Grund(
                text="flexibel - legt unsere restlichen Picks nicht fest",
                positiv=True, staerke=0.45,
            ))
        ergebnis[b.id] = komp
    return ergebnis


def _profiltexte(komp, kandidat, ctx, phase):
    """Die gepflegten Saetze zur Draft-Position - unveraendert."""
    offen = ctx.gegner_restpicks
    if offen > 0:
        konterbar = kandidat.draftwert("counterability")
        if konterbar >= 0.65:
            komp.gruende.append(Grund(
                text=f"leicht zu kontern, und der Gegner hat noch {offen} Pick(s)",
                positiv=False, staerke=0.45 + konterbar * 0.2,
            ))
    if phase == config.PHASE_FIRST_PICK and kandidat.draftwert("blind_pick_value") >= 0.7:
        komp.gruende.append(Grund(
            text="sicherer Blind Pick - schwer gezielt zu bestrafen",
            positiv=True, staerke=0.7,
        ))
    elif phase == config.PHASE_LAST and kandidat.draftwert("counter_pick_value") >= 0.7:
        komp.gruende.append(Grund(
            text="typischer Last Pick: bestraft gezielt, was schon steht",
            positiv=True, staerke=0.75,
        ))
    elif phase == config.PHASE_FIRST_PICK and kandidat.draftwert("blind_pick_value") <= 0.35:
        komp.gruende.append(Grund(
            text="als erster Pick riskant - der Gegner kann darauf antworten",
            positiv=False, staerke=0.6,
        ))


def komponente(kandidat, ctx):
    phase = ctx.phase
    komp = Komponente(key=config.K_DRAFT_POSITION)
    if not kandidat.hat_draftwerte:
        # Ohne gepflegte Draft-Werte waere jeder Wert der Default 0.5 -
        # eine Annahme, keine Auskunft.
        komp.verfuegbar = False
        return komp

    anteile = _PROFILE.get(phase, _PROFILE[config.PHASE_MID])
    roh = sum(kandidat.draftwert(key) * anteil for key, anteil in anteile.items())
    wert = zentriere(roh)

    # Konterbarkeit: gefaehrlich nur, solange der Gegner noch waehlen darf.
    # Beim letzten Pick des Drafts ist sie voellig belanglos - niemand
    # kann mehr reagieren. Genau das unterscheidet Last Pick von First Pick.
    offen = ctx.gegner_restpicks
    if offen > 0:
        konterbar = kandidat.draftwert("counterability")
        strafe = (konterbar - 0.5) * 0.5 * (offen / 3.0)
        wert -= strafe
        if strafe > 0.12:
            komp.gruende.append(Grund(
                text=f"leicht zu kontern, und der Gegner hat noch {offen} Pick(s)",
                positiv=False, staerke=0.45 + strafe,
            ))

    komp.wert = klemme(wert)

    if phase == config.PHASE_FIRST_PICK and kandidat.draftwert("blind_pick_value") >= 0.7:
        komp.gruende.append(Grund(
            text="sicherer Blind Pick - schwer gezielt zu bestrafen",
            positiv=True, staerke=0.7,
        ))
    elif phase == config.PHASE_LAST and kandidat.draftwert("counter_pick_value") >= 0.7:
        komp.gruende.append(Grund(
            text="typischer Last Pick: bestraft gezielt, was schon steht",
            positiv=True, staerke=0.75,
        ))
    elif phase == config.PHASE_FIRST_PICK and kandidat.draftwert("blind_pick_value") <= 0.35:
        komp.gruende.append(Grund(
            text="als erster Pick riskant - der Gegner kann darauf antworten",
            positiv=False, staerke=0.6,
        ))
    return komp


def flexibilitaet(kandidat, ctx):
    """Eigene kleine Komponente: wie sehr haelt er uns Optionen offen."""
    komp = Komponente(key=config.K_FLEXIBILITY)
    if not kandidat.hat_draftwerte:
        komp.verfuegbar = False
        return komp
    komp.wert = zentriere(kandidat.draftwert("flexibility_value"))
    if komp.wert > 0.35 and ctx.unsere_restpicks > 1:
        komp.gruende.append(Grund(
            text="flexibel - legt unsere restlichen Picks nicht fest",
            positiv=True, staerke=0.45,
        ))
    return komp
