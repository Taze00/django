# -*- coding: utf-8 -*-
"""Die Schnittstellen - zwei Rollen, streng getrennt.

    MatchProvider  liefert Rohmatches     -> nur fuer den IMPORT
    StatProvider   liefert Statistiken    -> nur fuer die ENGINE

Die Trennung ist die eigentliche Architekturentscheidung dieser Datei.
Die Engine sieht ausschliesslich voraggregierte Statistiken; Rohmatches
erreichen sie nie. Dazwischen liegen Import (Deduplizierung, Speichern)
und Aggregation (Zaehlen, Gewichten, Glaetten):

    MatchProvider -> Import -> Match-Tabellen -> Aggregation -> Stat-Tabellen
                                                                    |
                                                StatProvider -> Datenraum -> DraftEngine

Zwei Gruende, warum die Engine nie Rohmatches liest:
1. Geschwindigkeit. Eine Empfehlung hat rund 50 Millisekunden; eine
   Aggregation ueber hunderttausende Matches hat sie nicht.
2. Stabilitaet. Glaettung, Zeit- und Patchgewichtung sollen an EINER
   Stelle passieren. Liest die Engine Rohdaten, entsteht daneben eine
   zweite, abweichende Statistik.

Welcher Provider welche der geforderten Datenarten liefert:

    Datenart   Methode                    Rolle
    ---------  -------------------------  -------------
    Matches    MatchProvider.lieferungen   Import
    Meta       StatProvider.brawler_stats  Engine
    Counter    StatProvider.counter_stats  Engine
    Synergie   StatProvider.synergy_stats  Engine
    Builds     StatProvider.build_stats    Engine
"""


class DataProvider:
    """Gemeinsames Verhalten aller Provider."""

    name = "basis"

    def status(self):
        """Kann dieser Provider gerade liefern?

        Gibt einen `ProviderStatus` zurueck - nie eine Ausnahme. Fehlt der
        API-Key oder ist der Bestand leer, ist das ein Zustand mit Grund,
        kein Absturz.
        """
        from drafter.services.providers.records import ProviderStatus
        return ProviderStatus.bereit()

    @property
    def verfuegbar(self):
        return self.status().verfuegbar

    def __repr__(self):
        return f"<{type(self).__name__} {self.name}>"


class StatProvider(DataProvider):
    """Voraggregierte Statistiken. Das Einzige, was die Engine anfragt.

    Jede Methode bekommt eine `StatAnfrage` und gibt eine Liste von
    `StatRecord`s zurueck. Mehrere Zeilen je Brawler sind ausdruecklich
    erlaubt (Map, Modus, allgemein; verschiedene Zeitfenster) - welche
    davon passt, entscheidet der Datenraum.

    Eine leere Liste heisst "keine Auskunft", nicht "Wert 0". Die Engine
    faellt dann auf ihre Heuristiken zurueck und kennzeichnet das.
    """

    def brawler_stats(self, anfrage):
        raise NotImplementedError

    def counter_stats(self, anfrage):
        raise NotImplementedError

    def synergy_stats(self, anfrage):
        raise NotImplementedError

    def build_stats(self, anfrage):
        """Optional. Ohne Build-Daten laeuft die Build-Empfehlung auf Regeln."""
        return []


class MatchProvider(DataProvider):
    """Rohmatches fuer den Import.

    Liefert `Lieferung`en - eine je Datei oder API-Antwort - statt
    einzelner Matches. Grund: die Rohdaten werden gespeichert, bevor
    irgendetwas daraus gelesen wird, und sie gehoeren zu ihrer Lieferung,
    nicht zu einem einzelnen Match.
    """

    def lieferungen(self):
        raise NotImplementedError
