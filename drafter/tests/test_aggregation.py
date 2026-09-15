# -*- coding: utf-8 -*-
"""Aggregation: aus synthetischen Partien werden nachvollziehbare Statistiken.

Alle Partien hier sind konstruiert, um genau eine Eigenschaft der
Rechnung sichtbar zu machen. Gepruefft werden Richtungen und Invarianten
(Bayes zieht zur Mitte, alte Partien zaehlen weniger, ...), keine
auswendig gelernten Zahlen.
"""

from datetime import date, timedelta

from django.core.management import call_command

from drafter import config
from drafter.models.matches import Match
from drafter.models import (
    BrawlerBalanceChange, BrawlerStat, BuildStat, CounterStat, Datenquelle, Patch, SynergyStat,
)
from drafter.services.aggregation.aggregator import Aggregator, ziel_quelle_fuer
from drafter.services.aggregation.rechnung import (
    Zaehler, erwartet_gegeneinander, erwartet_miteinander, vorteil,
)
from drafter.services.confidence import stichproben_confidence
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.registry import hole_stat_provider
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import BASIS, FixtureMixin, partie, serie

STICHTAG = BASIS.date()


class RechnungTest(DrafterTest):
    def test_log5_ist_symmetrisch(self):
        for pa, pb in ((0.6, 0.4), (0.5, 0.5), (0.7, 0.55)):
            self.assertAlmostEqual(
                erwartet_gegeneinander(pa, pb) + erwartet_gegeneinander(pb, pa), 1.0, places=9
            )
        self.assertAlmostEqual(erwartet_gegeneinander(0.5, 0.5), 0.5)

    def test_starker_brawler_wird_gegen_schwachen_erwartet_zu_gewinnen(self):
        self.assertGreater(erwartet_gegeneinander(0.6, 0.4), 0.6)

    def test_neutraler_partner_aendert_die_erwartung_nicht(self):
        self.assertAlmostEqual(erwartet_miteinander(0.5, 0.62), 0.62, places=9)

    def test_vorteil_ist_begrenzt(self):
        self.assertEqual(vorteil(1.0, 0.0), 1.0)
        self.assertEqual(vorteil(0.0, 1.0), -1.0)

    def test_zaehler_trennt_roh_und_gewichtet(self):
        z = Zaehler()
        z.zaehle(True, 1.0)
        z.zaehle(False, 0.25)
        self.assertEqual((z.games, z.wins), (2, 1))
        self.assertAlmostEqual(z.roh, 0.5)
        self.assertAlmostEqual(z.gewicht, 1.25)


class AggregationsTest(FixtureMixin, DrafterTest):
    """Grundlage: kein Patch, fester Stichtag - nichts haengt am Testdatum."""

    def setUp(self):
        super().setUp()
        Patch.objects.all().delete()

    def aggregiere(self, **kwargs):
        kwargs.setdefault("stichtag", STICHTAG)
        kwargs.setdefault("fenster", ["90d"])
        # Partien hinter dem Stichtag faellt kein Zeitfenster auf - sie
        # werden still ignoriert, und ein Test kann aus dem falschen Grund
        # gruen sein. Genau das ist passiert; deshalb hier als Sperre.
        zu_spaet = Match.objects.filter(played_at__date__gt=kwargs["stichtag"]).count()
        self.assertEqual(zu_spaet, 0, "Testpartien liegen hinter dem Stichtag")
        return Aggregator((Datenquelle.SYNTHETIC,), **kwargs).ausfuehren()

    def stat(self, slug, **filter):
        filter.setdefault("window_label", "90d")
        filter.setdefault("rank_pool", "alle")
        # Nur vorbelegen, wenn der Aufrufer nichts zu Map/Modus sagt -
        # sonst entsteht "Map ist leer UND Map ist Undermine".
        if not any(k.startswith("brawl_map") for k in filter):
            filter["brawl_map__isnull"] = True
        if not any(k.startswith("game_mode") for k in filter):
            filter["game_mode__isnull"] = True
        return BrawlerStat.objects.get(brawler__slug=slug, source=Datenquelle.SYNTHETIC, **filter)


