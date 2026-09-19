# -*- coding: utf-8 -*-
"""Beobachtete Ranked-Nutzung je Map.

Der Drafter leitete seinen Mapkatalog aus `is_active` ab - einem von Hand
gesetzten Feld, das am 2026-09-19 noch den acht Maps des Demo-Seeds
entsprach. Gespielt wurde auf 30 Maps. Die beiden neuen Felder halten
fest, was die importierten Partien zeigen; gerechnet werden sie von
`aktualisiere_ranked_maps`, nie von Hand gesetzt.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("drafter", "0013_safe_poke")]

    operations = [
        migrations.AddField(
            model_name="brawlmap",
            name="observed_ranked_games",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="brawlmap",
            name="last_seen_ranked",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
