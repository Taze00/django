"""Persoenliche Sicherheit - wirkt, aber nur im erlaubten Rahmen."""

from drafter import config
from drafter.services import personal
from drafter.tests.basis import DrafterTest


class PersoenlicheConfidenceTest(DrafterTest):
    def _personal(self, slug, wert, **extra):
        eintrag = {"confidence": wert, "favorite": False, "avoid": False}
        eintrag.update(extra)
        return {self.brawler(slug).id: eintrag}

    def test_hohe_sicherheit_hebt_den_pick(self):
        ohne = self.engine(gegner=["bull"]).empfehlungen(anzahl=50)
        mit = self.engine(
            gegner=["bull"], personal=self._personal("belle", 100)
        ).empfehlungen(anzahl=50)
        self.assertGreater(self.score(mit, "belle"), self.score(ohne, "belle"))

    def test_niedrige_sicherheit_senkt_den_pick(self):
        ohne = self.engine(gegner=["bull"]).empfehlungen(anzahl=50)
        mit = self.engine(
            gegner=["bull"], personal=self._personal("gale", 0)
        ).empfehlungen(anzahl=50)
        self.assertLess(self.score(mit, "gale"), self.score(ohne, "gale"))

    def test_sicherheit_macht_aus_einem_schlechten_pick_keinen_guten(self):
        """Die wichtigste Leitplanke des Systems.

        Ein Brawler, der im Draft weit hinten liegt, darf durch maximale
        persoenliche Sicherheit nicht an die Spitze rutschen. Sonst
        bestaetigt das Werkzeug nur noch die eigene Gewohnheit, statt
        Draften beizubringen.
        """
        lage = dict(eigene=["bull", "frank"], gegner=["belle", "piper"])
        ohne = self.engine(**lage).empfehlungen(anzahl=50)

        # Den schlechtesten Kandidaten nehmen und maximal aufwerten.
        schlechtester = ohne[-1].brawler.slug
        mit = self.engine(
            **lage, personal=self._personal(schlechtester, 100, favorite=True)
        ).empfehlungen(anzahl=50)

        self.assertGreater(self.rang(mit, schlechtester), 3)
        differenz = self.score(mit, schlechtester) - self.score(ohne, schlechtester)
        self.assertLessEqual(differenz, config.PERSOENLICH_MAX_AUSSCHLAG + 1e-6)

    def test_ausschlag_ist_in_jeder_phase_gedeckelt(self):
        for phase_lage in ({}, dict(eigene=["gale", "belle"], gegner=["bull", "tick"])):
            ohne = self.engine(**phase_lage).empfehlungen(anzahl=50)
            # Nur Brawler pruefen, die in dieser Lage ueberhaupt noch
            # waehlbar sind - gepickte stehen zu Recht nicht mehr drin.
            im_draft = set(phase_lage.get("eigene", ())) | set(phase_lage.get("gegner", ()))
            for slug in {"mortis", "piper", "gale", "colette"} - im_draft:
                mit = self.engine(
                    **phase_lage, personal=self._personal(slug, 100)
                ).empfehlungen(anzahl=50)
                differenz = abs(self.score(mit, slug) - self.score(ohne, slug))
                self.assertLessEqual(
                    differenz, config.PERSOENLICH_MAX_AUSSCHLAG + 1e-6,
                    msg=f"{slug} verschiebt sich um {differenz}",
                )

    def test_vermeiden_wirkt_staerker_als_eine_niedrige_zahl(self):
        ohne = self.engine().empfehlungen(anzahl=50)
        nur_niedrig = self.engine(personal=self._personal("gale", 20)).empfehlungen(anzahl=50)
        vermeiden = self.engine(
            personal=self._personal("gale", 20, avoid=True)
        ).empfehlungen(anzahl=50)
        self.assertLess(self.score(vermeiden, "gale"), self.score(nur_niedrig, "gale"))
        self.assertLess(self.score(nur_niedrig, "gale"), self.score(ohne, "gale"))


class SessionTest(DrafterTest):
    def test_gastwerte_kommen_aus_der_session(self):
        class FakeRequest:
            user = None
            session = {personal.SESSION_SCHLUESSEL: {"gale": 90, "unbekannt": 50}}

        werte = personal.laden(FakeRequest(), list(self.brawler("gale").__class__.objects.all()))
        self.assertEqual(werte[self.brawler("gale").id]["confidence"], 90)
        self.assertEqual(len(werte), 1)   # unbekannter Slug wird ignoriert

    def test_unsinnige_sessionwerte_werden_verworfen(self):
        class FakeRequest:
            user = None
            session = {personal.SESSION_SCHLUESSEL: {"gale": "viel"}}

        werte = personal.laden(FakeRequest(), list(self.brawler("gale").__class__.objects.all()))
        self.assertEqual(werte, {})
