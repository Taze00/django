"""Die Schnittstellen.

Bewusst klein gehalten. Eine Schnittstelle, die alles kann, kann keine
Quelle erfuellen - und genau das ist hier absehbar: die offizielle API
wird Matches liefern, aber moeglicherweise keine Bans und keine Builds.
Eine Quelle, die nur zwei der drei Schnittstellen bedient, ist deshalb
der Normalfall und kein Sonderfall.
"""


class DataProvider:
    """Gemeinsames Verhalten aller Quellen."""

    name = "basis"
    ist_demo = False

    def verfuegbar(self):
        """Kann diese Quelle gerade etwas liefern?

        Fehlt der API-Key oder ist der Bestand leer, ist die Antwort
        False - und der Aufrufer nimmt die naechste Quelle, statt eine
        Ausnahme zu behandeln.
        """
        return True


class MatchDataProvider(DataProvider):
    """Einzelne gespielte Matches."""

    def matches(self, seit=None, limit=1000):
        raise NotImplementedError


class MetaDataProvider(DataProvider):
    """Aggregierte Werte: Staerke, Counter, Synergie."""

    def brawler_staerke(self, brawler, kontext):
        raise NotImplementedError

    def counter(self, brawler, gegner, kontext):
        raise NotImplementedError

    def synergie(self, a, b, kontext):
        raise NotImplementedError


class BuildDataProvider(DataProvider):
    """Ausruestung und ihre Bewaehrung.

    Ob die offizielle API Builds gespielter Matches ueberhaupt
    mitliefert, ist ungeprueft. Solange das offen ist, bleibt diese
    Schnittstelle bewusst allgemein - und der Drafter kommt ohne sie aus.
    """

    def builds(self, brawler, kontext):
        raise NotImplementedError
