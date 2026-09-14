"""Teamprofil, Luecken und Redundanz - der Kern gegen die Tierlist."""

from drafter import config
from drafter.services.team_coverage import (
    Teamanalyse, anforderungen_mit_gegner, teamprofil,
)
from drafter.tests.basis import DrafterTest


class TeamprofilTest(DrafterTest):
    def test_zwei_halbe_antworten_ergeben_keine_ganze(self):
        # Zwei Brawler mit mittlerem Anti-Tank duerfen zusammen nicht so
        # dastehen, als haette das Team einen echten Anti-Tank.
        gale = self.brawler("gale")        # anti_tank 90
        colette = self.brawler("colette")  # anti_tank 95
        einzeln = teamprofil([gale])["anti_tank"]
        zusammen = teamprofil([gale, colette])["anti_tank"]
        self.assertGreater(zusammen, einzeln)
        self.assertLessEqual(zusammen, 1.0)
        # Der Zuwachs des zweiten ist deutlich kleiner als der des ersten.
        self.assertLess(zusammen - einzeln, einzeln)

    def test_profil_ist_nicht_der_mittelwert(self):
        # Ein Spezialist darf die Deckung nicht senken, nur weil der
        # zweite Brawler in derselben Eigenschaft schwach ist.
        piper = self.brawler("piper")      # long_range 95
        bull = self.brawler("bull")        # long_range 0
        allein = teamprofil([piper])["long_range"]
        zu_zweit = teamprofil([piper, bull])["long_range"]
        self.assertEqual(allein, zu_zweit)

    def test_deckungsgrad_steigt_mit_passenden_picks(self):
        anforderungen = self.karte().anforderungs_vektor()
        leer = Teamanalyse.bauen([], anforderungen).deckungsgrad()
        besetzt = Teamanalyse.bauen(
            [self.brawler("gale"), self.brawler("belle")], anforderungen
        ).deckungsgrad()
        self.assertEqual(leer, 0.0)
        self.assertGreater(besetzt, 0.3)


class LueckenTest(DrafterTest):
    def test_gegnerteam_erzeugt_eigene_anforderungen(self):
        # Keine Map verlangt "Anti-Thrower" - ein gegnerischer Tick schon.
        basis = self.karte("belles-rock").anforderungs_vektor()
        self.assertLess(basis.get("anti_thrower", 0), 0.3)
        erweitert = anforderungen_mit_gegner(basis, [self.brawler("tick")])
        self.assertGreater(erweitert["anti_thrower"], 0.8)

    def test_map_anforderung_wird_vom_gegner_nicht_verwaessert(self):
        basis = self.karte("belles-rock").anforderungs_vektor()
        erweitert = anforderungen_mit_gegner(basis, [self.brawler("bull")])
        self.assertGreaterEqual(erweitert["long_range"], basis["long_range"])

    def test_fehlender_anti_tank_wird_als_kritische_luecke_erkannt(self):
        engine = self.engine(eigene=["piper"], gegner=["bull", "frank"])
        luecken = {e.key for e, _ in engine.eigene_analyse.kritische_luecken()}
        self.assertIn("anti_tank", luecken)


class RedundanzTest(DrafterTest):
    def test_dritter_tank_wird_abgestraft(self):
        engine = self.engine(eigene=["bull", "frank"], gegner=["belle"])
        empfehlungen = engine.empfehlungen(anzahl=50)

        dritter_tank = self.rang(empfehlungen, "rosa")
        reichweite = self.rang(empfehlungen, "piper")
        self.assertIsNotNone(dritter_tank)
        self.assertLess(reichweite, dritter_tank)

        # Und die Strafe ist auch benannt, nicht nur eingepreist.
        for e in empfehlungen:
            if e.brawler.slug == "rosa":
                self.assertLess(e.komponenten[config.K_REDUNDANCY].wert, 0)
                gruende = " ".join(g.text for g in e.gruende(positiv=False))
                self.assertIn("Tank", gruende)
                break

    def test_anti_tank_steigt_gegen_tanks(self):
        ohne = self.engine(gegner=["belle", "piper"]).empfehlungen(anzahl=50)
        mit = self.engine(gegner=["bull", "frank"]).empfehlungen(anzahl=50)
        self.assertLess(self.rang(mit, "colette"), self.rang(ohne, "colette"))
