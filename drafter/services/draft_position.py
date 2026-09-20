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
    """(Streuung, Partien, Modi) seiner Modus-Eignung - oder None.

    **Was hier gemessen wird:** wie stark seine Siegquote zwischen den
    Modi auseinandergeht. Wenig Streuung heisst "laeuft ueberall aehnlich"
    und damit flexibel; viel Streuung heisst spezialisiert.

    Zwei Fallen, beide entschaerft:

    1. **Datenarmut sieht aus wie Flexibilitaet.** Wer in jedem Modus drei
       Partien hat, liegt ueberall beim Prior - die Streuung ist dann fast
       null, und er saehe maximal flexibel aus. Deshalb zwei Dinge: je
       Modus wird der geschrumpfte Posterior verwendet (nicht die rohe
       Rate), und die AUSSAGEKRAFT wandert als Evidenzgewicht nach
       draussen, wo sie ueber das Profil entscheidet.
    2. **Ein einzelner Ausreisser.** Jede Modus-Rate zaehlt mit ihrer
       Partienzahl, nicht gleich viel.

    Unter zwei Modi gibt es nichts zu vergleichen - dann None.
    """
    from drafter.services import staerke
    raten, gewichte = [], []
    global_zeile = raum.ebenen(kandidat).get(staerke.GLOBAL)
    global_rate = 0.5
    if global_zeile is not None and (global_zeile.games or 0) > 0:
        n_g = float(global_zeile.games)
        s_g = float(global_zeile.wins or 0) or n_g * (
            global_zeile.raw_rate if global_zeile.raw_rate is not None
            else (global_zeile.adjusted_rate or 0.5))
        global_rate, _ = staerke.posterior(n_g, s_g)

    for zeile in raum.modus_zeilen(kandidat):
        n = float(zeile.games or 0)
        if n <= 0:
            continue
        siege = float(zeile.wins or 0)
        if not siege:
            rate = zeile.raw_rate if zeile.raw_rate is not None else zeile.adjusted_rate
            if rate is None:
                continue
            siege = n * rate
        # Der globale Wert ist der Prior: ein duenner Modus landet dort
        # und traegt dann zur Streuung nichts bei - richtig so, er sagt
        # ja auch nichts.
        posterior, _ = staerke.posterior(n, siege, prior_rate=global_rate,
                                         prior_staerke=config.STAERKE_PRIOR_GLOBAL)
        raten.append(posterior)
        gewichte.append(n)
    if len(raten) < 2:
        return None
    gesamt = sum(gewichte)
    mittel = sum(r * g for r, g in zip(raten, gewichte)) / gesamt
    varianz = sum(g * (r - mittel) ** 2 for r, g in zip(raten, gewichte)) / gesamt
    return varianz ** 0.5, gesamt, len(raten)


def prior_verlaesslichkeit(brawler):
    """Wie sehr darf ein gepflegter Wert dieses Brawlers behaupten? (0-1)

    Haengt an der Herkunft des Profils, nicht am Brawler: ein Demo-Seed
    ist ein Anhaltspunkt, ein von Hand gepflegtes Profil eine gepruefte
    Aussage. Siehe config.PRIOR_VERLAESSLICHKEIT.
    """
    quelle = getattr(brawler, "source", "") or ""
    return config.PRIOR_VERLAESSLICHKEIT.get(
        quelle, config.PRIOR_VERLAESSLICHKEIT_UNBEKANNT)


def evidenzgewicht(menge, k, modi=None):
    """0-1: wie sehr die Messung den Profil-Prior verdraengen darf.

    Stetig, ohne Schwelle - dieselbe Form wie im Objective Fit. `modi`
    daempft zusaetzlich, wenn die Streuung ueber sehr wenige Gruppen
    gerechnet wurde: zwei Modi sagen weniger als sechs.
    """
    if menge <= 0:
        return 0.0
    w = menge / (menge + k)
    if modi:
        w *= (modi - 1) / modi
    return max(0.0, min(1.0, w))


def _felder(kandidaten, raum, roh_profil, roh_messung):
    """Beide Stufen je in ihrem eigenen Feld zentrieren.

    Getrennte Felder, beide bei 0: so ist der Besitz eines Profils eine
    Information ueber den Brawler und kein Vorsprung gegenueber allen,
    die keines haben.
    """
    return z_werte(roh_profil), z_werte(roh_messung)


def gepflegter_draftwert(brawler, key):
    """Ein gepflegter Draftwert - **nur wenn er belastbar ist**.

    Alle sechs Draftwerte stammen aus der Demo-Handarbeit vom
    2026-09-14. Sie sagen ueber die heutige Meta nichts, und weil nur
    zwanzig von 106 Brawlern sie haben, bevorzugten sie genau diese
    zwanzig bei Flexibilitaet und Draft-Position. Gemessene Ableitungen
    fuer beides gibt es inzwischen (`modusbreite`,
    `gegnerabhaengigkeit`) - die haben Vorrang, und wo sie fehlen, ist
    die Antwort Unknown statt einer Handzahl.

    Die Werte bleiben in der Datenbank lesbar; nur ins Scoring gehen sie
    nicht mehr. Wird spaeter eine belastbare Quelle gepflegt (`source`
    ungleich demo), traegt sie hier wieder.
    """
    from drafter.models.base import Datenquelle

    if brawler.source == Datenquelle.DEMO:
        return None
    return brawler.draftwert(key)


