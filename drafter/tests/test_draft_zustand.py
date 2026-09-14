"""Der Draftzustand: was gewaehlt werden darf und was nicht."""

from drafter.services.context import DraftFehler
from drafter.tests.basis import DrafterTest


class VerfuegbarkeitTest(DrafterTest):
    def test_gebannter_brawler_wird_nicht_empfohlen(self):
        empfehlungen = self.engine(bans=["gale"]).empfehlungen(anzahl=50)
        self.assertIsNone(self.rang(empfehlungen, "gale"))

    def test_gepickter_brawler_wird_nicht_erneut_angeboten(self):
        empfehlungen = self.engine(
            eigene=["gale"], gegner=["buster"]
        ).empfehlungen(anzahl=50)
        self.assertIsNone(self.rang(empfehlungen, "gale"))
        self.assertIsNone(self.rang(empfehlungen, "buster"))

    def test_alle_uebrigen_bleiben_waehlbar(self):
        ctx = self.context(eigene=["gale"], gegner=["buster"], bans=["tick"])
        empfehlungen = self.engine(
            eigene=["gale"], gegner=["buster"], bans=["tick"]
        ).empfehlungen(anzahl=50)
        self.assertEqual(len(empfehlungen), 20 - 3)


class ZustandspruefungTest(DrafterTest):
    def test_derselbe_brawler_in_beiden_teams_ist_ein_fehler(self):
        with self.assertRaises(DraftFehler) as fehler:
            self.context(eigene=["gale"], gegner=["gale"]).pruefe()
        self.assertIn("Gale", str(fehler.exception))

    def test_gebannt_und_gepickt_ist_ein_fehler(self):
        with self.assertRaises(DraftFehler):
            self.context(eigene=["gale"], bans=["gale"]).pruefe()

    def test_zu_viele_picks_sind_ein_fehler(self):
        with self.assertRaises(DraftFehler):
            self.context(eigene=["gale", "belle", "max", "tick"]).pruefe()

    def test_map_muss_zum_modus_passen(self):
        ctx = self.context()
        falsche_map = self.karte("safe-zone")   # Heist statt Gem Grab
        from dataclasses import replace
        with self.assertRaises(DraftFehler):
            replace(ctx, brawl_map=falsche_map).pruefe()

    def test_abweichende_reihenfolge_ist_nur_ein_hinweis(self):
        # Zwei eigene Picks, null gegnerische - laut 1-2-2-1 unmoeglich.
        # Die Engine soll trotzdem rechnen, aber darauf hinweisen.
        hinweise = self.context(eigene=["gale", "belle"], first_pick=True).pruefe()
        self.assertTrue(hinweise)
        self.assertIn("1-2-2-1", hinweise[0])


class ReihenfolgeTest(DrafterTest):
    def test_erster_pick_gehoert_dem_first_pick_team(self):
        self.assertEqual(self.context(first_pick=True).am_zug, "own")
        self.assertEqual(self.context(first_pick=False).am_zug, "enemy")

    def test_letzter_pick_gehoert_dem_team_ohne_first_pick(self):
        # Nach fuenf Picks ist Slot 6 dran - der gehoert 'second'.
        ctx = self.context(
            eigene=["gale", "belle"], gegner=["buster", "gene"], first_pick=True
        )
        # Bei 4 Picks ist laut Reihenfolge wieder 'first' am Zug.
        self.assertEqual(ctx.am_zug, "own")
        ctx = self.context(
            eigene=["gale", "belle", "max"], gegner=["buster", "gene"], first_pick=True
        )
        self.assertEqual(ctx.am_zug, "enemy")

    def test_draft_ende_wird_erkannt(self):
        ctx = self.context(
            eigene=["gale", "belle", "max"], gegner=["buster", "gene", "tick"]
        )
        self.assertTrue(ctx.draft_fertig)
        self.assertIsNone(ctx.am_zug)
