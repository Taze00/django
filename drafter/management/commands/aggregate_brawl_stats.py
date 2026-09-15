# -*- coding: utf-8 -*-
"""Aus importierten Partien Statistiken rechnen.

    python manage.py aggregate_brawl_stats                        # gemessene Quellen, alles
    python manage.py aggregate_brawl_stats --quelle synthetisch
    python manage.py aggregate_brawl_stats --fenster 7d seit_patch --rank-pool masters
    python manage.py aggregate_brawl_stats --stichtag 2026-09-01  # rueckwirkend

Idempotent: jeder Lauf ersetzt die Zeilen seines Kontexts (Quelle,
Rangbereich, Zeitfenster) vollstaendig. Demo-Daten werden nie beruehrt.
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from drafter import config
from drafter.models import Datenquelle
from drafter.services.aggregation.aggregator import Aggregator

QUELLEN_WAHL = {
    "gemessen": (Datenquelle.FIXTURE, Datenquelle.API),
    "fixture": (Datenquelle.FIXTURE,),
    "api": (Datenquelle.API,),
    "synthetisch": (Datenquelle.SYNTHETIC,),
}


def stichtag(wert):
    try:
        return date.fromisoformat(wert)
    except ValueError:
        raise CommandError(f"Stichtag muss JJJJ-MM-TT sein, nicht {wert!r}")


def aggregations_argumente(parser):
    parser.add_argument("--quelle", choices=sorted(QUELLEN_WAHL), default="gemessen")
    parser.add_argument("--stichtag", type=str, default=None,
                        help="Bezugstag für Zeitfenster und Zeitgewicht (Standard: heute)")
    parser.add_argument("--alle-partien", action="store_true",
                        help="Auch nicht-ranked Partien zählen")


class Command(BaseCommand):
    help = "Aggregiert importierte Partien zu Brawler-, Counter-, Synergie- und Build-Statistiken."

    def add_arguments(self, parser):
        aggregations_argumente(parser)
        parser.add_argument("--fenster", nargs="+", choices=list(config.AGGREGATIONS_FENSTER))
        parser.add_argument("--rank-pool", nargs="+", choices=[k for k, _ in config.RANG_POOLS])

    def handle(self, *args, **optionen):
        try:
            aggregator = Aggregator(
                QUELLEN_WAHL[optionen["quelle"]],
                stichtag=stichtag(optionen["stichtag"]) if optionen["stichtag"] else None,
                rank_pools=optionen["rank_pool"],
                fenster=optionen["fenster"],
                nur_ranked=not optionen["alle_partien"],
            )
        except ValueError as fehler:
            raise CommandError(str(fehler))

        bericht = aggregator.ausfuehren()
        for zeile in bericht.zeilen_text():
            self.stdout.write(zeile)
