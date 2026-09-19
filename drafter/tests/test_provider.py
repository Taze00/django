# -*- coding: utf-8 -*-
"""Provider: austauschbar, ehrlich in der Quelle, und die Engine merkt nichts."""

import json
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from drafter.models import BrawlerStat, Datenquelle
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import DatenbankStatProvider
from drafter.services.providers.demo import DemoDataProvider
from drafter.services.providers.records import StatAnfrage, StatRecord
from drafter.services.providers.registry import hole_stat_provider
from drafter.services.providers.snapshot import SnapshotStatProvider
from drafter.tests.basis import DrafterTest

LAGEN = (
    dict(),
    dict(gegner=["bull"], first_pick=False),
    dict(eigene=["gale"], gegner=["bull", "tick"]),
    dict(eigene=["gale", "belle"], gegner=["buster", "gene", "tick"]),
    dict(eigene=["gale", "belle", "max"], gegner=["buster", "gene", "tick"]),
)


def _vergleichbar(daten):
    """Antwort ohne den Providernamen - der unterscheidet sich naturgemaess."""
    daten = json.loads(json.dumps(daten, default=str))
    for block in (daten.get("datenlage"), (daten.get("endanalyse") or {}).get("datenlage")):
        if block:
            block.pop("quelle", None)
    return daten


class DemoProviderTest(DrafterTest):
    def test_liest_nur_gepflegte_quellen(self):
        BrawlerStat.objects.create(
            brawler=self.brawler("gale"), adjusted_rate=0.9, source=Datenquelle.FIXTURE,
        )
        records = DemoDataProvider().brawler_stats(StatAnfrage())
        self.assertTrue(records)
        self.assertTrue(all(r.source in (Datenquelle.DEMO, Datenquelle.MANUAL) for r in records))

    def test_datensaetze_tragen_den_vollen_kontext(self):
        record = DemoDataProvider().brawler_stats(StatAnfrage())[0]
        for feld in ("games", "wins", "sample_size", "raw_rate", "adjusted_rate",
                     "source", "window_start", "window_end", "window_label",
                     "patch_id", "rank_pool", "confidence"):
            self.assertTrue(hasattr(record, feld), msg=feld)
        self.assertTrue(record.is_demo)

    def test_aus_model_kennt_jede_statistikart(self):
        with self.assertRaises(TypeError):
            StatRecord.aus_model(self.brawler("gale"))


class AustauschbarkeitTest(DrafterTest):
    """Dieselben Datensaetze aus einem anderen Provider -> dieselben Empfehlungen."""

    def test_engine_identisch_mit_momentaufnahme_des_demo_providers(self):
        demo = DemoDataProvider()
        kopie = SnapshotStatProvider.von(demo)
        for lage in LAGEN:
            ctx = self.context(**lage)
            mit_demo = DraftEngine(ctx, provider=demo).als_dict()
            mit_kopie = DraftEngine(ctx, provider=kopie).als_dict()
            self.assertEqual(_vergleichbar(mit_demo), _vergleichbar(mit_kopie), msg=str(lage))

    def test_standardweg_ist_ohne_messdaten_der_demo_provider(self):
        for lage in LAGEN:
            ctx = self.context(**lage)
            self.assertEqual(
                _vergleichbar(DraftEngine(ctx).als_dict()),
                _vergleichbar(DraftEngine(ctx, provider=DemoDataProvider()).als_dict()),
            )

    def test_endanalyse_identisch_unabhaengig_vom_provider(self):
        ctx = self.context(eigene=["gale", "belle", "max"], gegner=["buster", "gene", "tick"])
        demo = DemoDataProvider()
        self.assertEqual(
            _vergleichbar(DraftEngine(ctx, provider=demo).endanalyse()),
            _vergleichbar(DraftEngine(ctx, provider=SnapshotStatProvider.von(demo)).endanalyse()),
        )

    def test_engine_fragt_mit_momentaufnahme_keine_stat_tabellen_ab(self):
        """Der Beweis, dass die Engine nicht an den Tabellen haengt."""
        kopie = SnapshotStatProvider.von(DemoDataProvider())
        ctx = self.context(eigene=["gale"], gegner=["bull", "tick"])
        with CaptureQueriesContext(connection) as abfragen:
            DraftEngine(ctx, provider=kopie).als_dict()
        tabellen = ("drafter_brawlerstat", "drafter_counterstat",
                    "drafter_synergystat", "drafter_buildstat")
        for abfrage in abfragen.captured_queries:
            for tabelle in tabellen:
                self.assertNotIn(tabelle, abfrage["sql"])

    def test_engine_fragt_nie_rohmatches_ab(self):
        for lage in LAGEN:
            with CaptureQueriesContext(connection) as abfragen:
                engine = DraftEngine(self.context(**lage))
                engine.als_dict()
                if engine.ctx.own_picks:
                    engine.endanalyse()
            for abfrage in abfragen.captured_queries:
                for tabelle in ("drafter_match", "drafter_rawpayload"):
                    self.assertNotIn(f'"{tabelle}', abfrage["sql"])

    def test_fehlende_statistik_faellt_auf_heuristik(self):
        leer = SnapshotStatProvider([], name="leer")
        engine = DraftEngine(self.context(gegner=["bull"]), provider=leer)
        empfehlungen = engine.empfehlungen()
        self.assertTrue(empfehlungen, "Ohne Statistiken muss die Engine trotzdem empfehlen")
        self.assertTrue(engine.raum.nur_demo)
        quellen = {g.quelle for e in empfehlungen for g in e.gruende(True) + e.gruende(False)}
        self.assertNotIn("daten", quellen)


