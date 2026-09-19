# -*- coding: utf-8 -*-
"""Gem Grab und Brawl Ball verstehen ihr Ziel.

Gem Grab kannte bis zum 2026-09-19 nur Kontrolle - "wer traegt die Gems"
und "wer holt sie zurueck" kamen im Modusprofil nicht vor. Brawl Ball
kannte das TOR nicht: `objective_damage` stand nur auf einer einzelnen
Map, nicht im Modusziel.

Geprueft werden Richtungen und Strukturen, keine Raenge - und dass die
Mechanik modusunabhaengig bleibt.
"""

from drafter import attributes as attr
from drafter import config
from drafter.models import Brawler, BrawlerStat, Datenquelle, GameMode
from drafter.services import objective, rollenwissen
from drafter.services.anfrage import context_aus_daten
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import gemessen_mit_prior_provider
from drafter.tests.basis import DrafterTest


class ZielprofilTest(DrafterTest):
    def test_gem_grab_kennt_traeger_und_druck(self):
        anforderungen = GameMode.objects.get(slug="gem-grab").base_requirements
        for key in ("survivability", "disengage"):
            self.assertIn(key, anforderungen, "der Traeger muss ueberleben koennen")
        for key in ("engage", "backline_pressure"):
            self.assertIn(key, anforderungen, "jemand muss den Traeger jagen")

    def test_brawl_ball_kennt_das_tor(self):
        anforderungen = GameMode.objects.get(slug="brawl-ball").base_requirements
        self.assertIn("objective_damage", anforderungen)
        self.assertEqual(max(anforderungen, key=anforderungen.get), "objective_damage",
                         "das Tor ist das Ziel des Modus")

    def test_aspekte_nutzen_nur_vorhandenes_vokabular(self):
        for modus, tabelle in config.MODUS_ZIELASPEKTE.items():
            for name, keys in tabelle.items():
                for key in keys:
                    self.assertIn(key, attr.ATTRIBUT_KEYS, f"{modus}/{name}: {key}")

    def test_keine_neuen_brawlerfelder(self):
        for erfunden in ("gem_carrier_value", "goal_pressure", "ball_access",
                         "teamwipe_pressure", "carrier_survival"):
            self.assertNotIn(erfunden, attr.ATTRIBUT_KEYS)


class AspektTest(DrafterTest):
    """Der beste erfuellte Aspekt zaehlt - niemand muss alles koennen."""

    def tabelle(self, modus="gem-grab"):
        return config.MODUS_ZIELASPEKTE[modus]

    def test_spezialist_wird_an_seinem_aspekt_gemessen(self):
        traeger = Brawler.objects.create(
            name="TRAEGER", slug="traeger", external_id="98001", is_active=True,
            source=Datenquelle.MANUAL,
            attributes={"survivability": 90, "disengage": 85, "safe_poke": 70},
        )
        erfuellung = objective.aspekt_erfuellung(traeger, self.tabelle())
        name, wert = objective.bester_aspekt(erfuellung)
        self.assertEqual(name, "carrier")
        self.assertGreater(wert, 0.6)
        # ... und er wird NICHT dafuer bestraft, dass er kein Aggressor ist.
        self.assertLess(erfuellung["druck_auf_traeger"], wert)

    def test_zweiter_spezialist_zaehlt_ueber_seinen_eigenen_aspekt(self):
        jaeger = Brawler.objects.create(
            name="JAEGER", slug="jaeger", external_id="98002", is_active=True,
            source=Datenquelle.MANUAL,
            attributes={"engage": 90, "backline_pressure": 85, "mobility": 80,
                        "burst_damage": 75},
        )
        name, wert = objective.bester_aspekt(
            objective.aspekt_erfuellung(jaeger, self.tabelle()))
        self.assertEqual(name, "druck_auf_traeger")
        self.assertGreater(wert, 0.6)

    def test_mittelmass_in_allem_schlaegt_keinen_spezialisten(self):
        mittel = Brawler.objects.create(
            name="MITTEL", slug="mittel", external_id="98003", is_active=True,
            source=Datenquelle.MANUAL,
            attributes={k: 45 for aspekt in config.MODUS_ZIELASPEKTE["gem-grab"].values()
                        for k in aspekt},
        )
        spezialist = Brawler.objects.create(
            name="SPEZI", slug="spezi", external_id="98004", is_active=True,
            source=Datenquelle.MANUAL,
            attributes={"survivability": 90, "disengage": 90, "safe_poke": 85},
        )
        _, wert_mittel = objective.bester_aspekt(
            objective.aspekt_erfuellung(mittel, self.tabelle()))
        _, wert_spezi = objective.bester_aspekt(
            objective.aspekt_erfuellung(spezialist, self.tabelle()))
        self.assertGreater(wert_spezi, wert_mittel)

    def test_ohne_profil_zaehlt_die_beruehrung_statt_der_hoehe(self):
        ohne = Brawler.objects.create(
            name="ROLLE", slug="rolle", external_id="98005", is_active=True,
            source=Datenquelle.MANUAL, draft_rolle="tank")
        self.assertEqual(objective.aspekt_erfuellung(ohne, self.tabelle()), {})
        beruehrung = objective.aspekt_beruehrung(ohne, self.tabelle())
        self.assertTrue(beruehrung)
        self.assertLessEqual(max(beruehrung.values()), 1.0)
        # Es entsteht weiterhin kein Attributwert.
        self.assertEqual(ohne.wert("survivability"), 0.0)

    def test_brawl_ball_aspekte_trennen_abschluss_von_raum(self):
        tabelle = self.tabelle("brawl-ball")
        self.assertIn("abschluss", tabelle)
        self.assertIn("objective_damage", tabelle["abschluss"])
        self.assertNotIn("objective_damage", tabelle["raum"])


