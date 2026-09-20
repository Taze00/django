# -*- coding: utf-8 -*-
"""OBJECTIVE FIT: passt ein Brawler zum ZIEL des Modus?

Geprueft werden die vier Reparaturen vom 2026-09-18:

1. Map-Fit und Teambedarf messen im leeren Draft nicht mehr dasselbe.
2. Gemessene Modus-Eignung schlaegt ein gepflegtes Profil.
3. Gepflegte Faehigkeiten zaehlen, ohne zu einem Zahlenwert zu werden.
4. Der Mechanismus ist modusunabhaengig.

Keine Brawlernamen als Erwartung - geprueft werden Richtungen und
Quellen, nicht Plaetze.
"""

from drafter import config
from drafter.models import BrawlMap, Brawler, BrawlerStat, Datenquelle, GameMode
from drafter.services import objective
from drafter.services.anfrage import context_aus_daten
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import gemessen_mit_prior_provider
from drafter.tests.basis import DrafterTest


class DoppelzaehlungTest(DrafterTest):
    """Map & Modus und Teambedarf beantworten verschiedene Fragen."""

    def test_leerer_draft_hat_keinen_teambedarf(self):
        for e in self.engine().empfehlungen(anzahl=200):
            komp = e.komponenten[config.K_TEAM_NEED]
            self.assertFalse(komp.anwendbar, e.brawler.slug)
            self.assertEqual(komp.beitrag, 0.0, e.brawler.slug)

    def test_gegnerischer_pick_erzeugt_wieder_bedarf(self):
        """Nur der voellig leere Draft ist die Doppelzaehlung - nicht jeder First Pick."""
        empfehlungen = self.engine(gegner=["bull"], first_pick=False).empfehlungen(anzahl=200)
        beitraege = [abs(e.komponenten[config.K_TEAM_NEED].beitrag) for e in empfehlungen]
        self.assertTrue(any(b > 0 for b in beitraege),
                        "ein gegnerischer Pick erzeugt echten Bedarf")

    def test_eigener_pick_erzeugt_wieder_bedarf(self):
        empfehlungen = self.engine(eigene=["gale"]).empfehlungen(anzahl=200)
        beitraege = [abs(e.komponenten[config.K_TEAM_NEED].beitrag) for e in empfehlungen]
        self.assertTrue(any(b > 0 for b in beitraege))

    def test_teambedarf_ist_nicht_mehr_die_map_passung(self):
        """Der eigentliche Beweis: die beiden Werte duerfen nicht gekoppelt sein.

        Frueher war der Teambedarf im leeren Draft dasselbe Skalarprodukt
        wie die Map-Passung - zwei Komponenten, eine Rechnung.
        """
        leer = self.engine().empfehlungen(anzahl=200)
        self.assertTrue(all(e.komponenten[config.K_TEAM_NEED].beitrag == 0 for e in leer))
        self.assertTrue(any(e.komponenten[config.K_MAP_MODE].beitrag != 0 for e in leer))


