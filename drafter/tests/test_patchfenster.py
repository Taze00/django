# -*- coding: utf-8 -*-
"""Patchdatum und Statistikfenster: geraten wird nichts, verschwiegen auch nichts.

Am 2026-09-19 sprang das Patchdatum auf einen Tag NACH der juengsten
gesammelten Partie. `seed_brawl_data` schrieb `released_on = heute` bei
JEDEM Lauf, nicht nur beim Anlegen. Folge: das Fenster "seit Patch" war
leer, die Aggregation schrieb dafuer keine Zeile mehr, und die Engine
fiel still auf sieben Tage zurueck - die Oberflaeche behauptete weiter
nichts, aber sie sagte es eben auch nicht.

Zwei Regeln, beide hier festgehalten:

1. Ein Patchdatum ist **externe** Information. Es wird nicht aus der
   ersten Partie, dem letzten Collector-Lauf oder dem heutigen Datum
   abgeleitet. Ohne gepflegte Quelle gilt es als *unbestaetigt*.
2. Der Fallback auf ein anderes Fenster ist richtig - aber er muss
   **sichtbar** sein.
"""

import io
from datetime import date, timedelta

from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from drafter import config
from drafter.models import (
    Brawler, BrawlerBalanceChange, CounterStat, Datenquelle, Patch,
)
from drafter.services.analyse import als_dict
from drafter.services.draft_engine import DraftEngine
from drafter.tests.basis import DrafterTest


class SeedDatumTest(DrafterTest):
    """Ein Seed frischt Demo-Daten auf - er verschiebt keine Zeitgrenze."""

    def test_seed_legt_platzhalter_als_unbestaetigt_an(self):
        Patch.objects.all().delete()
        call_command("seed_brawl_data", verbosity=0)
        patch = Patch.objects.get(name="Demo-Patch")
        self.assertFalse(patch.datum_bestaetigt)
        self.assertIn("Platzhalter", patch.datum_quelle)
        self.assertIn("unbestätigt", patch.datumslage)

    def test_zweiter_seed_laesst_das_datum_stehen(self):
        """Der eigentliche Fehler vom 2026-09-19."""
        patch = Patch.objects.get(name="Demo-Patch")
        patch.released_on = date(2026, 9, 15)
        patch.save(update_fields=["released_on"])

        call_command("seed_brawl_data", verbosity=0)

        patch.refresh_from_db()
        self.assertEqual(patch.released_on, date(2026, 9, 15),
                         "der Seed darf das Patchdatum nicht auf heute ziehen")

    def test_ein_gepflegtes_datum_ueberlebt_den_seed(self):
        patch = Patch.objects.get(name="Demo-Patch")
        patch.released_on = date(2026, 9, 17)
        patch.datum_bestaetigt = True
        patch.datum_quelle = "Patch Notes"
        patch.save()

        call_command("seed_brawl_data", verbosity=0)

        patch.refresh_from_db()
        self.assertEqual(patch.released_on, date(2026, 9, 17))
        self.assertTrue(patch.datum_bestaetigt)

    def test_seed_haelt_den_platzhalter_aktuell(self):
        """Was der Seed weiter darf: `is_current` und die Beschreibung."""
        Patch.objects.filter(name="Demo-Patch").update(is_current=False)
        call_command("seed_brawl_data", verbosity=0)
        self.assertTrue(Patch.objects.get(name="Demo-Patch").is_current)


class PatchSetzenTest(DrafterTest):
    def laufen(self, **o):
        ausgabe = io.StringIO()
        call_command("patch_setzen", stdout=ausgabe, **o)
        return ausgabe.getvalue()

    def test_ohne_datum_wird_nichts_geraten(self):
        with self.assertRaises(CommandError) as fehler:
            self.laufen(name="Herbst")
        self.assertIn("released-on", str(fehler.exception))
        self.assertIn("NICHT geraten", str(fehler.exception))

    def test_datum_ohne_quelle_bleibt_unbestaetigt(self):
        self.laufen(name="Herbst", datum="2026-09-17")
        patch = Patch.objects.get(name="Herbst")
        self.assertEqual(patch.released_on, date(2026, 9, 17))
        self.assertFalse(patch.datum_bestaetigt)

    def test_mit_quelle_gilt_es_als_bestaetigt(self):
        self.laufen(name="Herbst", datum="2026-09-17", quelle="Patch Notes vom 16.09.")
        patch = Patch.objects.get(name="Herbst")
        self.assertTrue(patch.datum_bestaetigt)
        self.assertIn("Patch Notes", patch.datumslage)

    def test_unsinniges_datum_wird_abgewiesen(self):
        with self.assertRaises(CommandError):
            self.laufen(name="Herbst", datum="irgendwann")

    def test_trockenlauf_schreibt_nichts(self):
        text = self.laufen(name="Herbst", datum="2026-09-17", trocken=True)
        self.assertIn("[trocken]", text)
        self.assertFalse(Patch.objects.filter(name="Herbst").exists())


