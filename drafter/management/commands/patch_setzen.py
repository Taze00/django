# -*- coding: utf-8 -*-
"""Einen Patch anlegen oder aktivieren - mit einem Datum, das von aussen kommt.

Ein Patchdatum ist **externe fachliche Information**. Es darf nicht aus
der ersten gesehenen Partie, dem letzten Collector-Lauf oder dem heutigen
Datum abgeleitet werden: ein geratenes Datum sieht im Betrieb genauso aus
wie ein gepflegtes, schneidet aber still die Statistik. Deshalb ist
`--released-on` hier Pflicht und wird nirgends errechnet.

    python manage.py patch_setzen --liste
    python manage.py patch_setzen --name "2026-09 Herbstupdate" \\
        --released-on 2026-09-17 --quelle "Patch Notes vom 16.09." --aktivieren

**Was ein Patchwechsel NICHT tut:** alte Patches loeschen, Partien
umschreiben, Statistiken wegwerfen. Der alte Patch bleibt historisch
stehen, `BrawlerBalanceChange` haengt weiter an ihm, und die Partien
behalten ihre Zuordnung. Neu aggregiert wird getrennt
(`aggregate_brawl_stats`); erst dann gilt die neue Grenze.

Ohne `--quelle` bleibt das Datum als **unbestaetigt** markiert: es ist
dann ein Platzhalter und wird auch so angezeigt.
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from drafter import config
from drafter.models import Patch
from drafter.models.matches import Match


def _datum(wert):
    try:
        return date.fromisoformat(wert)
    except ValueError:
        raise CommandError(f"--released-on: '{wert}' ist kein Datum (YYYY-MM-DD)")


class Command(BaseCommand):
    help = "Patch anlegen/aktivieren - Datum ausdruecklich angeben, nie ableiten"

    def add_arguments(self, parser):
        parser.add_argument("--liste", action="store_true",
                            help="Alle Patches mit Datumslage zeigen")
        parser.add_argument("--name", help="Name des Patches, z.B. '2026-09 Herbstupdate'")
        parser.add_argument("--released-on", dest="datum",
                            help="Erscheinungsdatum YYYY-MM-DD - keine Ableitung, keine Vorgabe")
        parser.add_argument("--quelle", default="",
                            help="Woher das Datum stammt. Ohne Angabe gilt es als unbestätigt.")
        parser.add_argument("--beschreibung", default="")
        parser.add_argument("--aktivieren", action="store_true",
                            help="Diesen Patch als aktuellen setzen (alle anderen abwählen)")
        parser.add_argument("--trocken", action="store_true",
                            help="Nur zeigen, was passieren würde")

    def handle(self, *args, **o):
        if o["liste"] or not (o["name"] or o["datum"]):
            return self._liste()
        if not o["name"]:
            raise CommandError("--name fehlt")
        if not o["datum"]:
            raise CommandError(
                "--released-on fehlt. Das Datum wird bewusst NICHT geraten - "
                "es kommt aus Patch Notes oder Ankündigung, nicht aus den Daten.")

        datum = _datum(o["datum"])
        vorhanden = Patch.objects.filter(name=o["name"]).first()
        self._warnungen(datum)

        if o["trocken"]:
            was = "aktualisiert" if vorhanden else "angelegt"
            self.stdout.write(f"[trocken] '{o['name']}' würde {was}: {datum}, "
                              f"bestätigt={bool(o['quelle'])}, aktiv={o['aktivieren']}")
            return

        with transaction.atomic():
            patch, neu = Patch.objects.update_or_create(
                name=o["name"],
                defaults={
                    "released_on": datum,
                    "datum_bestaetigt": bool(o["quelle"]),
                    "datum_quelle": o["quelle"],
                    **({"description": o["beschreibung"]} if o["beschreibung"] else {}),
                },
            )
            if o["aktivieren"]:
                # Genau ein aktueller Patch - die Aggregation fragt nach
                # dem juengsten mit `released_on <= Stichtag`, die
                # Oberflaeche nach `is_current`. Zwei aktuelle waeren zwei
                # verschiedene Antworten auf dieselbe Frage.
                Patch.objects.exclude(pk=patch.pk).update(is_current=False)
                patch.is_current = True
                patch.save(update_fields=["is_current"])

        self.stdout.write(self.style.SUCCESS(
            f"{'Angelegt' if neu else 'Aktualisiert'}: {patch.name} · {patch.released_on} · "
            f"{patch.datumslage}{' · aktuell' if patch.is_current else ''}"))
        self.stdout.write(
            "Alte Patches, Partien und Statistiken bleiben unverändert. "
            "Neu rechnen mit: manage.py aggregate_brawl_stats --quelle api")

    # --- Teile ----------------------------------------------------------
    def _warnungen(self, datum):
        """Sagen, was das Datum fuer die vorhandenen Partien bedeutet.

        Kein Abbruch: ein Patch DARF nach der juengsten Partie liegen -
        dann ist das Fenster eben leer, und das soll man vorher wissen,
        statt es hinterher in einer stillen Statistik zu finden.
        """
        juengste = Match.objects.order_by("-played_at").values_list("played_at", flat=True).first()
        if juengste is None:
            return
        danach = Match.objects.filter(played_at__date__gte=datum)
        alle = danach.count()
        # Fuer die Draft-Statistik zaehlt nur soloRanked - die Gesamtzahl
        # allein taeuscht: sie enthaelt Trophaeenpartien, die nie in eine
        # Statistikzeile eingehen.
        ranked = danach.filter(
            is_ranked=True, battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN).count()
        self.stdout.write(f"Jüngste gespeicherte Partie: {juengste:%Y-%m-%d}")
        if ranked == 0:
            self.stdout.write(self.style.WARNING(
                f"  Achtung: keine einzige Ranked-Partie am oder nach dem {datum} "
                f"(Partien gesamt: {alle}). Das Fenster 'seit Patch' bliebe leer, "
                f"die Engine fiele auf ein anderes Fenster zurück."))
        else:
            self.stdout.write(f"  Partien am oder nach dem {datum}: "
                              f"{ranked} Ranked von {alle} gesamt")

    def _liste(self):
        patches = Patch.objects.all()
        if not patches:
            self.stdout.write("Kein Patch eingetragen.")
            return
        self.stdout.write(f"{'Name':<28} {'released_on':>12} {'aktuell':>8}  Datumslage")
        for p in patches:
            self.stdout.write(f"{p.name:<28} {str(p.released_on):>12} "
                              f"{'ja' if p.is_current else '-':>8}  {p.datumslage}")
        self.stdout.write(
            "\nDatum setzen: manage.py patch_setzen --name NAME --released-on YYYY-MM-DD "
            "--quelle \"woher\" [--aktivieren]")