class BrawlerRateTest(AggregationsTest):
    def test_winrate_mit_voller_stichprobenangabe(self):
        self.importiere(*serie(10, 7))
        self.aggregiere()
        gale = self.stat("gale")

        self.assertEqual((gale.games, gale.wins), (10, 7))
        self.assertAlmostEqual(gale.raw_rate, 0.7)
        self.assertGreater(gale.adjusted_rate, 0.5)
        self.assertLess(gale.adjusted_rate, 0.7, "Bayes muss zur Mitte ziehen")
        self.assertLessEqual(gale.sample_size, gale.games)
        self.assertAlmostEqual(gale.confidence, stichproben_confidence(gale.sample_size), places=3)
        self.assertEqual((gale.window_start, gale.window_end),
                         (STICHTAG - timedelta(days=89), STICHTAG))
        self.assertEqual(gale.source, Datenquelle.SYNTHETIC)

    def test_kleine_stichprobe_bekommt_weniger_confidence_und_mehr_glaettung(self):
        self.importiere(*serie(3, 3))
        self.importiere(*serie(30, 30, a=("piper", "brock", "colette"), minuten=500))
        self.aggregiere()
        klein, gross = self.stat("gale"), self.stat("piper")

        self.assertEqual(klein.raw_rate, 1.0)
        self.assertEqual(gross.raw_rate, 1.0)
        self.assertLess(klein.confidence, gross.confidence)
        self.assertLess(klein.adjusted_rate, gross.adjusted_rate)

    def test_pickrate(self):
        self.importiere(*serie(4, 2), *serie(4, 2, a=("piper", "brock", "colette"), minuten=100))
        self.aggregiere()
        self.assertAlmostEqual(self.stat("gale").pick_rate, 0.5)
        self.assertAlmostEqual(self.stat("buster").pick_rate, 1.0)

    def test_banrate_nur_ueber_partien_mit_bekannten_bans(self):
        mit_bans = partie(bans=[{"brawler": "piper", "side": "a"}])
        self.importiere(mit_bans, *serie(3, 1, minuten=100))  # drei Partien ohne Ban-Angabe
        self.aggregiere()
        self.assertAlmostEqual(self.stat("buster").ban_rate, 0.0)

        # Piper wurde nie gespielt, aber gebannt - und bekommt trotzdem eine
        # Zeile. Die Rate bezieht sich auf die EINE Partie, deren Quelle
        # Bans kennt, nicht auf alle vier.
        piper = self.stat("piper")
        self.assertAlmostEqual(piper.ban_rate, 1.0)
        self.assertEqual(piper.games, 0)
        self.assertIsNone(piper.adjusted_rate, "Ohne Spiele keine Rate")

    def test_ban_zeile_ohne_rate_ist_fuer_die_engine_keine_auskunft(self):
        self.importiere(partie(bans=[{"brawler": "piper", "side": "a"}]))
        self.aggregiere()
        engine = DraftEngine(self.context(), provider=hole_stat_provider("synthetisch"))
        piper = self.empfehlung(engine.empfehlungen(anzahl=50, mit_details=0), "piper")
        self.assertEqual(piper.komponenten[config.K_META].wert, 0.0)

    def test_map_und_modus_zeilen_entstehen_und_schrumpfen_zur_groeberen_ebene(self):
        self.importiere(*serie(20, 10, minuten=0))
        self.importiere(*serie(3, 3, karte="Undermine", minuten=1000))
        self.aggregiere()
        allgemein = self.stat("gale")
        modus = self.stat("gale", game_mode__isnull=False, brawl_map__isnull=True)
        undermine = self.stat("gale", brawl_map__slug="undermine", game_mode__isnull=False)

        self.assertEqual(modus.game_mode.slug, "gem-grab")
        self.assertEqual(undermine.raw_rate, 1.0)
        # Drei Siege auf Undermine: klar ueber dem Modus - aber weit unter 100 %,
        # weil der Prior die Modusrate ist, nicht 50 %.
        self.assertGreater(undermine.adjusted_rate, modus.adjusted_rate)
        self.assertLess(undermine.adjusted_rate, 0.7)
        self.assertEqual(allgemein.games, 23)

    def test_unentschieden_und_konflikte_zaehlen_nicht(self):
        self.importiere(partie(sieger="draw"))
        self.importiere(partie(minuten=10, sieger="a"))
        self.importiere(partie(minuten=10, sekunden=5, sieger="b"))   # Konflikt zur vorigen
        self.importiere(partie(minuten=20, sieger="a"))
        self.aggregiere()
        self.assertEqual(self.stat("gale").games, 1)


