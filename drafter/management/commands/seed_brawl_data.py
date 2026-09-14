"""Demo-Datensatz in die Datenbank schreiben.

    python manage.py seed_brawl_data
    python manage.py seed_brawl_data --reset

Idempotent: mehrfaches Ausfuehren aendert nur, was sich in
`drafter/seed_data.py` geaendert hat. Deshalb ein Management-Kommando
und keine Fixture - eine Fixture muesste man exportieren und neu
einspielen, dieses Kommando gleicht ab.

`--reset` loescht **nur** Demo-Daten (`source="demo"`). Von Hand
gepflegte oder aus Matches berechnete Zeilen bleiben stehen; sonst
haette ein Seed-Lauf spaeter echte Arbeit vernichtet.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from drafter import seed_data
from drafter.models import (
    Brawler, BrawlerItem, BrawlerStat, BrawlMap, BuildRule, CounterStat,
    Datenquelle, GameMode, Patch, SynergyStat,
)


class Command(BaseCommand):
    help = "Legt den gekennzeichneten Demo-Datensatz des Drafters an oder aktualisiert ihn."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Vorhandene Demo-Daten vorher löschen (echte Daten bleiben).",
        )

    @transaction.atomic
    def handle(self, *args, **optionen):
        # In Tests laeuft dieses Kommando je Testklasse - ohne diese
        # Zeile stehen zwischen den Testergebnissen zwanzig Seed-Berichte.
        self.leise = optionen.get("verbosity", 1) == 0
        if optionen["reset"]:
            self._reset()

        patch = self._patch()
        modi = self._modi()
        maps = self._maps(modi)
        brawler = self._brawler()
        self._meta(brawler, patch)
        self._counter(brawler)
        self._synergien(brawler)
        items = self._items(brawler)
        self._regeln(items)

        self._sag(self.style.SUCCESS(
            f"\nFertig: {len(brawler)} Brawler, {len(maps)} Maps, "
            f"{len(modi)} Modi, {len(items)} Ausrüstungsgegenstände."
        ))
        self._sag(
            "Alle Einträge sind als Demo-Daten markiert - die Oberfläche "
            "weist darauf hin."
        )

    def _sag(self, text):
        if not getattr(self, "leise", False):
            self.stdout.write(text)

    # --- Schritte -------------------------------------------------------
    def _reset(self):
        geloescht = 0
        for modell in (CounterStat, SynergyStat, BrawlerStat, BuildRule, BrawlerItem):
            if modell is BuildRule:
                anzahl = BuildRule.objects.filter(item__source=Datenquelle.DEMO).delete()[0]
            else:
                anzahl = modell.objects.filter(source=Datenquelle.DEMO).delete()[0]
            geloescht += anzahl
        self._sag(f"Demo-Daten geloescht: {geloescht} Zeilen")

    def _patch(self):
        patch, _ = Patch.objects.update_or_create(
            name="Demo-Patch",
            defaults={
                "released_on": timezone.now().date(),
                "description": (
                    "Platzhalter für den aktuellen Patch. Sobald echte "
                    "Patchdaten gepflegt werden, ersetzt sie diesen Eintrag."
                ),
                "is_current": True,
            },
        )
        return patch

    def _modi(self):
        modi = {}
        for eintrag in seed_data.MODI:
            modus, _ = GameMode.objects.update_or_create(
                slug=eintrag["slug"],
                defaults={
                    "name": eintrag["name"],
                    "description": eintrag.get("description", ""),
                    "win_condition": eintrag.get("win_condition", ""),
                    "base_requirements": eintrag["base_requirements"],
                    "order": eintrag.get("order", 0),
                },
            )
            modi[eintrag["slug"]] = modus
        self._sag(f"Modi: {len(modi)}")
        return modi

    def _maps(self, modi):
        maps = {}
        for eintrag in seed_data.MAPS:
            karte, _ = BrawlMap.objects.update_or_create(
                slug=eintrag["slug"],
                defaults={
                    "name": eintrag["name"],
                    "game_mode": modi[eintrag["mode"]],
                    "requirements": eintrag["requirements"],
                    "traits": eintrag.get("traits", {}),
                    "notes": eintrag.get("notes", ""),
                    "source": Datenquelle.DEMO,
                },
            )
            maps[eintrag["slug"]] = karte
        self._sag(f"Maps: {len(maps)}")
        return maps

    def _brawler(self):
        brawler = {}
        for eintrag in seed_data.BRAWLER:
            b, _ = Brawler.objects.update_or_create(
                slug=eintrag["slug"],
                defaults={
                    "name": eintrag["name"],
                    "role": eintrag["role"],
                    "tags": eintrag.get("tags", []),
                    "color": eintrag.get("color", "#3a3f4b"),
                    "attributes": eintrag["attributes"],
                    "draft_values": eintrag["draft_values"],
                    "notes": eintrag.get("notes", ""),
                    "source": Datenquelle.DEMO,
                },
            )
            brawler[eintrag["slug"]] = b
        self._sag(f"Brawler: {len(brawler)}")
        return brawler

    def _meta(self, brawler, patch):
        anzahl = 0
        for slug, (winrate, confidence) in seed_data.META.items():
            b = brawler.get(slug)
            if not b:
                continue
            stat = BrawlerStat(
                brawler=b, patch=patch, win_rate=winrate, confidence=confidence,
                source=Datenquelle.DEMO, games=0,
            )
            # update_or_create geht hier nicht: context_key entsteht erst
            # beim Speichern, ist aber Teil der Eindeutigkeit.
            schluessel = stat.berechne_context_key()
            BrawlerStat.objects.filter(brawler=b, context_key=schluessel).delete()
            stat.save()
            anzahl += 1
        self._sag(f"Meta-Statistiken: {anzahl}")

    def _counter(self, brawler):
        anzahl = 0
        for slug_a, slug_b, vorteil, grund in seed_data.COUNTER:
            a, b = brawler.get(slug_a), brawler.get(slug_b)
            if not a or not b:
                continue
            zeile = CounterStat(
                brawler=a, enemy=b, advantage=vorteil, reason=grund or "",
                confidence=0.25, source=Datenquelle.DEMO,
            )
            schluessel = zeile.berechne_context_key()
            CounterStat.objects.filter(
                brawler=a, enemy=b, context_key=schluessel
            ).delete()
            zeile.save()
            anzahl += 1
        self._sag(f"Counter: {anzahl}")

    def _synergien(self, brawler):
        anzahl = 0
        for slug_a, slug_b, wert, grund in seed_data.SYNERGIE:
            a, b = brawler.get(slug_a), brawler.get(slug_b)
            if not a or not b:
                continue
            # Paar normalisieren - das Modell tut es auch, aber die
            # Abfrage unten braucht die richtige Reihenfolge schon jetzt.
            if a.id > b.id:
                a, b = b, a
            zeile = SynergyStat(
                brawler_a=a, brawler_b=b, synergy=wert, reason=grund or "",
                confidence=0.25, source=Datenquelle.DEMO,
            )
            schluessel = zeile.berechne_context_key()
            SynergyStat.objects.filter(
                brawler_a=a, brawler_b=b, context_key=schluessel
            ).delete()
            zeile.save()
            anzahl += 1
        self._sag(f"Synergien: {anzahl}")

    def _items(self, brawler):
        items = {}
        for name, slug, beschreibung, gewicht in seed_data.GENERISCHE_GEARS:
            gegenstand, _ = BrawlerItem.objects.update_or_create(
                brawler=None, kind=BrawlerItem.Kind.GEAR, slug=slug,
                defaults={
                    "name": name, "description": beschreibung,
                    "base_weight": gewicht, "source": Datenquelle.DEMO,
                },
            )
            items[slug] = gegenstand

        for slug_b, kind, name, slug, beschreibung, gewicht in seed_data.ITEMS:
            b = brawler.get(slug_b)
            if not b:
                continue
            gegenstand, _ = BrawlerItem.objects.update_or_create(
                brawler=b, kind=kind, slug=slug,
                defaults={
                    "name": name, "description": beschreibung,
                    "base_weight": gewicht, "source": Datenquelle.DEMO,
                },
            )
            items[slug] = gegenstand
        self._sag(f"Ausrüstung: {len(items)}")
        return items

    def _regeln(self, items):
        anzahl = 0
        for item_slug, bedingung, gewicht, text, prioritaet in seed_data.BUILD_REGELN:
            gegenstand = items.get(item_slug)
            if not gegenstand:
                self.stderr.write(f"Regel ohne Gegenstand übersprungen: {item_slug}")
                continue
            # Gesucht wird ueber (Gegenstand, Bedingung) - NICHT ueber den
            # Begruendungstext. Sonst legt jede Textaenderung eine zweite
            # Regel an und die alte bleibt liegen: der Drafter begruendet
            # dann mit einem Satz, den es in der Datei laengst nicht mehr
            # gibt. Genau das ist bei der Umstellung auf Umlaute passiert.
            BuildRule.objects.update_or_create(
                item=gegenstand, condition=bedingung,
                defaults={
                    "reason_template": text, "weight": gewicht, "priority": prioritaet,
                },
            )
            anzahl += 1
        self._sag(f"Build-Regeln: {anzahl}")
