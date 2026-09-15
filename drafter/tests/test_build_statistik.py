# -*- coding: utf-8 -*-
"""Build-Statistiken: wirken nur, wenn es sie gibt - und dann nachvollziehbar.

Die Datensaetze kommen aus einer Momentaufnahme im Speicher, nicht aus
der Datenbank. Ob eine Build-Statistik aus einer Aggregation oder einem
anderen Provider stammt, darf fuer die Build-Empfehlung keine Rolle
spielen.
"""

from drafter import config
from drafter.models import BrawlerItem, Datenquelle
from drafter.services import builds
from drafter.services.daten import Datenraum
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.demo import DemoDataProvider
from drafter.services.providers.records import ART_BUILD, StatRecord
from drafter.services.providers.snapshot import SnapshotStatProvider
from drafter.tests.basis import DrafterTest


class BuildStatistikTest(DrafterTest):
    def _provider(self, *zusaetzlich):
        basis = SnapshotStatProvider.von(DemoDataProvider())._records
        return SnapshotStatProvider(list(basis) + list(zusaetzlich), name="mit-builds")

    def _raum(self, ctx, *zusaetzlich):
        return Datenraum(
            brawl_map=ctx.brawl_map, game_mode=ctx.game_mode, provider=self._provider(*zusaetzlich),
        ).laden()

    def _statistik(self, slug, vorteil, confidence, quelle=Datenquelle.FIXTURE, spiele=500):
        return StatRecord(
            art=ART_BUILD, brawler_id=self.brawler("gale").id, item_kind="gadget", item_slug=slug,
            games=spiele, advantage=vorteil, confidence=confidence, source=quelle, adjusted_rate=0.5,
        )

    def _punkte(self, ctx, raum, slug):
        gale = self.brawler("gale")
        gadgets = list(BrawlerItem.objects.filter(brawler=gale, kind="gadget").prefetch_related("rules"))
        for punkte, gegenstand, gruende, _ in builds._bewerte(gadgets, gale, ctx, raum):
            if gegenstand.slug == slug:
                return punkte, gruende
        self.fail(f"{slug} nicht im Katalog")

    # --- Ohne Statistik aendert sich nichts ------------------------------
    def test_ohne_build_statistik_zaehlen_nur_die_regeln(self):
        ctx = self.context()
        mit_raum, _ = self._punkte(ctx, self._raum(ctx), "spring-ejector")
        ohne_raum, _ = self._punkte(ctx, None, "spring-ejector")
        self.assertEqual(mit_raum, ohne_raum)

    def test_demo_engine_liefert_rein_regelbasierte_builds(self):
        engine = DraftEngine(self.context(gegner=["bull"]))
        build = engine.detail(self.brawler("gale")).build
        self.assertFalse(build["statistik"])
        self.assertEqual(build["quelle"], "regeln")

    # --- Mit Statistik: Richtung, Staerke, Deckel --------------------------
    def test_positive_statistik_hebt_negative_senkt(self):
        ctx = self.context()
        vorher, _ = self._punkte(ctx, self._raum(ctx), "spring-ejector")
        hoch, gruende = self._punkte(
            ctx, self._raum(ctx, self._statistik("spring-ejector", 0.5, 0.9)), "spring-ejector")
        tief, _ = self._punkte(
            ctx, self._raum(ctx, self._statistik("spring-ejector", -0.5, 0.9)), "spring-ejector")
        self.assertGreater(hoch, vorher)
        self.assertLess(tief, vorher)
        self.assertTrue(any("500 vergleichbaren Partien über" in g for g in gruende))

    def test_einfluss_waechst_mit_der_confidence(self):
        ctx = self.context()
        vorher, _ = self._punkte(ctx, self._raum(ctx), "spring-ejector")
        wenig, _ = self._punkte(
            ctx, self._raum(ctx, self._statistik("spring-ejector", 0.5, 0.1)), "spring-ejector")
        viel, _ = self._punkte(
            ctx, self._raum(ctx, self._statistik("spring-ejector", 0.5, 0.9)), "spring-ejector")
        self.assertLess(wenig - vorher, viel - vorher)

    def test_einfluss_ist_gedeckelt(self):
        ctx = self.context()
        vorher, _ = self._punkte(ctx, self._raum(ctx), "spring-ejector")
        maximal, _ = self._punkte(
            ctx, self._raum(ctx, self._statistik("spring-ejector", 1.0, 1.0)), "spring-ejector")
        self.assertLessEqual(maximal - vorher, config.BUILD_STAT_EINFLUSS + 1e-9)

    def test_nicht_gemessene_statistik_wird_benannt(self):
        ctx = self.context()
        _, gruende = self._punkte(
            ctx, self._raum(ctx, self._statistik("twister", 0.3, 0.5, quelle=Datenquelle.SYNTHETIC)),
            "twister")
        self.assertTrue(any("keine Messung" in g for g in gruende))

    # --- Durch die Engine -------------------------------------------------
    def test_engine_reicht_build_statistik_durch(self):
        provider = self._provider(self._statistik("twister", 0.4, 0.8))
        engine = DraftEngine(self.context(gegner=["bull"]), provider=provider)
        build = engine.detail(self.brawler("gale")).build
        self.assertTrue(build["statistik"])
        self.assertEqual(build["quelle"], "regeln+statistik")
        self.assertTrue(any("Partien" in g for g in build["gruende"]))
