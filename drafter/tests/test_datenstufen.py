"""Datenstufen: unbekannt heisst unbekannt, nicht 0.

Geprueft werden Verfuegbarkeit und Richtungen, keine Raenge (siehe
test_modellverhalten.py): ein Brawler ohne Profil darf weder aus Nullen
bewertet werden noch Luecken, Counter-Gruende oder Deckung verfaelschen.
"""

from drafter import config
from drafter.models import Brawler, BrawlerStat, Datenquelle
from drafter.models.stats import CounterStat
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import gemessener_provider
from drafter.services.team_coverage import Teamanalyse
from drafter.tests.basis import DrafterTest

PROFIL_KOMPONENTEN = (
    config.K_MAP_MODE, config.K_TEAM_NEED, config.K_DRAFT_POSITION,
    config.K_FLEXIBILITY, config.K_REDUNDANCY, config.K_WEAKNESS,
)


class DatenstufenTest(DrafterTest):
    def setUp(self):
        # Wie ein per API-Abgleich angelegter Brawler: ID, Name, sonst nichts.
        self.nori = Brawler.objects.create(
            name="NORI", slug="nori", external_id="16000099", is_active=False,
        )
        self.shelly = Brawler.objects.create(
            name="SHELLY", slug="shelly", external_id="16000000", is_active=False,
        )

    def messe(self, brawler, spiele, rate=0.56):
        BrawlerStat.objects.create(
            brawler=brawler, games=spiele, wins=round(spiele * rate),
            raw_rate=rate, adjusted_rate=rate, confidence=0.15,
            source=Datenquelle.API, window_label="90d",
        )

    def engine(self, **kwargs):
        return DraftEngine(self.context(**kwargs), provider=gemessener_provider())

    def empfehlung(self, engine, slug):
        return next((e for e in engine.empfehlungen(anzahl=200) if e.brawler.slug == slug), None)

    # --- Stufen ---------------------------------------------------------
    def test_stufen_folgen_profil_und_stichprobe(self):
        self.messe(self.nori, config.PROFIL_MESS_MINDESTSPIELE)
        self.messe(self.shelly, config.PROFIL_MESS_MINDESTSPIELE - 1)
        self.messe(self.brawler("gale"), 3)
        raum = self.engine().raum
        self.assertEqual(raum.stufe(self.brawler("gale")), "profil")
        self.assertEqual(raum.stufe(self.nori), "gemessen")
        self.assertEqual(raum.stufe(self.shelly), "katalog")

    def test_katalog_brawler_bekommt_keinen_score(self):
        self.messe(self.shelly, 3)
        engine = self.engine()
        self.assertIsNone(self.empfehlung(engine, "shelly"))
        engine.empfehlungen()
        self.assertNotIn("shelly", engine.alle_scores)

    def test_gemessener_brawler_wird_nur_aus_messwerten_bewertet(self):
        self.messe(self.nori, 30)
        e = self.empfehlung(self.engine(), "nori")
        self.assertIsNotNone(e)
        self.assertEqual(e.stufe, "gemessen")
        for key in PROFIL_KOMPONENTEN:
            self.assertFalse(e.komponenten[key].verfuegbar, key)
        self.assertTrue(e.komponenten[config.K_META].verfuegbar)
        self.assertLess(e.datenabdeckung, 0.5)
        self.assertEqual(e.datenabdeckung_label, "Niedrig")

    def test_fehlende_komponenten_ziehen_nicht_zur_mitte(self):
        """Hochgerechnet: eine starke Meta wirkt so, als waere sie alles, was bekannt ist."""
        self.messe(self.nori, 30, rate=0.60)
        e = self.empfehlung(self.engine(), "nori")
        meta = e.komponenten[config.K_META]
        self.assertGreater(e.skalierung, 1.0)
        bewertung = e.roher_score - sum(
            k.beitrag for k in e.komponenten.values()
            if k.ist_strafe or k.key == config.K_PERSONAL
        )
        self.assertAlmostEqual(bewertung, meta.beitrag * e.skalierung, places=6)

    def test_quelle_steht_an_jeder_komponente(self):
        self.messe(self.nori, 30)
        e = self.empfehlung(self.engine(), "nori")
        self.assertEqual(e.komponenten[config.K_META].quelle, "Measured + Prior")
        quellen = {k["key"]: k["quelle"] for k in e.als_dict()["komponenten"]}
        self.assertEqual(quellen[config.K_MAP_MODE], "Unknown")

    def test_voll_bekannter_brawler_wird_nicht_skaliert(self):
        e = self.empfehlung(DraftEngine(self.context()), "gale")
        self.assertEqual(e.skalierung, 1.0)
        self.assertEqual(e.datenabdeckung, 1.0)
        self.assertEqual(e.ausgelassen, [])

    def test_persoenliche_sicherheit_wird_nicht_hochgerechnet(self):
        self.messe(self.nori, 30)
        engine = self.engine(personal={self.nori.id: {"confidence": 100.0}})
        e = self.empfehlung(engine, "nori")
        persoenlich = e.komponenten[config.K_PERSONAL]
        self.assertLessEqual(abs(persoenlich.beitrag), config.PERSOENLICH_MAX_AUSSCHLAG + 1e-9)
        eintrag = next(k for k in e.als_dict()["komponenten"] if k["key"] == config.K_PERSONAL)
        self.assertAlmostEqual(eintrag["beitrag"], round(persoenlich.beitrag * 50, 1))

    # --- Picks ohne Profil ---------------------------------------------
    def test_eigener_pick_ohne_profil_erzeugt_keine_luecken(self):
        anf = self.karte().anforderungs_vektor()
        ohne = Teamanalyse.bauen([self.brawler("gale")], anf)
        mit = Teamanalyse.bauen([self.brawler("gale"), self.shelly], anf)
        self.assertEqual(ohne.profil, mit.profil)
        self.assertEqual(ohne.deckungsgrad(), mit.deckungsgrad())
        self.assertEqual([b.slug for b in mit.unbekannt], ["shelly"])

    def test_gegner_ohne_profil_erzeugt_keine_heuristischen_gruende(self):
        engine = DraftEngine(self.context(gegner=["shelly"], first_pick=False))
        for e in engine.empfehlungen(anzahl=200):
            counter = e.komponenten[config.K_COUNTER]
            self.assertFalse(counter.verfuegbar, e.brawler.slug)
            self.assertFalse(any("SHELLY" in g.text for g in counter.gruende))

    def test_gemessener_counter_gegen_gegner_ohne_profil_zaehlt(self):
        gale = self.brawler("gale")
        CounterStat.objects.create(
            brawler=gale, enemy=self.shelly, games=10, advantage=0.3,
            source=Datenquelle.API, window_label="90d",
        )
        engine = self.engine(gegner=["shelly"], first_pick=False)
        counter = self.empfehlung(engine, "gale").komponenten[config.K_COUNTER]
        self.assertTrue(counter.verfuegbar)
        self.assertGreater(counter.wert, 0)

    def test_bans_nur_fuer_bewertbare_und_mit_abdeckung(self):
        self.messe(self.nori, 30, rate=0.65)
        self.messe(self.shelly, 2, rate=0.9)
        engine = self.engine()
        bans = {b["slug"]: b for b in engine.als_dict()["ban_empfehlungen"]}
        self.assertNotIn("shelly", bans)
        for eintrag in bans.values():
            self.assertIn(eintrag["datenstufe"], ("profil", "gemessen"))
            self.assertGreater(eintrag["datenabdeckung"], 0)

    def test_antwort_nennt_stufe_und_abdeckung(self):
        self.messe(self.nori, 30)
        daten = self.engine().als_dict()
        self.assertEqual(daten["datenstufen"]["nori"]["stufe"], "gemessen")
        self.assertNotIn("shelly", daten["datenstufen"])
        erste = daten["empfehlungen"][0]
        for feld in ("datenstufe", "datenabdeckung", "datenabdeckung_label", "ausgelassen"):
            self.assertIn(feld, erste)

    def test_demo_profil_bleibt_gedeckelt_auch_mit_messdaten(self):
        """Gemessene Zeilen im Datenraum machen ein geschaetztes Profil nicht belastbar."""
        from drafter.services.confidence import DEMO_DECKEL
        self.messe(self.nori, 30)
        engine = self.engine()
        self.assertFalse(engine.raum.nur_demo)
        gale = self.empfehlung(engine, "gale")
        self.assertLessEqual(gale.confidence, DEMO_DECKEL)


