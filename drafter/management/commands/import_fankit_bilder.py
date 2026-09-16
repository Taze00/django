# -*- coding: utf-8 -*-
"""Portraits und Map-Bilder aus dem offiziellen Supercell Fan Kit einspielen.

    python manage.py import_fankit_bilder --brawler PFAD [--maps PFAD]
    python manage.py import_fankit_bilder --brawler PFAD --trocken
    python manage.py import_fankit_bilder --brawler PFAD --zuordnung zuordnung.json

Quelle ist ausschliesslich das Fan Kit (fankit.supercell.com), von Hand im
Browser heruntergeladen. Der Befehl laedt NICHTS aus dem Netz: das Fan Kit
ist ein Portal mit Anmeldung und Nutzungsbedingungen, und Dateien daraus
automatisch abzuholen hiesse, genau diese Bedingungen zu umgehen.
Fremde Spiegel (Wikis, Community-CDNs, GitHub-Kopien) sind keine Quelle -
dort ist nicht nachpruefbar, ob eine Datei unveraendert aus dem Fan Kit
stammt.

Was passiert:

1. Jede Bilddatei wird ueber ihren Dateinamen einem Brawler bzw. einer Map
   zugeordnet (Slug oder Name, ohne Gross-/Kleinschreibung, Trennzeichen
   und Zusaetze wie "portrait"). Was nicht eindeutig passt, wird NICHT
   geraten, sondern gemeldet - und laesst sich mit --zuordnung von Hand
   festlegen.
2. Die Datei wird proportional verkleinert, sonst nicht veraendert: das
   Fan Kit erlaubt nur das. Kein Zuschnitt, kein Formatwechsel, keine
   Farbaenderung. Verkleinert wird, weil das Gitter 54px-Kacheln zeigt
   und ein 1000px-Original dort nur Ladezeit kostet.
3. Sie landet unter static/drafter/fankit/ (gitignored - die Bilder
   gehoeren Supercell und nicht ins Repository), `image_url` zeigt darauf.
   Der Pfad traegt eine Pruefsumme (?v=...), damit ein ausgetauschtes
   Bild nicht aus dem Browser-Cache kommt.

Danach: `collectstatic` laeuft automatisch mit, gunicorn muss neu starten
(WhiteNoise liest die Dateiliste nur beim Start).
"""

import hashlib
import json
import re
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from drafter.models import Brawler, BrawlMap

BILDENDUNGEN = {".png", ".webp", ".jpg", ".jpeg"}

# Laengste Kante nach dem Verkleinern. Brawler: groesste Anzeige ist die
# 54px-Kachel, auf 2x-Bildschirmen also 108px - 160 laesst Luft. Maps
# zeigen 34px-Vorschauen, sind im Original aber hochkant und detailreich.
MAX_KANTE = {"brawler": 160, "maps": 240}

# Woerter, die in Fan-Kit-Dateinamen neben dem eigentlichen Namen stehen.
# "end" und "new" stehen im Fan Kit an Portraits, die nur in dieser Variante
# vorliegen (crow_end_portrait, jessie_new_portrait). Liegt zusaetzlich die
# Grundform vor, meldet der Import beide als mehrdeutig statt zu raten.
FUELLWOERTER = {
    "portrait", "portraits", "brawler", "brawlers", "icon", "icons", "avatar",
    "map", "maps", "default", "hd", "and", "bs", "brawlstars", "end", "new",
}

# Dateinamen im Fan Kit, die weder Slug noch Anzeigename treffen: interne
# Spielnamen und ein Tippfehler. Nur belegte Faelle - alles andere wird
# gemeldet, nicht geraten.
ALIASE = {
    "mike": "dynamike",            # mike_portrait.png
    "primo": "el-primo",           # primo_portrait.png
    "larrielawrie": "larry-lawrie",  # larrie&lawrie_portrait.png
}

STANDARD_ZIEL = Path(settings.BASE_DIR) / "static" / "drafter" / "fankit"


