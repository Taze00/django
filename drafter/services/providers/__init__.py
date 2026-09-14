"""Datenquellen hinter austauschbaren Schnittstellen.

Der Drafter soll nicht wissen, woher seine Zahlen kommen. Heute sind es
gepflegte Demo-Daten, morgen die offizielle API, uebermorgen vielleicht
eine Community-Quelle - und moeglicherweise mehrere gleichzeitig, je
nachdem, was welche Quelle liefern kann.

Deshalb drei schmale Schnittstellen statt eines grossen Importers:

    MatchDataProvider  - einzelne Matches
    MetaDataProvider   - aggregierte Staerke, Counter, Synergien
    BuildDataProvider  - Gadgets, Star Powers, Gears

`ManualDataProvider` bedient alle drei aus der eigenen Datenbank und ist
der Provider, mit dem der Drafter heute laeuft.
"""

from drafter.services.providers.basis import (
    BuildDataProvider, MatchDataProvider, MetaDataProvider,
)
from drafter.services.providers.manuell import ManualDataProvider

__all__ = [
    "MatchDataProvider", "MetaDataProvider", "BuildDataProvider",
    "ManualDataProvider",
]