class QuellenEhrlichkeitTest(DrafterTest):
    def test_gemessene_datensaetze_heben_den_demo_status_auf(self):
        gemessen = SnapshotStatProvider(
            [r.mit(source=Datenquelle.FIXTURE)
             for r in SnapshotStatProvider.von(DemoDataProvider())._records],
            name="gemessen-test",
        )
        engine = DraftEngine(self.context(gegner=["bull"]), provider=gemessen)
        daten = engine.als_dict()
        self.assertFalse(engine.raum.nur_demo)
        self.assertEqual(daten["datenlage"]["quelle"], "gemessen-test")
        self.assertNotIn("Demo", daten["datenlage"]["hinweis"])

    def test_synthetische_datensaetze_bleiben_gedeckelt(self):
        synthetisch = SnapshotStatProvider(
            [r.mit(source=Datenquelle.SYNTHETIC)
             for r in SnapshotStatProvider.von(DemoDataProvider())._records],
        )
        engine = DraftEngine(self.context(gegner=["bull"]), provider=synthetisch)
        self.assertTrue(engine.raum.nur_demo)
        for e in engine.empfehlungen(anzahl=50, mit_details=0):
            self.assertLessEqual(e.confidence, 0.35)


class RegistryTest(DrafterTest):
    def test_auto_nimmt_demo_ohne_messdaten(self):
        self.assertEqual(hole_stat_provider("auto").name, "demo")

    def test_auto_nimmt_messdaten_erst_nach_freigabe(self):
        from unittest import mock

        from drafter import config

        BrawlerStat.objects.create(
            brawler=self.brawler("gale"), adjusted_rate=0.55, source=Datenquelle.FIXTURE,
        )
        with mock.patch.object(config, "GEMESSENE_STATS_FREIGEGEBEN", False):
            self.assertEqual(
                hole_stat_provider("auto").name, "demo",
                "Ohne Freigabe bleibt die Seite bei Demo, auch wenn Messwerte vorliegen",
            )
        with mock.patch.object(config, "GEMESSENE_STATS_FREIGEGEBEN", True):
            self.assertEqual(hole_stat_provider("auto").name, "gemessen")

    def test_auto_nimmt_synthetische_daten_nie(self):
        BrawlerStat.objects.create(
            brawler=self.brawler("gale"), adjusted_rate=0.55, source=Datenquelle.SYNTHETIC,
        )
        self.assertEqual(hole_stat_provider("auto").name, "demo")

    def test_ausdrueckliche_wahl(self):
        self.assertEqual(hole_stat_provider("demo").name, "demo")
        self.assertEqual(hole_stat_provider("synthetisch").name, "synthetisch")

    def test_unbekannter_name_ist_ein_fehler(self):
        with self.assertRaises(ValueError):
            hole_stat_provider("gibtsnicht")

    def test_leerer_provider_meldet_sich_ohne_absturz(self):
        status = DatenbankStatProvider((Datenquelle.API,)).status()
        self.assertFalse(status.verfuegbar)
        self.assertIn("api", status.grund)


class DatenhinweisTest(DrafterTest):
    """Der Hinweis ueber dem Draft muss sagen, womit gerechnet wird.

    Bis zum 2026-09-20 stand dort ein fest verdrahteter Demo-Satz. Er
    blieb stehen, als die Seite laengst mit gemessenen Statistiken
    rechnete - die Seite behauptete also das Gegenteil dessen, was sie
    tat. Ein falscher Herkunftshinweis ist schlimmer als keiner: er
    entwertet genau die Unterscheidung, fuer die `Datenquelle` da ist.
    """

    def seite(self):
        return self.client.get(reverse("drafter:draft")).content.decode()

    def test_ohne_messung_steht_dort_demo(self):
        self.assertEqual(hole_stat_provider().name, "demo")
        self.assertIn("Demo-Daten", self.seite())

    def test_mit_messung_steht_dort_gemessen(self):
        BrawlerStat.objects.create(
            brawler=self.brawler("gale"), adjusted_rate=0.55, source=Datenquelle.API,
        )
        self.assertNotEqual(hole_stat_provider().name, "demo")
        seite = self.seite()
        self.assertIn("Gemessene Statistiken", seite)
        self.assertNotIn("<strong>Demo-Daten</strong>", seite)

    def test_der_hinweis_folgt_dem_provider_nicht_der_vorlage(self):
        """Kein Satz in der Vorlage darf die Quelle behaupten."""
        vorlage = Path(settings.BASE_DIR) / "templates" / "drafter" / "draft.html"
        text = vorlage.read_text(encoding="utf-8")
        hinweis = text.split('class="hinweis-demo"')[1].split("</p>")[0]
        self.assertIn("datenlage.gemessen", hinweis)