def schluessel(text):
    """Vergleichsform fuer Dateinamen, Slugs und Namen.

    "8-BIT" -> "8bit", "Mr. P" -> "mrp", "gale_portrait_02" -> "gale".
    Ziffern am ENDE fallen weg (Versionsnummern im Dateinamen), Ziffern
    am Anfang nicht - sonst verloere 8-Bit seine Acht.
    """
    teile = [t for t in re.split(r"[^0-9a-z]+", text.lower()) if t]
    teile = [t for t in teile if t not in FUELLWOERTER]
    while len(teile) > 1 and teile[-1].isdigit():
        teile.pop()
    return "".join(teile)


class Command(BaseCommand):
    help = "Portraits und Map-Bilder aus einem heruntergeladenen Fan-Kit-Ordner einspielen."

    def add_arguments(self, parser):
        parser.add_argument("--brawler", help="Ordner mit Brawler-Portraits aus dem Fan Kit")
        parser.add_argument("--maps", help="Ordner mit Map-Bildern aus dem Fan Kit")
        parser.add_argument(
            "--zuordnung",
            help='JSON-Datei {"dateiname.png": "slug"} fuer Dateien, die nicht eindeutig passen',
        )
        parser.add_argument("--trocken", action="store_true",
                            help="Nur berichten, nichts schreiben")
        parser.add_argument("--ziel", default=str(STANDARD_ZIEL),
                            help="Zielordner (Standard: static/drafter/fankit)")
        parser.add_argument("--ohne-collectstatic", action="store_true",
                            help="collectstatic nicht mitlaufen lassen")

    def handle(self, *args, **opts):
        if not opts["brawler"] and not opts["maps"]:
            raise CommandError("Mindestens --brawler oder --maps angeben.")

        zuordnung = {}
        if opts["zuordnung"]:
            try:
                zuordnung = json.loads(Path(opts["zuordnung"]).read_text(encoding="utf-8"))
            except (OSError, ValueError) as fehler:
                raise CommandError(f"Zuordnung nicht lesbar: {fehler}")

        ziel = Path(opts["ziel"])
        static_wurzel = Path(settings.BASE_DIR) / "static"
        geschrieben = 0

        for art, modell, ordner in (
            ("brawler", Brawler, opts["brawler"]),
            ("maps", BrawlMap, opts["maps"]),
        ):
            if not ordner:
                continue
            geschrieben += self._art(art, modell, Path(ordner), zuordnung, ziel,
                                     static_wurzel, opts["trocken"])

        if opts["trocken"]:
            self.stdout.write(self.style.WARNING("Trockenlauf - nichts geschrieben."))
            return
        if geschrieben and not opts["ohne_collectstatic"]:
            call_command("collectstatic", interactive=False, verbosity=0)
            self.stdout.write("collectstatic gelaufen. Jetzt: docker compose restart django-dev")

    # ------------------------------------------------------------------
    def _art(self, art, modell, ordner, zuordnung, ziel, static_wurzel, trocken):
        if not ordner.is_dir():
            raise CommandError(f"Kein Ordner: {ordner}")

        objekte = list(modell.objects.all())
        nach_schluessel = {}
        for obj in objekte:
            for k in {schluessel(obj.slug), schluessel(obj.name)}:
                nach_schluessel.setdefault(k, set()).add(obj)
        nach_slug = {obj.slug: obj for obj in objekte}

        dateien = sorted(p for p in ordner.rglob("*") if p.suffix.lower() in BILDENDUNGEN)
        treffer = {}          # obj -> [Pfad]
        ohne_treffer = []

        for datei in dateien:
            if datei.name in zuordnung:
                obj = nach_slug.get(zuordnung[datei.name])
                if obj is None:
                    ohne_treffer.append(f"{datei.name} (Zuordnung: unbekannter Slug "
                                        f"'{zuordnung[datei.name]}')")
                    continue
                treffer.setdefault(obj, []).insert(0, datei)   # Zuordnung gewinnt
                continue
            k = schluessel(datei.stem)
            if k in ALIASE and ALIASE[k] in nach_slug:
                treffer.setdefault(nach_slug[ALIASE[k]], []).append(datei)
                continue
            kandidaten = nach_schluessel.get(k, set())
            if len(kandidaten) == 1:
                treffer.setdefault(next(iter(kandidaten)), []).append(datei)
            else:
                ohne_treffer.append(datei.name)

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{art}: {len(dateien)} Dateien in {ordner}"))
        geschrieben = 0
        mehrdeutig = []
        for obj, pfade in sorted(treffer.items(), key=lambda p: p[0].slug):
            festgelegt = pfade[0].name in zuordnung
            if len(pfade) > 1 and not festgelegt:
                # Mehrere Dateien fuer denselben Brawler (Varianten, Skins):
                # welche die richtige ist, steht nicht im Dateinamen.
                mehrdeutig.append(f"{obj.slug}: {', '.join(p.name for p in pfade)}")
                continue
            quelle = pfade[0]
            if obj.image_url and "/drafter/fankit/" not in obj.image_url:
                self.stdout.write(f"  übersprungen {obj.slug}: hat schon ein fremdes Bild "
                                  f"({obj.image_url})")
                continue
            if trocken:
                self.stdout.write(f"  {obj.slug:<24} <- {quelle.name}")
                continue
            url = self._schreiben(quelle, art, obj.slug, ziel, static_wurzel)
            modell.objects.filter(pk=obj.pk).update(image_url=url)
            self.stdout.write(f"  {obj.slug:<24} <- {quelle.name}")
            geschrieben += 1

        if mehrdeutig:
            self.stdout.write(self.style.WARNING(
                "  Mehrdeutig (mit --zuordnung festlegen):\n    " + "\n    ".join(mehrdeutig)))
        if ohne_treffer:
            self.stdout.write(self.style.WARNING(
                "  Ohne Treffer:\n    " + "\n    ".join(ohne_treffer)))

        if not trocken:
            gesamt = modell.objects.count()
            ohne = sorted(o.slug for o in modell.objects.filter(image_url=""))
            self.stdout.write(self.style.SUCCESS(
                f"  Ergebnis: {gesamt - len(ohne)} von {gesamt} mit Bild, "
                f"{len(ohne)} weiter mit Kürzel"))
            if ohne:
                self.stdout.write(f"  Ohne Bild: {', '.join(ohne)}")
        return geschrieben

    def _schreiben(self, quelle, art, slug, ziel, static_wurzel):
        from PIL import Image

        ordner = ziel / art
        ordner.mkdir(parents=True, exist_ok=True)
        endung = quelle.suffix.lower()
        datei = ordner / f"{slug}{endung}"

        with Image.open(quelle) as bild:
            if max(bild.size) > MAX_KANTE[art]:
                # thumbnail() verkleinert proportional und nie ueber das
                # Original hinaus - genau die eine Aenderung, die das Fan
                # Kit erlaubt.
                bild.thumbnail((MAX_KANTE[art], MAX_KANTE[art]), Image.LANCZOS)
                bild.save(datei, optimize=True)
            else:
                shutil.copyfile(quelle, datei)

        pruefsumme = hashlib.sha1(datei.read_bytes()).hexdigest()[:8]
        try:
            relativ = datei.resolve().relative_to(static_wurzel.resolve())
            return f"{settings.STATIC_URL}{relativ.as_posix()}?v={pruefsumme}"
        except ValueError:
            # Ziel ausserhalb von static/ (nur in Tests) - Pfad trotzdem
            # im erkennbaren Fankit-Schema, damit ein zweiter Lauf ihn als
            # eigenen erkennt.
            return f"/static/drafter/fankit/{art}/{datei.name}?v={pruefsumme}"