class RangbereichTest(AggregationsTest):
    def test_rangbereiche_werden_getrennt_und_alle_zusammen_gezaehlt(self):
        self.importiere(*serie(4, 4, rank_pool="masters"))
        self.importiere(*serie(6, 0, rank_pool="legendary", minuten=100))
        self.aggregiere(rank_pools=["masters", "legendary", "alle"])
        self.assertEqual(self.stat("gale", rank_pool="masters").games, 4)
        self.assertEqual(self.stat("gale", rank_pool="legendary").games, 6)
        self.assertEqual(self.stat("gale", rank_pool="alle").games, 10)


class ZeitgewichtTest(AggregationsTest):
    def test_alte_partien_zaehlen_weniger(self):
        self.importiere(*serie(10, 10, tage_zurueck=60))              # alte Siege
        self.importiere(*serie(10, 0, tage_zurueck=1, minuten=1000))  # neue Niederlagen
        self.aggregiere()
        gale = self.stat("gale")
        self.assertAlmostEqual(gale.raw_rate, 0.5)
        self.assertLess(gale.adjusted_rate, 0.5, "Neue Niederlagen muessen schwerer wiegen")
        self.assertLess(gale.sample_size, 20)

    def test_gleiche_partien_ergeben_heute_mehr_stichprobe_als_vor_wochen(self):
        self.importiere(*serie(10, 5, tage_zurueck=45))
        self.aggregiere()
        alt = self.stat("gale").sample_size
        self.aggregiere(stichtag=STICHTAG - timedelta(days=45))
        frisch = BrawlerStat.objects.get(
            brawler__slug="gale", window_label="90d", rank_pool="alle",
            brawl_map__isnull=True, game_mode__isnull=True,
        ).sample_size
        self.assertGreater(frisch, alt)


class PatchgewichtTest(AggregationsTest):
    def setUp(self):
        super().setUp()
        self.alt = Patch.objects.create(name="Alt", released_on=STICHTAG - timedelta(days=60))
        self.neu = Patch.objects.create(name="Neu", released_on=STICHTAG - timedelta(days=10))

    def test_balanceaenderung_entwertet_nur_den_veraenderten_brawler(self):
        self.importiere(*serie(10, 5, tage_zurueck=30))
        BrawlerBalanceChange.objects.create(
            patch=self.neu, brawler=self.brawler("gale"),
            severity=BrawlerBalanceChange.Severity.LARGE,
        )
        self.aggregiere()
        gale, belle = self.stat("gale"), self.stat("belle")
        self.assertEqual(gale.games, belle.games)
        self.assertAlmostEqual(
            gale.sample_size, belle.sample_size * config.PATCH_GEWICHT["large"], places=3,
        )
        self.assertLess(gale.confidence, belle.confidence)

    def test_ohne_aenderung_bleibt_das_gewicht(self):
        self.importiere(*serie(10, 5, tage_zurueck=30))
        self.aggregiere()
        self.assertAlmostEqual(self.stat("gale").sample_size, self.stat("belle").sample_size)

    def test_seit_patch_fenster_beginnt_am_patch(self):
        self.importiere(*serie(6, 6, tage_zurueck=30))
        self.importiere(*serie(4, 0, tage_zurueck=2, minuten=1000))
        self.aggregiere(fenster=["seit_patch"])
        gale = self.stat("gale", window_label="seit_patch")
        self.assertEqual(gale.games, 4)
        self.assertEqual(gale.window_start, self.neu.released_on)
        self.assertEqual(gale.patch, self.neu)

    def test_patch_wechsel_veraendert_die_gewichtung_rueckwirkend(self):
        """Ein nachgetragener Patch wirkt nach rebuild_draft_stats auf alte Partien."""
        self.importiere(*serie(10, 5, tage_zurueck=30))
        call_command("rebuild_draft_stats", "--quelle", "synthetisch",
                     "--stichtag", STICHTAG.isoformat(), stdout=_Stumm())
        vorher = self.stat("gale").sample_size

        BrawlerBalanceChange.objects.create(
            patch=self.neu, brawler=self.brawler("gale"),
            severity=BrawlerBalanceChange.Severity.REWORK,
        )
        call_command("rebuild_draft_stats", "--quelle", "synthetisch",
                     "--stichtag", STICHTAG.isoformat(), stdout=_Stumm())
        self.assertLess(self.stat("gale").sample_size, vorher)


class PriorFensterTest(AggregationsTest):
    def test_kurzes_fenster_schrumpft_zur_langfristigen_rate_statt_zu_50_prozent(self):
        self.importiere(*serie(60, 48, tage_zurueck=40))            # langfristig 80 %
        self.importiere(*serie(2, 0, tage_zurueck=1, minuten=5000))  # zwei aktuelle Niederlagen
        self.aggregiere(fenster=["90d", "7d"])
        kurz = self.stat("gale", window_label="7d")
        self.assertEqual(kurz.raw_rate, 0.0)
        self.assertGreater(kurz.adjusted_rate, 0.5,
                           "Zwei Niederlagen duerfen eine lange 80-%-Historie nicht kippen")


