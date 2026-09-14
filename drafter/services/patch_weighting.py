"""Wie viel eine Statistik nach Patches und Zeit noch wert ist.

Zwei unabhaengige Abschlaege, multipliziert:

    gewicht = zeit_gewicht * patch_gewicht

**Zeit**: exponentieller Zerfall mit Halbwertszeit. Daten von gestern
zaehlen voll, Daten von vor vier Wochen ein Viertel.

**Patch**: haengt daran, wie stark der Brawler seit der Messung
veraendert wurde. Ein Rework macht alte Zahlen praktisch wertlos, ein
kleiner Nerf kaum.

Nicht abgebildet ist der *indirekte* Effekt (Tanks werden gebufft, also
wird Anti-Tank besser, ohne dass Anti-Tank veraendert wurde). Das
braucht Matchdaten und gehoert in den spaeteren Aggregator - hier waere
es geraten.
"""

import math
from datetime import date

from drafter import config


def zeit_gewicht(bis_datum, heute=None):
    """Exponentieller Zerfall nach Alter der Daten."""
    if not bis_datum:
        return 1.0
    heute = heute or date.today()
    alter = max(0, (heute - bis_datum).days)
    return 0.5 ** (alter / config.ZEIT_HALBWERTSZEIT_TAGE)


def patch_gewicht(brawler, seit_patch, bis_patch=None):
    """Wie sehr Balanceaenderungen die alten Zahlen entwerten.

    Betrachtet alle Aenderungen an diesem Brawler nach dem Patch, aus
    dem die Daten stammen. Mehrere Aenderungen multiplizieren sich -
    zwei mittlere Anpassungen hintereinander lassen von den alten Daten
    zu Recht wenig uebrig.
    """
    if seit_patch is None:
        return 1.0

    aenderungen = brawler.balance_changes.all()
    gewicht = 1.0
    for aenderung in aenderungen:
        if aenderung.patch_id == seit_patch.id:
            continue
        if aenderung.patch.released_on <= seit_patch.released_on:
            continue
        if bis_patch and aenderung.patch.released_on > bis_patch.released_on:
            continue
        gewicht *= config.PATCH_GEWICHT.get(aenderung.severity, 0.5)
    return gewicht


def statistik_gewicht(stat, brawler, aktueller_patch=None):
    """Gesamtgewicht einer Statistikzeile fuer den heutigen Draft."""
    g = zeit_gewicht(stat.window_end)
    if stat.patch_id and aktueller_patch:
        g *= patch_gewicht(brawler, stat.patch, aktueller_patch)
    # Ohne Zeitfenster (gepflegte Demo-Daten) faellt der Zeitabschlag weg -
    # sonst wuerde jede handgepflegte Zahl grundlos abgewertet.
    return max(0.05, min(1.0, g))


def bayes(spiele, siege, prior_rate=None, prior_staerke=None):
    """Winrate mit Prior glaetten.

    62 % aus 20 Spielen ist keine 62-%-Winrate - es sind 12 von 20. Der
    Prior zieht solche Werte zur Mitte, waehrend grosse Stichproben ihn
    einfach ueberstimmen. Genau das verhindert, dass ein Zufallstreffer
    an die Spitze der Empfehlungen rutscht.
    """
    prior_rate = config.PRIOR_RATE if prior_rate is None else prior_rate
    prior_staerke = config.PRIOR_STAERKE if prior_staerke is None else prior_staerke
    if spiele <= 0:
        return prior_rate
    return (siege + prior_staerke * prior_rate) / (spiele + prior_staerke)
