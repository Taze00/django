# -*- coding: utf-8 -*-
"""Mapnamen sind keine Identitaet.

Supercell vergibt denselben Mapnamen mehrfach mit verschiedenen IDs -
beobachtet am 2026-09-18 bei 'Siberian Stand Off', 'Stockpile Stadium'
und 'Insane Streamer'. Die bisherige Eindeutigkeit ueber (name, mode)
verhinderte, dass die zweite ueberhaupt gespeichert werden konnte: der
Import meldete einen Widerspruch und verwarf die Partie-Zuordnung.
Eindeutig bleibt `external_id`.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("drafter", "0014_beobachtete_ranked_maps")]

    operations = [
        migrations.AlterUniqueTogether(name="brawlmap", unique_together=set()),
    ]
