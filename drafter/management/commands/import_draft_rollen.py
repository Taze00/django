# -*- coding: utf-8 -*-
"""Draft-Rollen und Zusatzfaehigkeiten aus der Role-&-Ability-Map einspielen.

    python manage.py import_draft_rollen
    python manage.py import_draft_rollen --trocken

Quelle ist drafter/fachdaten/role_ability_map.py - eine gepflegte
Fachquelle, keine Messung. Der Befehl setzt `draft_rolle`,
`draft_faehigkeiten` und `ranked_verfuegbar`; Eigenschaften (die 32
Attribute) fasst er NICHT an: aus "hat Rueckstoss" folgt keine Zahl.

Namen werden ueber die normalisierte Form zugeordnet (Gross-/Kleinschreibung,
Punkte, Bindestriche egal), Kurzformen ueber die ALIASE der Quelle. Was
nicht eindeutig passt, wird gemeldet und nicht geraten.
"""

import re

from django.core.management.base import BaseCommand

from drafter import attributes as attr
from drafter.fachdaten import role_ability_map as quelle
from drafter.models import Brawler


def schluessel(text):
    """Vergleichsform: "Mr. P" -> "mrp", "8-Bit" -> "8bit"."""
    return re.sub(r"[^0-9a-z]+", "", (text or "").lower())


class Command(BaseCommand):
    help = "Draft-Rollen und Zusatzfähigkeiten aus der Role-&-Ability-Map übernehmen."

    def add_arguments(self, parser):
        parser.add_argument("--trocken", action="store_true",
                            help="Nur berichten, nichts speichern")

    def handle(self, *args, **opts):
        katalog = list(Brawler.objects.all())
        nach_schluessel = {}
        for b in katalog:
            nach_schluessel.setdefault(schluessel(b.name), []).append(b)
            nach_schluessel.setdefault(schluessel(b.slug), []).append(b)

        faehigkeiten_je_name = {}
        for key, namen in quelle.FAEHIGKEITEN.items():
            for name in namen:
                faehigkeiten_je_name.setdefault(name, []).append(key)

        zugeordnet, alias_benutzt, mehrdeutig, ohne_treffer = {}, [], [], []
        for rolle, namen in quelle.ROLLEN.items():
            for name in namen:
                k = schluessel(name)
                ziel = quelle.ALIASE.get(k)
                if ziel:
                    alias_benutzt.append(f"{name} → {ziel}")
                    k = schluessel(ziel)
                treffer = {b.id: b for b in nach_schluessel.get(k, [])}
                if not treffer:
                    ohne_treffer.append(name)
                    continue
                if len(treffer) > 1:
                    mehrdeutig.append(f"{name} → {[b.name for b in treffer.values()]}")
                    continue
                brawler = next(iter(treffer.values()))
                zugeordnet[brawler.id] = (
                    brawler, rolle, sorted(faehigkeiten_je_name.get(name, [])),
                )

        gesperrt = []
        for name in quelle.NICHT_RANKED:
            # Nach id entdoppeln: derselbe Brawler steht unter Name UND Slug
            # im Verzeichnis - ohne das gaelte jeder Treffer als mehrdeutig.
            treffer = {b.id: b for b in nach_schluessel.get(schluessel(name), [])}
            if len(treffer) == 1:
                gesperrt.append(next(iter(treffer.values())))
            else:
                ohne_treffer.append(f"{name} (Ranked-Sperre)")

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Quelle: {len(quelle.alle_namen())} Namen | Katalog: {len(katalog)} Brawler"))
        geaendert = 0
        if not opts["trocken"]:
            for brawler, rolle, faehigkeiten in zugeordnet.values():
                if (brawler.draft_rolle, sorted(brawler.draft_faehigkeiten or [])) == (rolle, faehigkeiten):
                    continue
                Brawler.objects.filter(pk=brawler.pk).update(
                    draft_rolle=rolle, draft_faehigkeiten=faehigkeiten)
                geaendert += 1
            Brawler.objects.update(ranked_verfuegbar=True)
            Brawler.objects.filter(pk__in=[b.pk for b in gesperrt]).update(ranked_verfuegbar=False)

        je_rolle = {}
        for _, rolle, _ in zugeordnet.values():
            je_rolle[rolle] = je_rolle.get(rolle, 0) + 1
        self.stdout.write(f"  Zugeordnet: {len(zugeordnet)} ({geaendert} geändert)")
        for key, label in attr.DRAFT_ROLLEN:
            self.stdout.write(f"    {label:<24} {je_rolle.get(key, 0)}")
        je_faehigkeit = {}
        for _, _, faehigkeiten in zugeordnet.values():
            for f in faehigkeiten:
                je_faehigkeit[f] = je_faehigkeit.get(f, 0) + 1
            if not faehigkeiten:
                je_faehigkeit["(weiß)"] = je_faehigkeit.get("(weiß)", 0) + 1
        self.stdout.write("  Zusatzfähigkeiten: " + ", ".join(
            f"{attr.DRAFT_FAEHIGKEITEN_LABEL.get(k, k)} {v}" for k, v in sorted(je_faehigkeit.items())))
        self.stdout.write(f"  Ranked gesperrt: {', '.join(b.name for b in gesperrt) or '-'}")

        if alias_benutzt:
            self.stdout.write(self.style.WARNING(
                "  Über Alias zugeordnet (bitte gegenprüfen): " + ", ".join(alias_benutzt)))
        if mehrdeutig:
            self.stdout.write(self.style.ERROR("  MEHRDEUTIG, nicht gesetzt: " + ", ".join(mehrdeutig)))
        if ohne_treffer:
            self.stdout.write(self.style.ERROR(
                "  KEIN TREFFER im Katalog: " + ", ".join(ohne_treffer)))

        ohne_rolle = sorted(
            b.name for b in katalog if b.id not in zugeordnet
        )
        self.stdout.write(self.style.WARNING(
            f"  Im Katalog, aber nicht in der Quelle ({len(ohne_rolle)}): {', '.join(ohne_rolle)}"))
        if opts["trocken"]:
            self.stdout.write(self.style.WARNING("Trockenlauf - nichts gespeichert."))
