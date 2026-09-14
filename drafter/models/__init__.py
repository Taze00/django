"""Datenmodelle des Drafters.

Aufgeteilt nach Themen statt einer models.py mit 700 Zeilen. Django
findet die Modelle trotzdem, weil sie hier alle importiert werden.
"""

from drafter.models.base import Datenquelle, StatBasis, Zeitstempel
from drafter.models.brawler import Brawler
from drafter.models.builds import BrawlerItem, BuildRule
from drafter.models.maps import BrawlMap, GameMode
from drafter.models.patches import BrawlerBalanceChange, Patch
from drafter.models.prefs import UserBrawlerPreference
from drafter.models.stats import BrawlerStat, CounterStat, SynergyStat

__all__ = [
    "Datenquelle", "StatBasis", "Zeitstempel",
    "Brawler",
    "GameMode", "BrawlMap",
    "Patch", "BrawlerBalanceChange",
    "BrawlerStat", "CounterStat", "SynergyStat",
    "BrawlerItem", "BuildRule",
    "UserBrawlerPreference",
]
