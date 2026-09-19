# -*- coding: utf-8 -*-
"""Einen Brawler aus einer Eingabe finden - an einer Stelle.

Die Web-App bekommt Slugs aus ihrem eigenen Katalog und braucht nichts
weiter. Ein Mensch auf der Kommandozeile tippt, was er sieht: "WILLOW",
"Larry & Lawrie", "R-T", "Mr. P". Dieselbe kanonische Identitaet, die
der Import benutzt (`katalog_schluessel`), loest all das auf - sie
trennt camelCase, normalisiert Zeichen und macht daraus den Slug.

**Keine unscharfe Suche.** Wenn eine Eingabe auf mehrere Brawler passen
koennte, wird gemeldet statt geraten - dieselbe Regel wie im Import und
bei den Portraits. Ein falsch zugeordneter Brawler in einem Protokoll
ist schlimmer als eine Fehlermeldung.
"""

from drafter.models import Brawler
from drafter.services.ingest.fingerprint import katalog_schluessel


class Mehrdeutig(ValueError):
    """Mehrere Brawler passen - der Aufrufer muss genauer werden."""

    def __init__(self, eingabe, treffer):
        self.eingabe = eingabe
        self.treffer = list(treffer)
        namen = ", ".join(f"{b.name} ({b.slug})" for b in self.treffer)
        super().__init__(f"'{eingabe}' ist mehrdeutig: {namen}")


def finde_brawler(eingabe, menge=None):
    """Brawler zu Name, Slug oder externer ID - oder None.

    Reihenfolge: externe ID, dann Slug, dann der kanonische Schluessel
    des Namens. Die ID steht vorn, weil sie die einzige stabile Kennung
    ist; Namen aendern Schreibweise, Slugs koennen kollidieren.
    """
    roh = str(eingabe or "").strip()
    if not roh:
        return None
    alle = menge if menge is not None else Brawler.objects.all()

    if roh.isdigit():
        treffer = list(alle.filter(external_id=roh))
        if len(treffer) == 1:
            return treffer[0]
        if treffer:
            raise Mehrdeutig(eingabe, treffer)

    schluessel = katalog_schluessel(roh)
    for abfrage in (alle.filter(slug=roh.lower()),
                    alle.filter(slug=schluessel),
                    alle.filter(name__iexact=roh)):
        treffer = list(abfrage)
        if len(treffer) == 1:
            return treffer[0]
        if len(treffer) > 1:
            raise Mehrdeutig(eingabe, treffer)

    # Letzter Schritt: der kanonische Schluessel auf beiden Seiten. Faengt
    # "Larry & Lawrie" -> larry-lawrie und "Mr. P" -> mr-p.
    treffer = [b for b in alle if katalog_schluessel(b.name) == schluessel]
    if len(treffer) == 1:
        return treffer[0]
    if len(treffer) > 1:
        raise Mehrdeutig(eingabe, treffer)
    return None


def finde_alle(eingaben, menge=None):
    """(gefundene Brawler, nicht auffindbare Eingaben)."""
    gefunden, fehlend = [], []
    for eingabe in eingaben:
        b = finde_brawler(eingabe, menge)
        (gefunden if b is not None else fehlend).append(b if b is not None else eingabe)
    return gefunden, fehlend
