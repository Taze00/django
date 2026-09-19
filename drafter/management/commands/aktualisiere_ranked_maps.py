# -*- coding: utf-8 -*-
"""Welche Maps kommen in gezaehlten Ranked-Partien vor? (ohne Netz)

    python manage.py aktualisiere_ranked_maps
    python manage.py aktualisiere_ranked_maps --trocken

Rechnet `observed_ranked_games` und `last_seen_ranked` aus den bereits
importierten Partien. Loescht nichts und schaltet nichts ab: `is_active`
bleibt unberuehrt, damit eine gepflegte Map nicht verschwindet, weil die
Rotation sie gerade aussetzt.

Die Identitaet ist die Map-Zeile, die der Import ueber die `external_id`
zugeordnet hat - nie der Name. Gleichnamige Maps mit verschiedenen IDs
bleiben getrennt.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Max

from drafter import config
from drafter.models import BrawlMap
from drafter.models.matches import Match


class Command(BaseCommand):
    help = "Traegt beobachtete Ranked-Nutzung je Map nach (ohne API-Zugriff)."

    def add_arguments(self, parser):
        parser.add_argument("--trocken", action="store_true",
                            help="Nur zeigen, nichts speichern")

    def handle(self, *args, **opts):
        zaehlbar = Match.objects.filter(
            is_ranked=True, battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN,
            brawl_map__isnull=False,
        )
        zeilen = (zaehlbar.values("brawl_map")
                  .annotate(n=Count("id"), zuletzt=Max("played_at")))
        gesehen = {z["brawl_map"]: (z["n"], z["zuletzt"]) for z in zeilen}

        geaendert = neu_waehlbar = 0
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Beobachtete Maps: {len(gesehen)} | Fenster {config.RANKED_MAP_FENSTER_TAGE} Tage "
            f"| Rauschgrenze {config.RANKED_MAP_MIN_PARTIEN} Partien"))
        for karte in BrawlMap.objects.select_related("game_mode").order_by(
                "game_mode__slug", "-observed_ranked_games"):
            vorher = karte.waehlbar
            n, zuletzt = gesehen.get(karte.id, (0, None))
            if (karte.observed_ranked_games, karte.last_seen_ranked) == (n, zuletzt):
                continue
            karte.observed_ranked_games = n
            karte.last_seen_ranked = zuletzt
            if not opts["trocken"]:
                karte.save(update_fields=["observed_ranked_games", "last_seen_ranked",
                                          "updated_at"])
            geaendert += 1
            if karte.waehlbar and not vorher:
                neu_waehlbar += 1
                self.stdout.write(
                    f"  neu wählbar: {karte.game_mode.slug:<12} {karte.name:<26} "
                    f"ID {karte.external_id or '-'} | {n} Partien, zuletzt "
                    f"{zuletzt:%Y-%m-%d}")

        self.stdout.write(f"\n{geaendert} Maps aktualisiert, {neu_waehlbar} neu wählbar")
        for modus_slug in sorted({k.game_mode.slug for k in BrawlMap.objects.select_related("game_mode")}):
            karten = [k for k in BrawlMap.objects.select_related("game_mode")
                      .filter(game_mode__slug=modus_slug)]
            waehlbar = [k for k in karten if k.waehlbar]
            if waehlbar:
                self.stdout.write(
                    f"  {modus_slug:<14} wählbar {len(waehlbar):>2} von {len(karten):>2}"
                    f" ({', '.join(k.name for k in waehlbar)})")
        if opts["trocken"]:
            self.stdout.write(self.style.WARNING("\nTrockenlauf - nichts gespeichert."))