class CounterTest(AggregationsTest):
    def _gale_kontert_buster(self):
        # Gales Team schlaegt Busters Team 8 von 10 ...
        self.importiere(*serie(10, 8))
        # ... verliert aber sonst 8 von 10, und Busters Team gewinnt sonst 8 von 10.
        self.importiere(*serie(10, 2, b=("piper", "brock", "colette"), minuten=1000))
        self.importiere(*serie(10, 2, a=("rosa", "poco", "pam"), minuten=2000))

    def test_counter_entsteht_aus_abweichung_von_der_erwartung(self):
        self._gale_kontert_buster()
        self.aggregiere()
        hin = CounterStat.objects.get(brawler__slug="gale", enemy__slug="buster",
                                      game_mode__isnull=True, rank_pool="alle")
        her = CounterStat.objects.get(brawler__slug="buster", enemy__slug="gale",
                                      game_mode__isnull=True, rank_pool="alle")
        self.assertGreater(hin.advantage, 0)
        self.assertLess(her.advantage, 0)
        self.assertAlmostEqual(hin.raw_rate, 0.8)
        self.assertEqual(hin.games, 10)

    def test_ein_starker_brawler_ist_nicht_automatisch_ein_counter(self):
        """Gale gewinnt gegen JEDEN 80 % - gegen Buster ist das nichts Besonderes."""
        self.importiere(*serie(10, 8))
        self.importiere(*serie(10, 8, b=("piper", "brock", "colette"), minuten=1000))
        self.aggregiere()
        zeile = CounterStat.objects.get(brawler__slug="gale", enemy__slug="buster",
                                        game_mode__isnull=True, rank_pool="alle")
        self.assertAlmostEqual(zeile.raw_rate, 0.8)
        self.assertLess(abs(zeile.advantage), 0.2)

    def test_kleine_paarstichprobe_bleibt_nahe_null(self):
        self.importiere(partie(a=("gale", "belle", "max"), b=("mortis", "stu", "surge")))
        self.aggregiere()
        zeile = CounterStat.objects.get(brawler__slug="gale", enemy__slug="mortis",
                                        game_mode__isnull=True, rank_pool="alle")
        self.assertLess(abs(zeile.advantage), 0.1)


class SynergieTest(AggregationsTest):
    def test_synergie_ist_mehr_als_die_summe_der_einzelstaerken(self):
        self.importiere(*serie(10, 8, a=("gale", "belle", "max")))
        self.importiere(*serie(10, 2, a=("gale", "piper", "max"), minuten=1000))
        self.importiere(*serie(10, 2, a=("belle", "piper", "max"), minuten=2000))
        self.aggregiere()

        def synergie(x, y):
            a, b = sorted((self.brawler(x), self.brawler(y)), key=lambda br: br.id)
            return SynergyStat.objects.get(brawler_a=a, brawler_b=b, game_mode__isnull=True,
                                           rank_pool="alle")

        self.assertGreater(synergie("gale", "belle").synergy, 0)
        self.assertLess(synergie("gale", "piper").synergy, synergie("gale", "belle").synergy)
        self.assertTrue(all(z.brawler_a_id < z.brawler_b_id for z in SynergyStat.objects.all()))


class BuildStatTest(AggregationsTest):
    def test_builds_werden_nur_gezaehlt_wenn_vorhanden(self):
        mit = lambda gadget: {"brawler": "gale", "build": {"gadget": gadget, "gears": ["damage-gear"]}}
        self.importiere(*[partie(a=(mit("twister"), "belle", "max"), sieger="a", minuten=i * 5)
                          for i in range(8)])
        self.importiere(*[partie(a=(mit("spring-ejector"), "belle", "max"), sieger="b",
                                 minuten=1000 + i * 5) for i in range(8)])
        self.importiere(*serie(5, 2, minuten=3000))   # ohne Build-Angabe
        self.aggregiere()

        twister = BuildStat.objects.get(brawler__slug="gale", item_slug="twister",
                                        game_mode__isnull=True, rank_pool="alle")
        feder = BuildStat.objects.get(brawler__slug="gale", item_slug="spring-ejector",
                                      game_mode__isnull=True, rank_pool="alle")
        self.assertEqual(twister.games, 8)
        self.assertIsNotNone(twister.item, "Katalogtreffer muss verknuepft werden")
        self.assertGreater(twister.advantage, feder.advantage)
        gear = BuildStat.objects.get(brawler__slug="gale", item_slug="damage-gear",
                                     game_mode__isnull=True, rank_pool="alle")
        self.assertEqual(gear.games, 16)
        self.assertEqual(gear.item.brawler, None)

    def test_unbekannter_gegenstand_bleibt_erhalten(self):
        self.importiere(partie(a=({"brawler": "gale", "build": {"gadget": "gibt-es-nicht"}},
                                  "belle", "max")))
        self.aggregiere()
        zeile = BuildStat.objects.get(item_slug="gibt-es-nicht", game_mode__isnull=True,
                                      rank_pool="alle")
        self.assertIsNone(zeile.item)

    def test_ohne_builds_keine_build_statistik(self):
        self.importiere(*serie(5, 3))
        self.aggregiere()
        self.assertFalse(BuildStat.objects.exists())