class QuellenprioritaetTest(DrafterTest):
    """Messung ersetzt Gepflegtes nur, wenn tatsaechlich gemessen wurde."""

    def engine(self, **kwargs):
        from drafter.services.providers.datenbank import gemessen_mit_prior_provider
        return DraftEngine(self.context(**kwargs), provider=gemessen_mit_prior_provider())

    def meta(self, engine, slug):
        e = next(x for x in engine.empfehlungen(anzahl=200) if x.brawler.slug == slug)
        return e.komponenten[config.K_META]

    def messe(self, slug, spiele, rate):
        BrawlerStat.objects.create(
            brawler=self.brawler(slug), games=spiele, sample_size=spiele,
            wins=round(spiele * rate), raw_rate=rate, adjusted_rate=rate,
            confidence=0.2, source=Datenquelle.API, window_label="90d",
        )

    def test_profil_ohne_messung_behaelt_seine_meta(self):
        # Irgendeine Messung im Datenraum - aber keine fuer Gale.
        self.messe("sandy", 30, 0.55)
        meta = self.meta(self.engine(), "gale")
        self.assertTrue(meta.verfuegbar)
        self.assertEqual(meta.quelle, "Profile")

    def test_wenig_messung_mischt_mit_dem_profil(self):
        from drafter.services.quellen import meta_aufloesen
        prior = BrawlerStat.objects.get(brawler__slug="gale", source=Datenquelle.DEMO)
        self.messe("gale", 30, 0.30)
        engine = self.engine()
        auskunft = engine.raum.meta(self.brawler("gale"))
        w = 30 / (30 + config.PRIOR_STAERKE)
        self.assertEqual(auskunft.quelle, "Measured + Prior")
        self.assertAlmostEqual(auskunft.rate, w * 0.30 + (1 - w) * prior.adjusted_rate)
        self.assertEqual(self.meta(engine, "gale").quelle, "Measured + Prior")

    def test_genug_messung_ersetzt_das_profil(self):
        self.messe("gale", config.CONFIDENCE_VOLL_AB, 0.30)
        auskunft = self.engine().raum.meta(self.brawler("gale"))
        self.assertEqual(auskunft.quelle, "Measured")
        self.assertAlmostEqual(auskunft.rate, 0.30)

    def test_weder_messung_noch_profil_ist_unknown(self):
        nori = Brawler.objects.create(name="NORI", slug="nori", external_id="1", is_active=False)
        auskunft = self.engine().raum.meta(nori)
        self.assertEqual(auskunft.quelle, "Unknown")
        self.assertIsNone(auskunft.rate)

    def test_jede_komponente_nennt_ihre_quelle(self):
        self.messe("sandy", 30, 0.55)
        erlaubt = {"Measured", "Measured + Prior", "Profile", "Unknown"}
        for e in self.engine(gegner=["bull"]).empfehlungen():
            for k in e.als_dict()["komponenten"]:
                self.assertIn(k["quelle"], erlaubt, (e.brawler.slug, k["key"]))


