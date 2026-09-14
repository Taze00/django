"""Wie sicher ist sich das System - und warum nicht sicherer.

Getrennt vom Score, weil es eine andere Frage beantwortet. Der Score
sagt "wie gut ist dieser Pick", die Confidence sagt "wie gut wissen wir
das". Beide Zahlen zusammen sind ehrlich; der Score allein waere eine
Behauptung.

Einfluesse:
- Stichprobengroesse der beteiligten Statistiken
- Datenquelle (Demo-Schaetzung vs. gemessene Daten)
- wie viel vom Draft ueberhaupt bekannt ist
- wie stark die beteiligten Brawler zuletzt veraendert wurden
"""

from drafter import config

# Mehr als das ist mit reinen Demo-Daten nicht zu rechtfertigen. Der
# Deckel ist der Grund, warum die Oberflaeche im MVP nie "Hoch" anzeigt.
DEMO_DECKEL = 0.35


def stichproben_confidence(spiele):
    """0-1 aus der Anzahl Spiele, mit abflachendem Zuwachs.

    Wurzelfoermig statt linear: der Sprung von 50 auf 500 Spiele ist ein
    echter Erkenntnisgewinn, der von 5000 auf 5500 kaum noch einer.
    """
    if spiele <= 0:
        return 0.0
    return min(1.0, (spiele / config.CONFIDENCE_VOLL_AB) ** 0.5)


def label(wert):
    for grenze, text in config.CONFIDENCE_STUFEN:
        if wert >= grenze:
            return text
    return config.CONFIDENCE_STUFEN[-1][1]


def fuer_empfehlung(komponenten, ctx, raum):
    """Gesamtconfidence einer Empfehlung, 0-1.

    Gewichtet die Confidence jeder Komponente mit deren Gewicht - eine
    unsichere Nebenkomponente soll das Gesamturteil nicht so stark
    trueben wie eine unsichere Hauptkomponente.
    """
    gewicht_summe = 0.0
    gewichtet = 0.0
    for komp in komponenten.values():
        g = abs(komp.gewicht)
        if g <= 0:
            continue
        gewicht_summe += g
        gewichtet += g * komp.confidence
    basis = gewichtet / gewicht_summe if gewicht_summe else 0.3

    # Bekannter Draftstand: je mehr feststeht, desto belastbarer die Aussage.
    bekannt = (ctx.picks_gesamt + len(ctx.bans) * 0.3) / 7.8
    basis = basis * (0.75 + 0.25 * min(1.0, bekannt))

    if raum.nur_demo:
        basis = min(basis, DEMO_DECKEL)
    return max(0.0, min(1.0, basis))


def erklaerung(wert, raum, ctx):
    """Ein Satz, der die Confidence begruendet - nie nur eine Zahl."""
    if raum.nur_demo:
        return (
            "Demo-Daten: die Werte sind gepflegte Einschätzungen, keine "
            "gemessenen Statistiken."
        )
    if wert < 0.45:
        return "Wenig belastbare Matchdaten für diese Map und diesen Patch."
    if ctx.picks_gesamt < 2:
        return "Noch wenig vom Draft bekannt - die Aussage wird mit jedem Pick sicherer."
    return "Ausreichend Daten für diese Map, diesen Modus und den aktuellen Patch."