def komponenten_fuer_pool(kandidaten, ctx, raum):
    """Draft-Position fuer alle Kandidaten - Messung mischt sich mit dem Profil."""
    phase = ctx.phase
    anteile = _PROFILE.get(phase, _PROFILE[config.PHASE_MID])
    # Frueher Pick: Berechenbarkeit ist gut. Spaeter Pick: gerade die
    # Abhaengigkeit vom Gegner ist der Wert, weil man ihn jetzt kennt.
    richtung = -1.0 if ctx.gegner_restpicks > 0 else 1.0

    roh_profil, roh_messung, belege = {}, {}, {}
    for b in kandidaten:
        werte = {key: gepflegter_draftwert(b, key) for key in anteile}
        if all(v is not None for v in werte.values()):
            roh_profil[b.id] = sum(werte[key] * anteil
                                   for key, anteil in anteile.items())
        lage = gegnerabhaengigkeit(b, raum)
        if lage is not None:
            streuung, n, paare = lage
            roh_messung[b.id] = richtung * streuung
            belege[b.id] = (streuung, n, paare)
    z_profil, z_messung = _felder(kandidaten, raum, roh_profil, roh_messung)

    ergebnis = {}
    for b in kandidaten:
        komp = Komponente(key=config.K_DRAFT_POSITION)
        prior = z_profil.get(b.id)
        gemessen = z_messung.get(b.id)
        if prior is None and gemessen is None:
            komp.verfuegbar = False
            ergebnis[b.id] = komp
            continue
        w = 0.0
        if gemessen is not None:
            _, n, paare = belege[b.id]
            w = evidenzgewicht(n, config.DRAFTLAGE_EVIDENZ_K)
        zuverlaessig = prior_verlaesslichkeit(b) if prior is not None else 0.0
        komp.wert = klemme(w * (gemessen or 0.0)
                           + (1.0 - w) * (prior or 0.0) * zuverlaessig)
        komp.mess_anteil = w
        komp.prior_verlaesslichkeit = zuverlaessig if prior is not None else None
        komp.quelle = _quelle(w, prior is not None)
        if gemessen is not None and w > 0.3 and abs(komp.wert) > 0.3:
            _, n, paare = belege[b.id]
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
        elif prior is not None and w <= 0.5:
            _profiltexte(komp, b, ctx, phase)
        ergebnis[b.id] = komp
    return ergebnis


def _quelle(w, hat_prior):
    """Wie die Mischung heisst - damit man sie im Debug-Output sieht."""
    if w >= 0.8:
        return quellen.MEASURED
    if w > 0.0:
        return quellen.MEASURED_PRIOR
    return quellen.PROFIL_PRIOR if hat_prior else quellen.UNKNOWN


def flexibilitaet_fuer_pool(kandidaten, ctx, raum):
    """Flexibilitaet fuer alle Kandidaten - Messung mischt sich mit dem Profil."""
    roh_profil, roh_messung, belege = {}, {}, {}
    for b in kandidaten:
        flex = gepflegter_draftwert(b, "flexibility_value")
        if flex is not None:
            roh_profil[b.id] = flex
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
        prior = z_profil.get(b.id)
        gemessen = z_messung.get(b.id)
        if prior is None and gemessen is None:
            komp.verfuegbar = False
            ergebnis[b.id] = komp
            continue
        w = 0.0
        if gemessen is not None:
            _, n, modi = belege[b.id]
            w = evidenzgewicht(n, config.FLEX_EVIDENZ_K, modi=modi)
        zuverlaessig = prior_verlaesslichkeit(b) if prior is not None else 0.0
        komp.wert = klemme(w * (gemessen or 0.0)
                           + (1.0 - w) * (prior or 0.0) * zuverlaessig)
        komp.mess_anteil = w
        komp.prior_verlaesslichkeit = zuverlaessig if prior is not None else None
        komp.quelle = _quelle(w, prior is not None)
        if gemessen is not None and w > 0.3 and komp.wert > 0.35:
            _, _, modi = belege[b.id]
            komp.gruende.append(Grund(
                text=f"läuft über {modi} Modi hinweg ähnlich - legt uns wenig fest",
                positiv=True, staerke=0.4, quelle="daten",
            ))
        elif komp.wert > 0.35 and ctx.unsere_restpicks > 1:
            komp.gruende.append(Grund(
                text="flexibel - legt unsere restlichen Picks nicht fest",
                positiv=True, staerke=0.45,
            ))
        ergebnis[b.id] = komp
    return ergebnis


