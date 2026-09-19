# -*- coding: utf-8 -*-
"""safe_damage -> safe_poke.

Der alte Name bedeutete "Schaden aus sicherer Position", las sich in
einem Spiel mit dem Modus Heist aber wie "Schaden am Safe". Genau diese
Verwechslung stand am Anfang der Heist-Fehldiagnose. Schaden am Safe
heisst `objective_damage`.

Die Migration schreibt den Schluessel in allen JSON-Feldern um, in denen
das Vokabular vorkommt: Brawler-Attribute, Map-Anforderungen und
Modus-Grundanforderungen. Sie ist in beide Richtungen anwendbar.
"""

from django.db import migrations

ALT, NEU = "safe_damage", "safe_poke"


def _tauschen(apps, felder, von, nach):
    for modell_name, feld in felder:
        modell = apps.get_model("drafter", modell_name)
        for zeile in modell.objects.all().iterator():
            werte = getattr(zeile, feld) or {}
            if von in werte:
                werte[nach] = werte.pop(von)
                setattr(zeile, feld, werte)
                zeile.save(update_fields=[feld])


FELDER = (
    ("Brawler", "attributes"),
    ("BrawlMap", "requirements"),
    ("GameMode", "base_requirements"),
)


def vorwaerts(apps, schema_editor):
    _tauschen(apps, FELDER, ALT, NEU)


def rueckwaerts(apps, schema_editor):
    _tauschen(apps, FELDER, NEU, ALT)


class Migration(migrations.Migration):
    dependencies = [("drafter", "0012_sampling_herkunft")]
    operations = [migrations.RunPython(vorwaerts, rueckwaerts)]