class ModusEignungTest(DrafterTest):
    """Stufe 1: die Differenz Modus minus global."""

    def messe(self, slug, ebene, spiele, rate, karte=None):
        karte = karte or self.karte()
        felder = {}
        if ebene == "modus":
            felder["game_mode"] = karte.game_mode
        elif ebene == "map":
            felder["game_mode"] = karte.game_mode
            felder["brawl_map"] = karte
        BrawlerStat.objects.create(
            brawler=self.brawler(slug), games=spiele, sample_size=spiele,
            wins=round(spiele * rate), raw_rate=rate, adjusted_rate=rate,
            confidence=0.5, source=Datenquelle.API, window_label="90d", **felder
        )

    def eignung(self, slug, karte=None):
        karte = karte or self.karte()
        raum = DraftEngine(self.context(karte=karte.slug),
                           provider=gemessen_mit_prior_provider()).raum.laden()
        return objective.modus_eignung(self.brawler(slug), raum)

    def test_ohne_modus_zeile_keine_aussage(self):
        self.messe("gale", "global", 500, 0.52)
        self.assertIsNone(self.eignung("gale"))

    def test_besser_im_modus_ergibt_positives_signal(self):
        self.messe("gale", "global", 1000, 0.50)
        self.messe("gale", "modus", 400, 0.60)
        e = self.eignung("gale")
        self.assertGreater(e["differenz"], 0.02)

    def test_schlechter_im_modus_ergibt_negatives_signal(self):
        self.messe("gale", "global", 1000, 0.50)
        self.messe("gale", "modus", 400, 0.40)
        self.assertLess(self.eignung("gale")["differenz"], -0.02)

    def test_duenne_modus_stichprobe_schrumpft_gegen_null(self):
        """Kein Schwellenwert - die Kette erledigt das von selbst."""
        self.messe("gale", "global", 1000, 0.50)
        self.messe("gale", "modus", 8, 1.00)
        e = self.eignung("gale")
        self.assertLess(abs(e["differenz"]), 0.04,
                        "acht Partien sind keine Modus-Aussage")

    def test_partien_zaehlen_nicht_doppelt(self):
        """Die Modus-Partien stecken in der globalen Zeile mit drin.

        Spielt jemand nur diesen Modus, bleibt als Vergleich der Prior -
        und "Modus gegen 50 %" waere die aktuelle Staerke, nicht die
        Modus-Eignung. Ohne Basis gibt es deshalb keine Aussage.
        """
        self.messe("gale", "global", 400, 0.60)
        self.messe("gale", "modus", 400, 0.60)
        e = self.eignung("gale")
        self.assertAlmostEqual(e["differenz"], 0.0, places=6)


class QuellenprioritaetTest(DrafterTest):
    """Messung schlaegt Faehigkeit schlaegt Rolle schlaegt Unknown."""

    def anlegen(self, name, rolle="", faehigkeiten=()):
        return Brawler.objects.create(
            name=name, slug=name.lower(),
            external_id=f"17{abs(hash(name)) % 100000:05d}",
            is_active=True, source=Datenquelle.MANUAL, draft_rolle=rolle,
            draft_faehigkeiten=list(faehigkeiten),
        )

    def auskunft(self, brawler):
        engine = DraftEngine(self.context(), provider=gemessen_mit_prior_provider())
        raum = engine.raum.laden()
        kandidaten = list(raum.brawler)
        alle = objective.fuer_pool(kandidaten, raum, self.karte().anforderungs_vektor())
        return alle[brawler.id]

    def test_ohne_alles_ist_es_unbekannt(self):
        b = self.anlegen("NORO")
        a = self.auskunft(b)
        self.assertFalse(a.verfuegbar)
        self.assertEqual(a.quelle, "Unknown")

    def test_faehigkeit_zaehlt_ohne_zahlenwert(self):
        """Der COLT-Fall: gepflegtes `wallbreak`, kein Attributwert."""
        karte = self.karte()
        self.assertGreater(karte.anforderungs_vektor().get("wallbreak", 0), 0,
                           "Vorbedingung: diese Map verlangt Wandbruch")
        mit = self.anlegen("NORI", rolle="sniper", faehigkeiten=["wallbreak"])
        ohne = self.anlegen("NORU", rolle="sniper")
        a_mit, a_ohne = self.auskunft(mit), self.auskunft(ohne)
        self.assertEqual(a_mit.quelle, "Fachquelle")
        self.assertIn("wallbreak", a_mit.faehigkeiten)
        self.assertGreater(a_mit.wert, a_ohne.wert)
        # ... und es entsteht KEIN Attributwert. Seit dem 2026-09-20 ist
        # das None statt 0: die Rolle sagt nichts ueber die Hoehe, und
        # eine 0 waere die Behauptung "kann das nicht".
        self.assertIsNone(mit.wert("wallbreak"))
        self.assertFalse(mit.bekannt("wallbreak"))
        self.assertFalse(mit.hat_profil)

    def test_messung_verdraengt_das_fachwissen(self):
        b = self.anlegen("NORI", rolle="sniper", faehigkeiten=["wallbreak"])
        karte = self.karte()
        # Die globale Zeile ENTHAELT die Modus-Partien - sie muss deshalb
        # groesser sein, sonst gibt es ausserhalb des Modus keine Basis.
        for spiele, rate, felder in ((1500, 0.50, {}),
                                     (600, 0.60, {"game_mode": karte.game_mode})):
            BrawlerStat.objects.create(
                brawler=b, games=spiele, sample_size=spiele, wins=round(spiele * rate),
                raw_rate=rate, adjusted_rate=rate,
                confidence=0.5, source=Datenquelle.API, window_label="90d", **felder)
        a = self.auskunft(b)
        self.assertEqual(a.quelle, objective.MESSUNG)
        self.assertGreater(a.wert, 0)
        self.assertGreater(a.differenz, 0)

    def test_messung_kann_einem_profil_widersprechen(self):
        """Der BROCK-Fall: Profil sagt perfekt, hunderte Partien sagen nein."""
        karte = self.karte()
        gut = self.empfehlung(
            DraftEngine(self.context(), provider=gemessen_mit_prior_provider())
            .empfehlungen(anzahl=200), "gale")
        vorher = gut.komponenten[config.K_MAP_MODE].wert
        for spiele, rate, felder in ((2000, 0.50, {}),
                                     (800, 0.35, {"game_mode": karte.game_mode})):
            BrawlerStat.objects.create(
                brawler=self.brawler("gale"), games=spiele, sample_size=spiele,
                wins=round(spiele * rate), raw_rate=rate, adjusted_rate=rate,
                confidence=0.6, source=Datenquelle.API, window_label="90d", **felder)
        nachher = self.empfehlung(
            DraftEngine(self.context(), provider=gemessen_mit_prior_provider())
            .empfehlungen(anzahl=200), "gale").komponenten[config.K_MAP_MODE]
        self.assertLess(nachher.wert, vorher,
                        "eine schlechte Modus-Bilanz muss die Profil-Passung drücken")
        self.assertIsNotNone(nachher.objective)
        self.assertLess(nachher.objective.differenz, 0)


