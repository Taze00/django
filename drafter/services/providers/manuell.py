"""Der Provider, mit dem der Drafter heute laeuft.

Liest die gepflegten Daten aus der eigenen Datenbank - dieselben Zeilen,
die auch der Datenraum benutzt. Er existiert nicht, weil der Drafter ihn
braeuchte, sondern damit die Schnittstelle von Anfang an einen echten
Nutzer hat: eine Abstraktion ohne Implementierung ist nur eine Vermutung
darueber, wie sie spaeter aussehen muesste.
"""

from drafter.models import BrawlerItem, BrawlerStat, CounterStat, Datenquelle, SynergyStat
from drafter.services.providers.basis import (
    BuildDataProvider, MetaDataProvider,
)


class ManualDataProvider(MetaDataProvider, BuildDataProvider):
    """Gepflegte Daten aus der Datenbank."""

    name = "manuell"

    def verfuegbar(self):
        return BrawlerStat.objects.exists() or CounterStat.objects.exists()

    @property
    def ist_demo(self):
        return not BrawlerStat.objects.exclude(source=Datenquelle.DEMO).exists()

    def brawler_staerke(self, brawler, kontext=None):
        return BrawlerStat.objects.filter(brawler=brawler).first()

    def counter(self, brawler, gegner, kontext=None):
        return CounterStat.objects.filter(brawler=brawler, enemy=gegner).first()

    def synergie(self, a, b, kontext=None):
        erster, zweiter = (a, b) if a.id < b.id else (b, a)
        return SynergyStat.objects.filter(brawler_a=erster, brawler_b=zweiter).first()

    def builds(self, brawler, kontext=None):
        return list(
            BrawlerItem.objects.filter(brawler=brawler, is_active=True)
            .prefetch_related("rules")
        )
