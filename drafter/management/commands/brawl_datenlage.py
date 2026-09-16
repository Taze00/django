# -*- coding: utf-8 -*-
"""Was liegt an echten Daten vor? Ohne Netz, ohne Aenderung.

    python manage.py brawl_datenlage
    python manage.py brawl_datenlage --quelle api --top 25

Zeigt Spielerwarteschlange, Collector-Laeufe, gespeicherte Rohantworten und
die Verteilung der importierten Partien - Trophaeen und soloRanked strikt
getrennt.
"""

from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models import Sum

from drafter import config
from drafter.models import Datenquelle
from drafter.models.collector import CollectorRun, TrackedPlayer
from drafter.models.matches import Match, MatchPlayer, RawPayload
from drafter.services.ingest.parser import FORMAT_OFFIZIELLER_BATTLELOG

QUELLEN = {
    "api": (Datenquelle.API,),
    "fixture": (Datenquelle.FIXTURE,),
    "gemessen": (Datenquelle.FIXTURE, Datenquelle.API),
}


def _verteilung(zaehler, top, gesamt_text="verschiedene"):
    zeilen = [f"  {name}: {anzahl}" for name, anzahl in zaehler.most_common(top)]
    if len(zaehler) > top:
        zeilen.append(f"  … und {len(zaehler) - top} weitere {gesamt_text}")
    return zeilen or ["  –"]


class Command(BaseCommand):
    help = "Zeigt die vorhandenen Roh- und Matchdaten samt Verteilung - ändert nichts."

    def add_arguments(self, parser):
        parser.add_argument("--quelle", choices=sorted(QUELLEN), default="api")
        parser.add_argument("--top", type=int, default=15)

    def handle(self, *args, **optionen):
        quellen = QUELLEN[optionen["quelle"]]
        top = optionen["top"]
        schreibe = self.stdout.write

        # --- Spieler ---------------------------------------------------
        spieler = TrackedPlayer.objects.all()
        schreibe(self.style.MIGRATE_HEADING("Beobachtete Spieler"))
        schreibe(f"  bekannt: {spieler.count()}"
                 f" | abgefragt: {spieler.filter(fetch_count__gt=0).count()}"
                 f" | noch nie: {spieler.filter(last_fetched_at__isnull=True).count()}")
        schreibe(f"  nach Herkunft: {dict(Counter(spieler.values_list('origin', flat=True)))}")
        schreibe(f"  nach Tiefe:    {dict(Counter(spieler.values_list('depth', flat=True)))}")
        letzte_status = Counter(s for s in spieler.values_list("last_status", flat=True) if s)
        schreibe(f"  letzter Status: {dict(letzte_status)}")
        solo = spieler.aggregate(summe=Sum("last_solo_ranked_count"))["summe"] or 0
        schreibe(f"  soloRanked im jeweils letzten Battlelog: {solo}")

        # --- Laeufe ----------------------------------------------------
        laeufe = CollectorRun.objects.all()
        schreibe(self.style.MIGRATE_HEADING("\nCollector-Läufe"))
        schreibe(f"  Läufe: {laeufe.count()}"
                 f" | abgebrochen: {laeufe.filter(status=CollectorRun.Status.ABORTED).count()}")
        for lauf in laeufe[:3]:
            bericht = lauf.report or {}
            api = bericht.get("api", {})
            schreibe(f"  {lauf.started_at:%Y-%m-%d %H:%M} {lauf.status}: "
                     f"{bericht.get('spieler_abgefragt', 0)} Spieler, "
                     f"{bericht.get('neu', 0)} neue Partien, "
                     f"{bericht.get('duplikate', 0)} Dubletten, "
                     f"API {api.get('anfragen', 0)} Anfragen {api.get('status', {})}, "
                     f"{api.get('wiederholungen', 0)} Wiederholungen")
            if lauf.abort_reason:
                schreibe(f"    Abbruch: {lauf.abort_reason[:160]}")

        # --- Rohantworten ----------------------------------------------
        roh = RawPayload.objects.filter(source__in=quellen)
        battlelogs = roh.filter(format=FORMAT_OFFIZIELLER_BATTLELOG)
        sichtungen = battlelogs.aggregate(s=Sum("match_count"))["s"] or 0
        neu = battlelogs.aggregate(s=Sum("new_match_count"))["s"] or 0
        schreibe(self.style.MIGRATE_HEADING("\nRohantworten"))
        schreibe(f"  gespeichert: {roh.count()} "
                 f"({dict(Counter(roh.values_list('format', flat=True)))})")
        schreibe(f"  Partien gesehen: {sichtungen} | davon neu: {neu} "
                 f"| als Dublette erkannt: {sichtungen - neu}")

        # --- Partien ---------------------------------------------------
        partien = Match.objects.filter(source__in=quellen)
        nach_typ = Counter(partien.values_list("battle_type", flat=True))
        draft = partien.filter(battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN)
        schreibe(self.style.MIGRATE_HEADING("\nPartien"))
        schreibe(f"  eindeutig: {partien.count()} | nach Partietyp: {dict(nach_typ)}")
        schreibe(f"  für Statistik zählbar (soloRanked, mit Ergebnis, ohne Konflikt): "
                 f"{draft.filter(winner_side__in=['a', 'b'], has_conflict=False).count()}")
        schreibe(f"  ohne Ergebnis: {draft.filter(winner_side='').count()}"
                 f" | Konflikte: {partien.filter(has_conflict=True).count()}")
        schreibe(f"  ohne Katalog-Map: {partien.filter(brawl_map__isnull=True).count()}"
                 f" | ohne Katalog-Modus: {partien.filter(game_mode__isnull=True).count()}")

        spieler_zeilen = MatchPlayer.objects.filter(match__in=draft)
        schreibe(f"  Spielerzeilen (soloRanked): {spieler_zeilen.count()}"
                 f" | ohne Katalog-Brawler: {spieler_zeilen.filter(brawler__isnull=True).count()}")

        schreibe("\nModi (soloRanked):")
        for zeile in _verteilung(Counter(draft.values_list("mode_name", flat=True)), top):
            schreibe(zeile)
        schreibe("\nMaps (soloRanked):")
        karten = Counter(f"{m} ({k})" for k, m in draft.values_list("mode_name", "map_name"))
        for zeile in _verteilung(karten, top):
            schreibe(zeile)
        schreibe("\nBrawler (soloRanked, Picks):")
        brawler = Counter(spieler_zeilen.values_list("brawler_name", flat=True))
        for zeile in _verteilung(brawler, top, "Brawler"):
            schreibe(zeile)