class GenerischTest(DrafterTest):
    """Derselbe Mechanismus, andere Modi - keine Sonderlogik je Modus."""

    MODI = {
        "gem-grab": {"mid_control": 80, "survivability": 70, "objective_damage": 40},
        "hot-zone-test": {"zone_control": 85, "area_control": 75, "survivability": 70},
        "brawl-ball": {"objective_damage": 80, "engage": 70, "mobility": 75},
        "knockout": {"long_range": 80, "disengage": 70, "burst_damage": 65},
        "bounty": {"long_range": 85, "poke": 70, "survivability": 60},
    }

    def lage(self, modus_slug, anforderungen):
        modus, _ = GameMode.objects.get_or_create(
            slug=modus_slug, defaults={"name": modus_slug, "order": 90})
        modus.base_requirements = anforderungen
        modus.is_active = True
        modus.save()
        karte, _ = BrawlMap.objects.get_or_create(
            slug=f"testmap-{modus_slug}",
            defaults={"name": f"Testmap {modus_slug}", "game_mode": modus})
        karte.game_mode = modus
        karte.requirements = {}
        karte.is_active = True
        karte.save()
        return karte

    def test_jeder_modus_bekommt_seine_eigenen_zielanforderungen(self):
        gesehen = {}
        for slug, anforderungen in self.MODI.items():
            karte = self.lage(slug, anforderungen)
            engine = DraftEngine(context_aus_daten({"map": karte.slug}),
                                 provider=gemessen_mit_prior_provider())
            empfehlungen = engine.empfehlungen(anzahl=200)
            self.assertTrue(empfehlungen, f"{slug}: keine Empfehlung")
            werte = {e.brawler.slug: e.komponenten[config.K_MAP_MODE].wert
                     for e in empfehlungen}
            gesehen[slug] = werte
            self.assertTrue(any(w != 0 for w in werte.values()),
                            f"{slug}: Map & Modus wirkt gar nicht")
        # Verschiedene Ziele muessen verschiedene Bilder ergeben - sonst
        # waere die Modusanforderung wirkungslos.
        paare = list(gesehen.values())
        self.assertNotEqual(paare[0], paare[1])

    def test_objective_fit_braucht_keine_modusspezifische_regel(self):
        """Dasselbe Modul, nur andere Anforderungen - kein `if modus ==`."""
        quelltext = (objective.__file__ or "")
        with open(quelltext, encoding="utf-8") as datei:
            inhalt = datei.read()
        for name in ("heist", "gem_grab", "brawl_ball", "knockout", "bounty",
                     "safe zone", "Safe Zone"):
            self.assertNotIn(f'"{name}"', inhalt,
                             f"objective.py darf {name} nicht kennen")