class MidControlTest(DrafterTest):
    """Control ist ein Spielstil, Mid eine Position."""

    def test_rolle_control_behauptet_kein_mid(self):
        self.assertNotIn("mid_control", config.ROLLE_DECKT["control"])
        for rolle, keys in config.ROLLE_DECKT.items():
            self.assertNotIn("mid_control", keys, rolle)

    def test_ohne_profil_bleibt_mid_unbekannt(self):
        """Lieber keine Auskunft als falsches Rollenwissen."""
        b = Brawler.objects.create(name="KONTROLL", slug="kontroll", external_id="98006",
                                   is_active=True, draft_rolle="control",
                                   source=Datenquelle.MANUAL)
        self.assertNotIn("mid_control", rollenwissen.deckt(b))


class MapEbeneTest(DrafterTest):
    """Die Map-Ebene ist ein Zuwachs zur Modus-Eignung, keine zweite Staerke."""

    def messe(self, slug, spiele, rate, ebene):
        karte = self.karte()
        felder = {}
        if ebene in ("modus", "map"):
            felder["game_mode"] = karte.game_mode
        if ebene == "map":
            felder["brawl_map"] = karte
        BrawlerStat.objects.create(
            brawler=self.brawler(slug), games=spiele, sample_size=spiele,
            wins=round(spiele * rate), raw_rate=rate, adjusted_rate=rate,
            confidence=0.5, source=Datenquelle.API, window_label="90d", **felder)

    def eignung(self):
        raum = DraftEngine(self.context(),
                           provider=gemessen_mit_prior_provider()).raum.laden()
        return objective.modus_eignung(self.brawler("gale"), raum)

    def test_gute_map_hebt_die_eignung(self):
        self.messe("gale", 2000, 0.50, "global")
        self.messe("gale", 600, 0.50, "modus")
        self.messe("gale", 300, 0.62, "map")
        e = self.eignung()
        self.assertGreater(e["map_diff"], 0.02)
        self.assertGreater(e["differenz"], e["modus_diff"])

    def test_duenne_map_zeile_bewegt_kaum(self):
        self.messe("gale", 2000, 0.50, "global")
        self.messe("gale", 600, 0.50, "modus")
        self.messe("gale", 6, 1.00, "map")
        self.assertLess(abs(self.eignung()["map_diff"]), 0.03)

    def test_ohne_map_zeile_kein_zuwachs(self):
        self.messe("gale", 2000, 0.50, "global")
        self.messe("gale", 600, 0.56, "modus")
        e = self.eignung()
        self.assertEqual(e["map_diff"], 0.0)
        self.assertEqual(e["differenz"], e["modus_diff"])


class TeambedarfTest(DrafterTest):
    """Nach eigenen Picks muss der Bedarf das Ziel kennen."""

    def bedarf(self, picks, karte="center-stage"):
        ctx = context_aus_daten({"map": karte, "own_picks": picks})
        engine = DraftEngine(ctx)
        engine.empfehlungen(anzahl=10)
        return engine.eigene_analyse

    def test_fehlender_abschluss_wird_zur_luecke(self):
        """Zwei Kontrollpicks: Torgefahr muss als Luecke auftauchen."""
        analyse = self.bedarf(["gale", "sandy"])
        luecken = {e.key for e, _ in analyse.groesste_luecken(anzahl=6)}
        self.assertIn("objective_damage", luecken,
                      "ohne Abschluss fehlt dem Team das Tor")

    def test_frontliner_deckt_anderes_ab_als_kontrolle(self):
        kontrolle = self.bedarf(["gale", "sandy"])
        gemischt = self.bedarf(["buster", "gale"])
        self.assertNotEqual(
            [e.key for e, _ in kontrolle.groesste_luecken(anzahl=4)],
            [e.key for e, _ in gemischt.groesste_luecken(anzahl=4)])

    def test_leerer_draft_zaehlt_weiterhin_nicht_doppelt(self):
        ctx = context_aus_daten({"map": "center-stage"})
        for e in DraftEngine(ctx).empfehlungen(anzahl=50):
            self.assertFalse(e.komponenten[config.K_TEAM_NEED].anwendbar)


class GenerischBleibtTest(DrafterTest):
    """Der Mechanismus kennt weiterhin keinen Modus beim Namen."""

    def test_objective_nennt_keinen_modus(self):
        with open(objective.__file__, encoding="utf-8") as datei:
            inhalt = datei.read().lower()
        for name in ("gem-grab", "gem_grab", "brawl-ball", "brawl_ball",
                     "heist", "hot_zone", "knockout", "bounty"):
            self.assertNotIn(f'"{name}"', inhalt)
            self.assertNotIn(f"'{name}'", inhalt)

    def test_modus_ohne_aspekte_funktioniert_weiter(self):
        """Heist, Knockout, Bounty und Hot Zone haben keine Aspekte."""
        for slug in ("heist", "knockout", "bounty", "hot-zone"):
            self.assertNotIn(slug, config.MODUS_ZIELASPEKTE)
            modus = GameMode.objects.get(slug=slug)
            self.assertEqual(objective.aspekte(modus), {})