class PatchwechselTest(DrafterTest):
    """Ein Wechsel darf nichts wegwerfen."""

    def setUp(self):
        self.alt = Patch.objects.get(name="Demo-Patch")
        self.alt.released_on = date(2026, 9, 10)
        self.alt.save(update_fields=["released_on"])
        BrawlerBalanceChange.objects.create(
            brawler=self.brawler("gale"), patch=self.alt,
            severity=BrawlerBalanceChange.Severity.SMALL)
        CounterStat.objects.create(
            brawler=self.brawler("gale"), enemy=self.brawler("bull"),
            advantage=0.2, patch=self.alt, source=Datenquelle.API,
            window_label="30d", games=50)

    def test_alter_patch_bleibt_mit_allem_dran(self):
        call_command("patch_setzen", name="Herbst", datum="2026-09-17",
                     quelle="Notes", aktivieren=True, stdout=io.StringIO())

        self.alt.refresh_from_db()
        self.assertTrue(Patch.objects.filter(pk=self.alt.pk).exists(),
                        "der alte Patch bleibt historisch stehen")
        self.assertEqual(self.alt.released_on, date(2026, 9, 10))
        self.assertFalse(self.alt.is_current)
        self.assertEqual(BrawlerBalanceChange.objects.filter(patch=self.alt).count(), 1)
        self.assertEqual(CounterStat.objects.filter(patch=self.alt).count(), 1,
                         "alte Statistiken werden nicht geloescht")

    def test_genau_ein_aktueller_patch(self):
        call_command("patch_setzen", name="Herbst", datum="2026-09-17",
                     aktivieren=True, stdout=io.StringIO())
        self.assertEqual(Patch.objects.filter(is_current=True).count(), 1)
        self.assertEqual(Patch.aktueller().name, "Herbst")

    def test_neue_grenze_gilt_fuer_neue_aggregationen(self):
        """`_zeitraum('seit_patch')` folgt dem aktiven Patch."""
        from drafter.services.aggregation.aggregator import Aggregator
        call_command("patch_setzen", name="Herbst", datum="2026-09-17",
                     aktivieren=True, stdout=io.StringIO())
        agg = Aggregator((Datenquelle.SYNTHETIC,), stichtag=date(2026, 9, 20))
        self.assertEqual(agg._zeitraum("seit_patch"),
                         (date(2026, 9, 17), date(2026, 9, 20)))

    def test_ohne_patch_gibt_es_kein_patchfenster(self):
        from drafter.services.aggregation.aggregator import Aggregator
        Patch.objects.all().delete()
        agg = Aggregator((Datenquelle.SYNTHETIC,), stichtag=date(2026, 9, 20))
        self.assertIsNone(agg._zeitraum("seit_patch"),
                          "ohne Patch wird kein Datum erfunden")


class FensterLageTest(DrafterTest):
    """Der Fallback ist erlaubt - aber er muss dastehen."""

    def raum(self):
        engine = DraftEngine(self.context(karte="hard-rock-mine"))
        engine.empfehlungen(anzahl=3)
        return engine.raum

    def messe(self, fenster, anzahl=40):
        """Gemessene Counterzeilen in einem bestimmten Zeitfenster."""
        gale, bull = self.brawler("gale"), self.brawler("bull")
        a, b = sorted((gale, bull), key=lambda x: x.id)
        CounterStat.objects.create(
            brawler=a, enemy=b, advantage=0.15, source=Datenquelle.API,
            window_label=fenster, games=anzahl, sample_size=float(anzahl),
            raw_rate=0.55, adjusted_rate=0.54, confidence=0.4)

    def test_ohne_messung_bleibt_die_auskunft_leer(self):
        lage = self.raum().fenster_lage()
        self.assertIsNone(lage["hauptfenster"])
        self.assertEqual(lage["verwendet"], [])

    def test_benutztes_fenster_steht_drin(self):
        self.messe("7d")
        lage = self.raum().fenster_lage()
        self.assertEqual(lage["hauptfenster"], "7d")
        self.assertEqual(lage["verwendet"][0]["zeilen"], 1)

    def test_fehlendes_patchfenster_wird_begruendet(self):
        """Der Fall vom 2026-09-19: 'seit Patch' existiert gar nicht."""
        self.messe("7d")
        lage = self.raum().fenster_lage()
        self.assertEqual(lage["bevorzugt"], "seit_patch")
        self.assertFalse(lage["bevorzugt_vorhanden"])
        self.assertIn("seit_patch", lage["grund"])
        self.assertIn("7d", lage["grund"])

    def test_vorhandenes_patchfenster_wird_bevorzugt_und_nicht_begruendet(self):
        self.messe("seit_patch")
        lage = self.raum().fenster_lage()
        self.assertEqual(lage["hauptfenster"], "seit_patch")
        self.assertTrue(lage["bevorzugt_vorhanden"])
        self.assertEqual(lage["grund"], "", "kein Grund noetig, wenn nichts abweicht")

    def test_die_analyse_traegt_die_fensterlage_mit(self):
        self.messe("7d")
        ctx = self.context(karte="hard-rock-mine")
        engine = DraftEngine(ctx)
        empfehlung, rang, anzahl = engine.analyse(self.brawler("mortis"))
        daten = als_dict(empfehlung, rang, anzahl, ctx, engine.raum)
        self.assertIn("statistikfenster", daten)
        self.assertEqual(daten["statistikfenster"]["hauptfenster"], "7d")

    def test_gepflegte_zeilen_zaehlen_nicht_als_fenster(self):
        """Demo-Zeilen haben kein Fenster - sie duerfen keins vortaeuschen."""
        lage = self.raum().fenster_lage()
        self.assertNotIn("", [v["fenster"] for v in lage["verwendet"]])
