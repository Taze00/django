# -*- coding: utf-8 -*-
"""Counter: gepflegt darf asymmetrisch sein, gemessen zaehlt genau einmal.

Die Datensaetze kommen fuer die Rechenweg-Tests aus einer Momentaufnahme
im Speicher - so ist jeder Test auf genau die Zeilen beschraenkt, um die
es geht. Die Aggregations-Tests pruefen dasselbe Ende-zu-Ende.
"""

from django.db import IntegrityError, transaction

from drafter import config
from drafter.models import CounterStat, Datenquelle
from drafter.services.aggregation.aggregator import Aggregator
from drafter.services.counters import heuristischer_vorteil, komponente, vorteil
from drafter.services.daten import Datenraum
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.records import ART_COUNTER, StatRecord
from drafter.services.providers.registry import hole_stat_provider
from drafter.services.providers.snapshot import SnapshotStatProvider
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import BASIS, FixtureMixin, serie


class CounterBasis(DrafterTest):
    def zeile(self, a, b, wert, quelle=Datenquelle.FIXTURE, spiele=400):
        return StatRecord(
            art=ART_COUNTER, brawler_id=self.brawler(a).id, partner_id=self.brawler(b).id,
            advantage=wert, games=spiele, source=quelle, confidence=0.6, adjusted_rate=0.5,
        )

    def raum(self, *zeilen):
        return Datenraum(brawl_map=self.karte(), provider=SnapshotStatProvider(zeilen)).laden()

    def v(self, raum, a, b):
        return vorteil(self.brawler(a), self.brawler(b), raum)


class GemessenerCounterTest(CounterBasis):
    def test_gemessener_counter_ist_symmetrisch(self):
        raum = self.raum(self.zeile("gale", "bull", 0.3))
        self.assertAlmostEqual(self.v(raum, "gale", "bull")[0], 0.3)
        self.assertAlmostEqual(self.v(raum, "bull", "gale")[0], -0.3)

    def test_egal_welche_richtung_gespeichert_ist(self):
        hin = self.raum(self.zeile("gale", "bull", 0.3))
        her = self.raum(self.zeile("bull", "gale", -0.3))
        for a, b in (("gale", "bull"), ("bull", "gale")):
            self.assertAlmostEqual(self.v(hin, a, b)[0], self.v(her, a, b)[0])

    def test_kein_double_counting_wenn_beide_richtungen_vorliegen(self):
        """Der alte Fehler: hin + 0,8 * hin = 1,8-fach."""
        raum = self.raum(self.zeile("gale", "bull", 0.3), self.zeile("bull", "gale", -0.3))
        self.assertAlmostEqual(self.v(raum, "gale", "bull")[0], 0.3)
        self.assertAlmostEqual(self.v(raum, "bull", "gale")[0], -0.3)

    def test_synthetische_messung_folgt_der_messlogik(self):
        raum = self.raum(self.zeile("gale", "bull", 0.3, quelle=Datenquelle.SYNTHETIC))
        wert, _, quelle = self.v(raum, "bull", "gale")
        self.assertAlmostEqual(wert, -0.3)
        self.assertEqual(quelle, "demo", "Synthetisch ist nicht gemessen - so benannt")

    def test_grund_nennt_die_stichprobe_statt_eines_mechanismus(self):
        raum = self.raum(self.zeile("gale", "bull", 0.3, spiele=812))
        _, grund, _ = self.v(raum, "gale", "bull")
        self.assertIn("812 Partien", grund)
        self.assertIn("als erwartet", grund)

    def test_messung_hat_vorrang_vor_pflege(self):
        raum = self.raum(
            self.zeile("gale", "bull", 0.6, quelle=Datenquelle.DEMO),
            self.zeile("bull", "gale", -0.2, quelle=Datenquelle.FIXTURE),
        )
        self.assertAlmostEqual(self.v(raum, "gale", "bull")[0], 0.2)


class GepflegterCounterTest(CounterBasis):
    def test_gepflegte_counter_duerfen_asymmetrisch_sein(self):
        faktor = config.GEPFLEGTER_COUNTER_GEGENRICHTUNG
        raum = self.raum(
            self.zeile("gale", "bull", 0.3, quelle=Datenquelle.DEMO),
            self.zeile("bull", "gale", -0.1, quelle=Datenquelle.DEMO),
        )
        hin, her = self.v(raum, "gale", "bull")[0], self.v(raum, "bull", "gale")[0]
        self.assertAlmostEqual(hin, 0.3 + 0.1 * faktor)
        self.assertAlmostEqual(her, -0.1 - 0.3 * faktor)
        self.assertNotAlmostEqual(hin, -her)

    def test_faktor_ist_unveraendert(self):
        """Die 0,8 sind nur aus dem Code in die Konfiguration umgezogen."""
        self.assertEqual(config.GEPFLEGTER_COUNTER_GEGENRICHTUNG, 0.8)
        self.assertEqual(config.HEURISTISCHER_COUNTER_GEGENRICHTUNG, 0.8)

    def test_heuristik_ohne_zeilen_unveraendert(self):
        raum = self.raum()
        gale, bull = self.brawler("gale"), self.brawler("bull")
        hin, _ = heuristischer_vorteil(gale, bull)
        her, _ = heuristischer_vorteil(bull, gale)
        erwartet = max(-1.0, min(1.0, hin - her * config.HEURISTISCHER_COUNTER_GEGENRICHTUNG))
        self.assertAlmostEqual(vorteil(gale, bull, raum)[0], erwartet)
        self.assertEqual(vorteil(gale, bull, raum)[2], "heuristik")

    def test_zugriffe_trennen_die_bedeutungen(self):
        gepflegt = self.zeile("gale", "bull", 0.3, quelle=Datenquelle.MANUAL)
        gemessen = self.zeile("gale", "bull", 0.3, quelle=Datenquelle.API)
        self.assertEqual((gepflegt.manual_counter_score, gepflegt.measured_counter_advantage), (0.3, None))
        self.assertEqual((gemessen.manual_counter_score, gemessen.measured_counter_advantage), (None, 0.3))