class RankedVerfuegbarkeitTest(DrafterTest):
    """Nicht ranked-wählbare Brawler sind keine Datenlücke."""

    def setUp(self):
        self.gesperrt = Brawler.objects.create(
            name="COSMO", slug="cosmo", external_id="16000200",
            is_active=False, ranked_verfuegbar=False,
        )

    def test_gesperrter_brawler_ist_kein_kandidat(self):
        engine = DraftEngine(self.context())
        self.assertNotIn("cosmo", {b.slug for b in engine.raum.brawler})
        self.assertNotIn("cosmo", engine.als_dict()["scores"])

    def test_gesperrter_brawler_bleibt_im_katalog(self):
        from django.urls import reverse
        daten = self.client.get(reverse("drafter:api_katalog")).json()
        eintrag = next(b for b in daten["brawler"] if b["slug"] == "cosmo")
        self.assertFalse(eintrag["ranked_verfuegbar"])

    def test_gesperrter_brawler_erzeugt_kein_defizit(self):
        from drafter.services.prioritaet import Datenluecken
        luecken = Datenluecken()
        self.assertIn(self.gesperrt.id, luecken.ausgeschlossen)
        self.assertNotIn(self.gesperrt.id, luecken.seltene_brawler())

    def test_sperre_ist_umstellbar(self):
        Brawler.objects.filter(pk=self.gesperrt.pk).update(ranked_verfuegbar=True, is_active=True)
        engine = DraftEngine(self.context())
        self.assertIn("cosmo", {b.slug for b in engine.raum.brawler})


class PersoenlicheConfidenceOptionalTest(DrafterTest):
    """Ohne gepflegte Werte darf nichts schlechter werden."""

    def test_ohne_werte_kein_malus_und_keine_luecke(self):
        e = next(x for x in DraftEngine(self.context()).empfehlungen() if x.brawler.slug == "gale")
        persoenlich = e.komponenten[config.K_PERSONAL]
        self.assertFalse(persoenlich.verfuegbar)
        self.assertEqual(persoenlich.beitrag, 0.0)
        self.assertEqual(e.datenabdeckung, 1.0, "Abdeckung bleibt voll")
        self.assertEqual(e.ausgelassen, [], "gilt nicht als fehlende Komponente")

    def test_ohne_werte_ist_die_confidence_nicht_niedriger(self):
        ohne = next(x for x in DraftEngine(self.context()).empfehlungen()
                    if x.brawler.slug == "gale")
        mit = next(x for x in DraftEngine(
            self.context(personal={self.brawler("gale").id: {"confidence": 50.0}})
        ).empfehlungen() if x.brawler.slug == "gale")
        self.assertGreaterEqual(ohne.confidence, mit.confidence - 1e-9)

    def test_gepflegter_wert_wirkt_weiterhin_begrenzt(self):
        e = next(x for x in DraftEngine(
            self.context(personal={self.brawler("gale").id: {"confidence": 100.0}})
        ).empfehlungen() if x.brawler.slug == "gale")
        komp = e.komponenten[config.K_PERSONAL]
        self.assertTrue(komp.verfuegbar)
        self.assertLessEqual(abs(komp.beitrag), config.PERSOENLICH_MAX_AUSSCHLAG + 1e-9)
