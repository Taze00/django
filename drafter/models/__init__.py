"""Datenmodelle des Drafters.

Aufgeteilt nach Themen statt einer models.py mit 700 Zeilen. Django
findet die Modelle trotzdem, weil sie hier alle importiert werden.
"""

from drafter.models.base import NICHT_GEMESSEN, Datenquelle, StatBasis, Zeitstempel
from drafter.models.brawler import Brawler
from drafter.models.builds import BrawlerItem, BuildRule
from drafter.models.collector import CollectorRun, TaggedPlayer, TaggedPlayerObservation, TrackedPlayer
from drafter.models.maps import BrawlMap, GameMode
from drafter.models.matches import Match, MatchBan, MatchPlayer, RawPayload
from drafter.models.patches import BrawlerBalanceChange, Patch
from drafter.models.praxis import Ergebnis, Fehlerklasse, Praxisfall
from drafter.models.prefs import UserBrawlerPreference
from drafter.models.stats import BrawlerStat, BuildStat, CounterStat, SynergyStat

__all__ = [
    "NICHT_GEMESSEN", "Datenquelle", "StatBasis", "Zeitstempel",
    "Brawler",
    "GameMode", "BrawlMap",
    "Patch", "BrawlerBalanceChange",
    "BrawlerStat", "BuildStat", "CounterStat", "SynergyStat",
    "BrawlerItem", "BuildRule",
    "UserBrawlerPreference",
    "RawPayload", "Match", "MatchPlayer", "MatchBan",
    "TrackedPlayer", "CollectorRun", "TaggedPlayer", "TaggedPlayerObservation",
    "Praxisfall", "Ergebnis", "Fehlerklasse",
]