class CounterVerhaeltnisTest(CounterBasis):
    """Die Counter-Komponente bleibt im Verhaeltnis zu Map Fit und Teambedarf."""

    def test_gemessener_counter_wird_nicht_verstaerkt(self):
        ctx = self.context(gegner=["bull"])
        gale = self.brawler("gale")
        gemessen = komponente(gale, ctx, self.raum(self.zeile("gale", "bull", 0.3)))
        gepflegt = komponente(gale, ctx, self.raum(
            self.zeile("gale", "bull", 0.3, quelle=Datenquelle.DEMO),
            self.zeile("bull", "gale", -0.3, quelle=Datenquelle.DEMO),
        ))
        # Ein Gegner: Komponente = Vorteil gegen ihn.
        self.assertAlmostEqual(gemessen.wert, 0.3)
        # Dieselben Zahlen als gegengleiche Pflege: genau der alte 1,8-Faktor.
        self.assertAlmostEqual(gepflegt.wert, 0.3 * (1 + config.GEPFLEGTER_COUNTER_GEGENRICHTUNG))

    def test_counter_gewicht_nie_groesser_als_map_fit_und_bedarf_zusammen(self):
        for phase, gewichte in config.PHASEN_GEWICHTE.items():
            self.assertLessEqual(
                gewichte[config.K_COUNTER],
                gewichte[config.K_MAP_MODE] + gewichte[config.K_TEAM_NEED],
                msg=phase,
            )

    def test_extreme_messung_bleibt_durch_ihr_gewicht_begrenzt(self):
        gegner = ["bull", "tick", "mortis"]
        zeilen = [self.zeile("gale", g, 1.0) for g in gegner]
        engine = DraftEngine(
            self.context(eigene=["belle", "max"], gegner=gegner),
            provider=SnapshotStatProvider(zeilen),
        )
        gale = self.empfehlung(engine.empfehlungen(anzahl=50, mit_details=0), "gale")
        counter = gale.komponenten[config.K_COUNTER]
        self.assertLessEqual(counter.wert, 1.0)
        self.assertLessEqual(counter.beitrag, counter.gewicht + 1e-9)


class AggregierterCounterTest(FixtureMixin, CounterBasis):
    def aggregiere(self):
        Aggregator((Datenquelle.SYNTHETIC,), stichtag=BASIS.date(), fenster=["90d"]).ausfuehren()
        return hole_stat_provider("synthetisch")

    def test_nur_eine_richtung_je_paar_gespeichert(self):
        self.importiere(*serie(10, 7))
        self.aggregiere()
        zeilen = CounterStat.objects.filter(source=Datenquelle.SYNTHETIC)
        self.assertTrue(zeilen.exists())
        paare = set()
        for z in zeilen:
            self.assertLess(z.brawler_id, z.enemy_id)
            paare.add((z.context_key, z.brawler_id, z.enemy_id))
        self.assertEqual(len(paare), zeilen.count())

    def test_datenbank_verbietet_berechnete_gegenrichtung(self):
        klein, gross = sorted((self.brawler("gale"), self.brawler("bull")), key=lambda b: b.id)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CounterStat.objects.create(brawler=gross, enemy=klein, source=Datenquelle.FIXTURE)
        # Gepflegt ist die Gegenrichtung erlaubt - und in den Demo-Daten ueblich.
        CounterStat.objects.create(
            brawler=gross, enemy=klein, source=Datenquelle.MANUAL, rank_pool="pro",
        )

    def test_aggregierter_counter_ist_in_der_engine_symmetrisch(self):
        self.importiere(*serie(10, 8))
        self.importiere(*serie(10, 2, b=("piper", "brock", "colette"), minuten=1000))
        self.importiere(*serie(10, 2, a=("rosa", "poco", "pam"), minuten=2000))
        raum = Datenraum(brawl_map=self.karte(), provider=self.aggregiere()).laden()
        hin, her = self.v(raum, "gale", "buster")[0], self.v(raum, "buster", "gale")[0]
        self.assertGreater(hin, 0)
        self.assertAlmostEqual(hin, -her, places=6)

    def test_starker_brawler_wird_in_der_engine_nicht_zum_counter(self):
        """Gale gewinnt gegen jeden 80 % - gegen Buster ist das kein Counter."""
        self.importiere(*serie(10, 8))
        self.importiere(*serie(10, 8, b=("piper", "brock", "colette"), minuten=1000))
        raum = Datenraum(brawl_map=self.karte(), provider=self.aggregiere()).laden()
        zeile = CounterStat.objects.get(
            brawler__slug="gale", enemy__slug="buster", game_mode__isnull=True, rank_pool="alle",
        )
        self.assertAlmostEqual(zeile.raw_rate, 0.8)
        self.assertLess(abs(self.v(raum, "gale", "buster")[0]), 0.2)
