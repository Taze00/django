# -*- coding: utf-8 -*-
"""Der Provider fuer die gepflegten Demo-Daten.

Liest die Zeilen, die `seed_brawl_data` anlegt - und zusaetzlich die, die
im Admin auf "Manuell gepflegt" umgestellt wurden. Beides sind
Einschaetzungen von Hand und keine Messungen; beide unterliegen deshalb
dem Confidence-Deckel.

Der Drafter lief bisher ausschliesslich auf diesen Daten, nur ohne
Provider dazwischen. Die Zahlen sind dieselben geblieben - ein Test haelt
fest, dass die Empfehlungen vor und nach der Umstellung identisch sind.
"""

from drafter.models import Datenquelle
from drafter.services.providers.datenbank import DatenbankStatProvider


class DemoDataProvider(DatenbankStatProvider):
    name = "demo"

    def __init__(self):
        super().__init__((Datenquelle.DEMO, Datenquelle.MANUAL), name="demo")
