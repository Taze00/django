# -*- coding: utf-8 -*-
"""Alle Statistiken einer Quelle von Grund auf neu aufbauen.

    python manage.py rebuild_draft_stats
    python manage.py rebuild_draft_stats --quelle synthetisch

Unterschied zu aggregate_brawl_stats:
- ordnet allen Partien ihren Patch NEU zu (noetig, wenn ein Patch
  nachtraeglich eingetragen wurde)
- loescht ALLE Zeilen der Zielquelle, auch die von Zeitfenstern oder
  Rangbereichen, die es nicht mehr gibt
- aggregiert danach alle Fenster und Rangbereiche

Demo- und gepflegte Daten sind ausgeschlossen - sie sind keine Matches
und koennen nicht "neu berechnet" werden.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from drafter.management.commands.aggregate_brawl_stats import (
    QUELLEN_WAHL, aggregations_argumente, stichtag,
)
from drafter.services.aggregation.aggregator import (
    STAT_MODELLE, Aggregator, patches_neu_zuordnen, ziel_quelle_fuer,
)


class Command(BaseCommand):
    help = "Baut alle Statistiken einer Quelle neu auf (Patchzuordnung, Löschen, Aggregieren)."

    def add_arguments(self, parser):
        aggregations_argumente(parser)

    def handle(self, *args, **optionen):
        quellen = QUELLEN_WAHL[optionen["quelle"]]
        try:
            ziel = ziel_quelle_fuer(quellen)
        except ValueError as fehler:
            raise CommandError(str(fehler))

        with transaction.atomic():
            neu_zugeordnet = patches_neu_zuordnen(quellen)
            geloescht = sum(m.objects.filter(source=ziel).delete()[0] for m in STAT_MODELLE)
            bericht = Aggregator(
                quellen,
                stichtag=stichtag(optionen["stichtag"]) if optionen["stichtag"] else None,
                nur_ranked=not optionen["alle_partien"],
            ).ausfuehren()

        self.stdout.write(f"Patch neu zugeordnet: {neu_zugeordnet} Partien")
        self.stdout.write(f"Gelöschte Zeilen der Quelle '{ziel}': {geloescht}")
        for zeile in bericht.zeilen_text():
            self.stdout.write(zeile)