class AbgeleiteteGroessenTest(DrafterTest):
    """objective_sustain und objective_defense sind abgeleitet, nicht gepflegt."""

    def test_aus_vorhandenen_eigenschaften(self):
        b = self.brawler("gale")
        sustain = objective.objective_sustain(b)
        verteidigung = objective.objective_defense(b)
        self.assertIsNotNone(sustain)
        self.assertLessEqual(sustain, b.wert_oder("objective_damage"))
        self.assertLessEqual(sustain, b.wert_oder("sustained_damage"))
        self.assertGreaterEqual(verteidigung, 0.0)
        self.assertLessEqual(verteidigung, 1.0)

    def test_ohne_profil_keine_ableitung(self):
        ohne = Brawler.objects.create(name="NOR", slug="nor", external_id="17999",
                                      is_active=True)
        self.assertIsNone(objective.objective_sustain(ohne))
        self.assertIsNone(objective.objective_defense(ohne))

    def test_kein_neues_basisattribut(self):
        from drafter import attributes as attr
        for name in ("objective_sustain", "objective_defense"):
            self.assertNotIn(name, attr.ATTRIBUT_KEYS,
                             f"{name} soll abgeleitet bleiben, kein Pflegefeld")


class NamensumbenennungTest(DrafterTest):
    """safe_damage hiess nie, was es zu heissen schien."""

    def test_alter_schluessel_ist_weg(self):
        from drafter import attributes as attr
        self.assertNotIn("safe_damage", attr.ATTRIBUT_KEYS)
        self.assertIn("safe_poke", attr.ATTRIBUT_KEYS)

    def test_altdaten_lassen_sich_umschreiben(self):
        from drafter import attributes as attr
        alt = {"safe_damage": 70, "long_range": 80}
        self.assertEqual(attr.umbenennen(alt), {"safe_poke": 70, "long_range": 80})

    def test_datenbank_kennt_den_alten_schluessel_nicht_mehr(self):
        for b in Brawler.objects.all():
            self.assertNotIn("safe_damage", b.attributes or {}, b.slug)
        for m in BrawlMap.objects.all():
            self.assertNotIn("safe_damage", m.requirements or {}, m.slug)
        for g in GameMode.objects.all():
            self.assertNotIn("safe_damage", g.base_requirements or {}, g.slug)


class HeistProfilTest(DrafterTest):
    """Das Modusziel steht im Modus, nicht in der Map."""

    def test_heist_verlangt_auch_dauerschaden(self):
        heist = GameMode.objects.get(slug="heist")
        self.assertGreater(heist.base_requirements.get("sustained_damage", 0), 0,
                           "ein Safe faellt nicht von einem Burst")
        self.assertGreater(heist.base_requirements.get("objective_damage", 0), 0)

    def test_map_wiederholt_den_modus_nicht(self):
        karte = BrawlMap.objects.get(slug="safe-zone")
        modus = karte.game_mode.base_requirements
        for key, wert in (karte.requirements or {}).items():
            self.assertNotEqual(
                wert, modus.get(key),
                f"{key} steht identisch in Map und Modus - dann gehoert es in den Modus")
