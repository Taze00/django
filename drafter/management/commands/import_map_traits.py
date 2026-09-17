# -*- coding: utf-8 -*-
"""Map-Merkmale aus einer gepflegten Datei einlesen - oder eine Vorlage schreiben.

    python manage.py import_map_traits --vorlage data/map_traits.json
    python manage.py import_map_traits --datei data/map_traits.json --trocken
    python manage.py import_map_traits --datei data/map_traits.json

Die Merkmale (openness, wall_density, bush_density, choke_points,
lane_count) stehen in keiner API - sie muessen von Hand gepflegt werden.
Damit das nachvollziehbar und korrigierbar bleibt, liegen sie in einer
JSON-Datei und nicht in der Datenbank allein:

    {"hard-rock-mine": {"openness": 45, "wall_density": 70, ...}}

`--vorlage` schreibt ein Geruest mit allen Maps OHNE Merkmale und leeren
Werten (null). Nichts wird dabei geraten: null bleibt null, und eine Map
mit null-Werten wird beim Import uebersprungen, nicht auf 0 gesetzt.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from drafter import attributes as attr
from drafter.models import BrawlMap


class Command(BaseCommand):
    help = "Map-Merkmale aus einer JSON-Datei einlesen (oder Vorlage schreiben)."

    def add_arguments(self, parser):
        parser.add_argument("--datei", help="JSON mit {map-slug: {trait: wert}}")
        parser.add_argument("--vorlage", help="Geruest für Maps ohne Merkmale hierhin schreiben")
        parser.add_argument("--trocken", action="store_true", help="Nur berichten")
        parser.add_argument("--nur-aktive", action="store_true",
                            help="Vorlage nur für aktive Maps")

    def handle(self, *args, **opts):
        if not opts["datei"] and not opts["vorlage"]:
            raise CommandError("--datei oder --vorlage angeben.")
        if opts["vorlage"]:
            self._vorlage(Path(opts["vorlage"]), opts["nur_aktive"])
        if opts["datei"]:
            self._einlesen(Path(opts["datei"]), opts["trocken"])

    def _vorlage(self, pfad, nur_aktive):
        maps = BrawlMap.objects.select_related("game_mode").order_by("game_mode__name", "name")
        if nur_aktive:
            maps = maps.filter(is_active=True)
        offen = [k for k in maps if not k.traits]
        geruest = {
            k.slug: {
                "_name": k.name, "_modus": k.game_mode.name,
                **{key: None for key in attr.MAP_TRAIT_KEYS},
            }
            for k in offen
        }
        pfad.parent.mkdir(parents=True, exist_ok=True)
        pfad.write_text(json.dumps(geruest, indent=2, ensure_ascii=False), encoding="utf-8")
        self.stdout.write(
            f"Vorlage für {len(offen)} Maps ohne Merkmale geschrieben: {pfad}\n"
            f"  Felder: {', '.join(attr.MAP_TRAIT_KEYS)} (null lassen, was unbekannt ist)"
        )

    def _einlesen(self, pfad, trocken):
        try:
            daten = json.loads(pfad.read_text(encoding="utf-8"))
        except (OSError, ValueError) as fehler:
            raise CommandError(f"Datei nicht lesbar: {fehler}")
        if not isinstance(daten, dict):
            raise CommandError("Erwartet ein Objekt {map-slug: {trait: wert}}")

        nach_slug = {k.slug: k for k in BrawlMap.objects.all()}
        gesetzt, uebersprungen, unbekannt, fehlerhaft = [], [], [], []
        for slug, werte in daten.items():
            karte = nach_slug.get(slug)
            if karte is None:
                unbekannt.append(slug)
                continue
            # Unterstriche sind Notizen der Vorlage (_name, _modus), null
            # heisst "noch nicht gepflegt" - beides wird nicht gespeichert.
            sauber = {
                k: v for k, v in (werte or {}).items()
                if not k.startswith("_") and v is not None
            }
            if not sauber:
                uebersprungen.append(slug)
                continue
            fehler = attr.pruefe_map_traits(sauber)
            if fehler:
                fehlerhaft.append(f"{slug}: {'; '.join(fehler)}")
                continue
            if not trocken:
                BrawlMap.objects.filter(pk=karte.pk).update(traits={**(karte.traits or {}), **sauber})
            gesetzt.append(slug)

        self.stdout.write(f"Gesetzt: {len(gesetzt)}")
        if uebersprungen:
            self.stdout.write(f"  Ohne gepflegte Werte übersprungen: {len(uebersprungen)}")
        if unbekannt:
            self.stdout.write(self.style.ERROR(f"  Unbekannte Map-Slugs: {', '.join(unbekannt)}"))
        if fehlerhaft:
            self.stdout.write(self.style.ERROR("  Ungültig:\n    " + "\n    ".join(fehlerhaft)))
        ohne = BrawlMap.objects.filter(traits={}).count()
        self.stdout.write(f"  Maps weiterhin ohne Merkmale: {ohne}")
        if trocken:
            self.stdout.write(self.style.WARNING("Trockenlauf - nichts gespeichert."))
