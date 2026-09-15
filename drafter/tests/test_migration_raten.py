# -*- coding: utf-8 -*-
"""Die Uebernahme von win_rate in die neuen Felder - mit echten Zeilen.

Der normale Testlauf baut die Datenbank leer von null auf; die
Datenmigration 0003 laeuft dort ueber null Zeilen und beweist nichts.
Dieser Test faehrt deshalb gezielt auf 0002 zurueck, legt Zeilen im
alten Format an und migriert dann vorwaerts.
"""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

VORHER = [("drafter", "0002_statistik_stichprobe")]
NACHHER = [("drafter", "0004_alte_raten_entfernen")]


class RatenUebernahmeTest(TransactionTestCase):
    def _migriere(self, ziel):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(ziel)
        return executor.loader.project_state(ziel).apps

    def setUp(self):
        apps = self._migriere(VORHER)
        Brawler = apps.get_model("drafter", "Brawler")
        a = Brawler.objects.create(name="Alt A", slug="alt-a")
        b = Brawler.objects.create(name="Alt B", slug="alt-b")
        klein, gross = (a, b) if a.id < b.id else (b, a)

        apps.get_model("drafter", "BrawlerStat").objects.create(
            brawler=a, win_rate=0.58, games=200, wins=116, context_key="alt",
        )
        apps.get_model("drafter", "CounterStat").objects.create(
            brawler=a, enemy=b, advantage=0.3, win_rate=0.61, games=90, context_key="alt",
        )
        apps.get_model("drafter", "SynergyStat").objects.create(
            brawler_a=klein, brawler_b=gross, synergy=0.2, win_rate=0.55, context_key="alt",
        )
        self.apps = self._migriere(NACHHER)

    def tearDown(self):
        # Zurueck auf den neuesten Stand, sonst erben folgende Tests das
        # zurueckgedrehte Schema.
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes("drafter"))

    def test_benutzte_rate_wird_zur_geglaetteten(self):
        stat = self.apps.get_model("drafter", "BrawlerStat").objects.get()
        self.assertAlmostEqual(stat.adjusted_rate, 0.58)
        self.assertAlmostEqual(stat.raw_rate, 116 / 200)
        self.assertEqual(stat.sample_size, 200.0)

    def test_rohmessungen_werden_zur_rohrate(self):
        counter = self.apps.get_model("drafter", "CounterStat").objects.get()
        synergie = self.apps.get_model("drafter", "SynergyStat").objects.get()
        self.assertAlmostEqual(counter.raw_rate, 0.61)
        self.assertAlmostEqual(counter.advantage, 0.3)
        self.assertAlmostEqual(synergie.raw_rate, 0.55)

    def test_kontextschluessel_enthaelt_das_zeitfenster(self):
        for name in ("BrawlerStat", "CounterStat", "SynergyStat"):
            zeile = self.apps.get_model("drafter", name).objects.get()
            self.assertTrue(zeile.context_key.endswith("|w-"), msg=f"{name}: {zeile.context_key}")

    def test_alte_felder_sind_entfernt(self):
        felder = {f.name for f in self.apps.get_model("drafter", "BrawlerStat")._meta.get_fields()}
        self.assertNotIn("win_rate", felder)
        self.assertIn("adjusted_rate", felder)

    def test_migration_ist_umkehrbar(self):
        apps = self._migriere(VORHER)
        stat = apps.get_model("drafter", "BrawlerStat").objects.get()
        self.assertAlmostEqual(stat.win_rate, 0.58)
        self.assertEqual(stat.context_key.count("|"), 3)