def _profiltexte(komp, kandidat, ctx, phase):
    """Die gepflegten Saetze zur Draft-Position.

    Sie zitieren die Demo-Draftwerte und erscheinen deshalb nur noch,
    wo eine belastbare Quelle sie traegt - sonst gar nicht. Ein Satz,
    der sich auf eine Zahl beruft, die nicht mehr ins Scoring eingeht,
    waere eine Begruendung fuer etwas, das gar nicht passiert ist.
    """
    hole = lambda key: gepflegter_draftwert(kandidat, key)
    if all(hole(k) is None for k in
           ("counterability", "blind_pick_value", "counter_pick_value")):
        return
    offen = ctx.gegner_restpicks
    if offen > 0:
        konterbar = (hole("counterability") or 0.0)
        if konterbar >= 0.65:
            komp.gruende.append(Grund(
                text=f"leicht zu kontern, und der Gegner hat noch {offen} Pick(s)",
                positiv=False, staerke=0.45 + konterbar * 0.2,
            ))
    if phase == config.PHASE_FIRST_PICK and (hole("blind_pick_value") or 0.0) >= 0.7:
        komp.gruende.append(Grund(
            text="sicherer Blind Pick - schwer gezielt zu bestrafen",
            positiv=True, staerke=0.7,
        ))
    elif phase == config.PHASE_LAST and (hole("counter_pick_value") or 0.0) >= 0.7:
        komp.gruende.append(Grund(
            text="typischer Last Pick: bestraft gezielt, was schon steht",
            positiv=True, staerke=0.75,
        ))
    elif phase == config.PHASE_FIRST_PICK and (hole("blind_pick_value") or 0.0) <= 0.35:
        komp.gruende.append(Grund(
            text="als erster Pick riskant - der Gegner kann darauf antworten",
            positiv=False, staerke=0.6,
        ))


def komponente(kandidat, ctx):
    """Draft-Position aus GEPFLEGTEN Werten - ohne sie: nicht verfuegbar.

    Liefert immer eine Komponente, nie None: eine fehlende Auskunft ist
    `verfuegbar=False`, kein fehlendes Objekt. Der Aufrufer soll nicht
    zwischen "weiss nichts" und "gibt es nicht" unterscheiden muessen.
    """
    phase = ctx.phase
    komp = Komponente(key=config.K_DRAFT_POSITION)
    hole = lambda key: gepflegter_draftwert(kandidat, key)

    anteile = _PROFILE.get(phase, _PROFILE[config.PHASE_MID])
    werte = {key: hole(key) for key in anteile}
    if any(v is None for v in werte.values()):
        # Seit dem 2026-09-20: die Demo-Draftwerte zaehlen nicht mehr,
        # und ohne belastbare Quelle waere jeder Wert eine Annahme.
        komp.verfuegbar = False
        return komp
    roh = sum(werte[key] * anteil for key, anteil in anteile.items())
    wert = zentriere(roh)

    # Konterbarkeit: gefaehrlich nur, solange der Gegner noch waehlen darf.
    # Beim letzten Pick des Drafts ist sie voellig belanglos - niemand
    # kann mehr reagieren. Genau das unterscheidet Last Pick von First Pick.
    offen = ctx.gegner_restpicks
    if offen > 0:
        konterbar = (hole("counterability") or 0.0)
        strafe = (konterbar - 0.5) * 0.5 * (offen / 3.0)
        wert -= strafe
        if strafe > 0.12:
            komp.gruende.append(Grund(
                text=f"leicht zu kontern, und der Gegner hat noch {offen} Pick(s)",
                positiv=False, staerke=0.45 + strafe,
            ))

    komp.wert = klemme(wert)

    if phase == config.PHASE_FIRST_PICK and (hole("blind_pick_value") or 0.0) >= 0.7:
        komp.gruende.append(Grund(
            text="sicherer Blind Pick - schwer gezielt zu bestrafen",
            positiv=True, staerke=0.7,
        ))
    elif phase == config.PHASE_LAST and (hole("counter_pick_value") or 0.0) >= 0.7:
        komp.gruende.append(Grund(
            text="typischer Last Pick: bestraft gezielt, was schon steht",
            positiv=True, staerke=0.75,
        ))
    elif phase == config.PHASE_FIRST_PICK and (hole("blind_pick_value") or 0.0) <= 0.35:
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
    flex = gepflegter_draftwert(kandidat, "flexibility_value")
    if flex is None:
        komp.verfuegbar = False
        return komp
    komp.wert = zentriere(flex)
    if komp.wert > 0.35 and ctx.unsere_restpicks > 1:
        komp.gruende.append(Grund(
            text="flexibel - legt unsere restlichen Picks nicht fest",
            positiv=True, staerke=0.45,
        ))
    return komp
