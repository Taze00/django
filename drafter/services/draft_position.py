"""Die Pick-Reihenfolge als eigene Bewertung.

Derselbe Brawler ist an verschiedenen Stellen des Drafts verschieden
viel wert. Ein Spezialist, der eine bestimmte Comp zerlegt, ist als
letzter Pick hervorragend und als Blind Pick ein Risiko - weil der
Gegner dann noch drei Picks hat, um ihn zu bestrafen.

Diese Komponente liest ausschliesslich die `draft_values` des Brawlers
(blind/early/last/counter/flexibility/counterability). Sie greift
bewusst **nicht** auf Eigenschaften zu: wie gut jemand kaempft, ist
Sache der anderen Komponenten. Hier geht es nur um Informationsstand.
"""

from drafter import config
from drafter.services.scoring import Grund, Komponente, klemme, zentriere

# Welcher Draftwert in welcher Phase zaehlt, und wie stark.
_PROFILE = {
    config.PHASE_FIRST_PICK: {"blind_pick_value": 0.65, "flexibility_value": 0.35},
    config.PHASE_EARLY: {"early_pick_value": 0.6, "flexibility_value": 0.25,
                         "blind_pick_value": 0.15},
    config.PHASE_MID: {"early_pick_value": 0.35, "counter_pick_value": 0.35,
                       "flexibility_value": 0.30},
    config.PHASE_LAST: {"last_pick_value": 0.6, "counter_pick_value": 0.4},
}


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
