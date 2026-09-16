# -*- coding: utf-8 -*-
"""Kontrollierter Collector-Lauf gegen die offizielle API.

    python manage.py collect_brawl_matches --max-spieler 10
    python manage.py collect_brawl_matches --spieler "#TAG" --ohne-rangliste
    python manage.py collect_brawl_matches --max-spieler 25 --dateien

Ruft die globale Trophaeen-Rangliste als Saat ab, holt Battlelogs und
entdeckt Mitspieler aus soloRanked-Partien. Begrenzt durch Budget
(--max-spieler), Tiefe (--max-tiefe) und Abrufabstand - siehe
services/collector.py. Aggregiert nichts.

Der API-Key kommt ausschliesslich aus BRAWL_STARS_API_KEY.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError

from drafter import config
from drafter.services.brawl_api_client import ApiFehler
from drafter.services.collector import Collector


class Command(BaseCommand):
    help = (
        "Sammelt Battlelogs hochplatzierter Spieler: Rangliste -> Battlelogs -> "
        "Mitspieler aus soloRanked. Mit Budget, Tiefengrenze und Abrufabstand."
    )

    def add_arguments(self, parser):
        parser.add_argument("--max-spieler", type=int, default=config.COLLECTOR_MAX_SPIELER,
                            help="Battlelogs je Lauf (Standard: %(default)s)")
        parser.add_argument("--max-tiefe", type=int, default=config.COLLECTOR_MAX_TIEFE,
                            choices=range(0, config.COLLECTOR_TIEFE_OBERGRENZE + 1),
                            help="0 = nur Saat, 1 = deren Mitspieler (Standard: %(default)s)")
        parser.add_argument("--abruf-abstand-stunden", type=float,
                            default=config.COLLECTOR_ABRUF_ABSTAND_STUNDEN,
                            help="Denselben Spieler frühestens nach so vielen Stunden erneut")
        parser.add_argument("--spieler", nargs="+", default=[], metavar="TAG",
                            help='Zusätzliche Saat, z.B. "#2ABC" (Anführungszeichen wegen #)')
        parser.add_argument("--ohne-rangliste", action="store_true",
                            help="Keine Rangliste abrufen - nur bereits bekannte Spieler")
        parser.add_argument("--ohne-katalog", action="store_true",
                            help="/brawlers nicht abrufen (nur wenn alle IDs schon stehen)")
        parser.add_argument("--dateien", action="store_true",
                            help=f"Rohantworten zusätzlich als Dateien nach "
                                 f"{config.FIXTURE_VERZEICHNIS}")

    def handle(self, *args, **optionen):
        try:
            collector = Collector(
                max_spieler=optionen["max_spieler"],
                max_tiefe=optionen["max_tiefe"],
                abruf_abstand=timedelta(hours=optionen["abruf_abstand_stunden"]),
                rangliste=not optionen["ohne_rangliste"],
                katalog=not optionen["ohne_katalog"],
                spieler_tags=optionen["spieler"],
                datei_verzeichnis=config.FIXTURE_VERZEICHNIS if optionen["dateien"] else None,
            )
        except (ValueError, ApiFehler) as fehler:
            raise CommandError(str(fehler))

        if not collector.client.einsatzbereit:
            raise CommandError(
                "BRAWL_STARS_API_KEY ist nicht gesetzt. In die .env eintragen und den Befehl "
                "über `docker compose run --rm --no-deps -T django-dev …` starten."
            )

        bericht = collector.ausfuehren()
        for zeile in bericht.zeilen():
            self.stdout.write(zeile)
        if bericht.abbruch:
            self.stderr.write(self.style.WARNING(
                "Lauf abgebrochen - bereits gelesene Partien sind gespeichert."
            ))
        elif bericht.neu:
            self.stdout.write(self.style.SUCCESS(
                "\nNächster Schritt: python manage.py vergleiche_brawl_stats --quelle api "
                "(nach aggregate_brawl_stats --quelle api)"
            ))
