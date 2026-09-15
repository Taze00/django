# -*- coding: utf-8 -*-
"""Bestehende Raten in die neuen Felder uebernehmen.

Zwischen 0002 (neue Felder) und 0004 (alte Felder weg). Getrennt, damit
keine Zahl verloren geht: erst kopieren, dann loeschen.

- BrawlerStat.win_rate war der BENUTZTE Wert  -> adjusted_rate
- CounterStat/SynergyStat.win_rate war die ROHMESSUNG -> raw_rate
- context_key bekommt das Zeitfenster als letzten Bestandteil

Die Schluesselberechnung steht hier ausgeschrieben statt ueber
`berechne_context_key()`: historische Modelle in Migrationen kennen
keine eigenen Methoden. Das Format muss mit StatBasis uebereinstimmen.
"""

from django.db import migrations


def _schluessel(zeile, mit_fenster=True):
    teile = [
        f"m{zeile.game_mode_id or 0}",
        f"k{zeile.brawl_map_id or 0}",
        f"p{zeile.patch_id or 0}",
        f"r{zeile.rank_pool or '-'}",
    ]
    if mit_fenster:
        teile.append(f"w{zeile.window_label or '-'}")
    return "|".join(teile)


def vorwaerts(apps, schema_editor):
    for name in ("BrawlerStat", "CounterStat", "SynergyStat"):
        modell = apps.get_model("drafter", name)
        geaendert = []
        for zeile in modell.objects.all():
            if name == "BrawlerStat":
                zeile.adjusted_rate = zeile.win_rate
                if zeile.games:
                    zeile.raw_rate = zeile.wins / zeile.games
            else:
                zeile.raw_rate = zeile.win_rate
            # Ohne Gewichtsinformation ist die ungewichtete Anzahl die
            # ehrlichste Schaetzung der effektiven Stichprobe.
            zeile.sample_size = float(zeile.games)
            zeile.context_key = _schluessel(zeile)
            geaendert.append(zeile)
        modell.objects.bulk_update(
            geaendert, ["adjusted_rate", "raw_rate", "sample_size", "context_key"]
        )


def rueckwaerts(apps, schema_editor):
    for name in ("BrawlerStat", "CounterStat", "SynergyStat"):
        modell = apps.get_model("drafter", name)
        geaendert = []
        for zeile in modell.objects.all():
            if name == "BrawlerStat":
                zeile.win_rate = zeile.adjusted_rate if zeile.adjusted_rate is not None else 0.5
            else:
                zeile.win_rate = zeile.raw_rate
            zeile.context_key = _schluessel(zeile, mit_fenster=False)
            geaendert.append(zeile)
        modell.objects.bulk_update(geaendert, ["win_rate", "context_key"])


class Migration(migrations.Migration):
    dependencies = [
        ("drafter", "0002_statistik_stichprobe"),
    ]

    operations = [
        migrations.RunPython(vorwaerts, rueckwaerts),
    ]