class IdempotenzUndIsolationTest(AggregationsTest):
    def test_zweimal_aggregieren_ergibt_dasselbe(self):
        self.importiere(*serie(10, 6))
        self.aggregiere()
        erste = sorted(BrawlerStat.objects.filter(source=Datenquelle.SYNTHETIC)
                       .values_list("context_key", "brawler_id", "adjusted_rate"))
        self.aggregiere()
        zweite = sorted(BrawlerStat.objects.filter(source=Datenquelle.SYNTHETIC)
                        .values_list("context_key", "brawler_id", "adjusted_rate"))
        self.assertEqual(erste, zweite)

    def test_demo_daten_bleiben_unberuehrt(self):
        vorher = {m.__name__: m.objects.filter(source=Datenquelle.DEMO).count()
                  for m in (BrawlerStat, CounterStat, SynergyStat)}
        self.importiere(*serie(10, 6))
        self.aggregiere(fenster=None)
        call_command("rebuild_draft_stats", "--quelle", "synthetisch",
                     "--stichtag", STICHTAG.isoformat(), stdout=_Stumm())
        nachher = {m.__name__: m.objects.filter(source=Datenquelle.DEMO).count()
                   for m in (BrawlerStat, CounterStat, SynergyStat)}
        self.assertEqual(vorher, nachher)

    def test_synthetisch_wird_nie_mit_echten_quellen_gemischt(self):
        with self.assertRaises(ValueError):
            ziel_quelle_fuer((Datenquelle.SYNTHETIC, Datenquelle.FIXTURE))
        with self.assertRaises(ValueError):
            ziel_quelle_fuer((Datenquelle.DEMO,))
        self.assertEqual(ziel_quelle_fuer((Datenquelle.FIXTURE, Datenquelle.API)),
                         Datenquelle.AGGREGATED)

    def test_aggregations_kommando(self):
        self.importiere(*serie(6, 4))
        call_command("aggregate_brawl_stats", "--quelle", "synthetisch", "--fenster", "90d",
                     "--rank-pool", "alle", "--stichtag", STICHTAG.isoformat(), stdout=_Stumm())
        self.assertEqual(self.stat("gale").games, 6)


class EndeZuEndeTest(AggregationsTest):
    def test_import_aggregation_engine_ohne_api(self):
        """Fixture -> Import -> Aggregation -> Provider -> Engine, komplett offline."""
        from pathlib import Path
        from django.conf import settings
        from drafter.services.ingest.importer import MatchImporter
        from drafter.services.providers.fixture import FixtureDataProvider

        pfad = Path(settings.BASE_DIR) / "drafter" / "testdaten" / "synthetisch_ranked.json"
        MatchImporter(FixtureDataProvider(pfad)).ausfuehren()
        Aggregator((Datenquelle.SYNTHETIC,), stichtag=date(2026, 9, 10)).ausfuehren()

        provider = hole_stat_provider("synthetisch")
        self.assertTrue(provider.status().verfuegbar)
        engine = DraftEngine(self.context(gegner=["buster"]), provider=provider)
        daten = engine.als_dict()

        self.assertTrue(daten["empfehlungen"])
        self.assertEqual(daten["datenlage"]["quelle"], "synthetisch")
        self.assertTrue(daten["datenlage"]["nur_demo"], "Synthetisch ist nicht gemessen")
        self.assertEqual(hole_stat_provider("auto").name, "demo")


class _Stumm:
    def write(self, *args, **kwargs):
        pass

    def flush(self):
        pass
