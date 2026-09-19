# -*- coding: utf-8 -*-
"""Portraits: gleiche Flaeche, eindeutige Zuordnung, sauberer Rueckfall.

Die Fan-Kit-Portraits haben sehr verschiedene Seitenverhaeltnisse
(gemessen am 2026-09-20: 160x108 bis 160x160). Im quadratischen Rahmen
der Oberflaeche wirken sie dadurch unterschiedlich gross. Die Pipeline
legt sie deshalb proportional auf eine einheitliche quadratische Flaeche -
ohne Zuschnitt, ohne Verzerrung, ohne die Originale anzufassen.
"""

from pathlib import Path

from django.conf import settings

from drafter.models import Brawler
from drafter.tests.basis import DrafterTest

FANKIT = Path(settings.BASE_DIR) / "static" / "drafter" / "fankit" / "brawler"


class QuadratTest(DrafterTest):
    """Die eine Rechnung, auf die es ankommt."""

    def kommando(self):
        from drafter.management.commands.import_fankit_bilder import Command
        return Command()

    def bild(self, breite, hoehe, farbe=(255, 0, 0, 255)):
        from PIL import Image
        return Image.new("RGBA", (breite, hoehe), farbe)

    def test_breites_bild_wird_quadratisch_ohne_verzerrung(self):
        from PIL import Image
        quelle = self.bild(160, 108)
        fertig = self.kommando()._auf_quadrat(quelle, 160, Image)
        self.assertEqual(fertig.size, (160, 160))
        sichtbar = fertig.split()[3].getbbox()
        self.assertEqual((sichtbar[2] - sichtbar[0], sichtbar[3] - sichtbar[1]),
                         (160, 108), "das Motiv darf nicht gestreckt werden")

    def test_motiv_wird_zentriert(self):
        from PIL import Image
        fertig = self.kommando()._auf_quadrat(self.bild(160, 100), 160, Image)
        oben = fertig.split()[3].getbbox()[1]
        unten = 160 - fertig.split()[3].getbbox()[3]
        self.assertLessEqual(abs(oben - unten), 1)

    def test_zu_grosses_bild_wird_proportional_verkleinert(self):
        from PIL import Image
        fertig = self.kommando()._auf_quadrat(self.bild(800, 400), 160, Image)
        self.assertEqual(fertig.size, (160, 160))
        sichtbar = fertig.split()[3].getbbox()
        breite, hoehe = sichtbar[2] - sichtbar[0], sichtbar[3] - sichtbar[1]
        self.assertEqual(breite, 160)
        self.assertAlmostEqual(breite / hoehe, 2.0, delta=0.05)

    def test_bereits_quadratisch_bleibt_unangetastet(self):
        from PIL import Image
        self.assertIsNone(self.kommando()._auf_quadrat(self.bild(160, 160), 160, Image))


class RueckfallTest(DrafterTest):
    """Ohne Bild muss etwas Konsistentes dastehen."""

    def test_jeder_brawler_hat_initialen(self):
        for b in Brawler.objects.all():
            self.assertTrue(b.initialen, b.slug)
            self.assertLessEqual(len(b.initialen), 3, b.slug)

    def test_ohne_bild_bleibt_die_url_leer_statt_kaputt(self):
        b = Brawler.objects.create(name="OHNE BILD", slug="ohne-bild",
                                   external_id="95001", is_active=True)
        self.assertEqual(b.image_url, "")
        self.assertTrue(b.initialen)


class BestandTest(DrafterTest):
    """Gegen den echten Dateibestand - uebersprungen, wo keiner liegt.

    Die Fan-Kit-Dateien sind gitignored (sie gehoeren Supercell), also
    laeuft dieser Test nur dort, wo sie tatsaechlich eingespielt sind.
    """

    def setUp(self):
        if not FANKIT.exists():
            self.skipTest("keine Fan-Kit-Dateien eingespielt")

    def test_alle_portraits_sind_quadratisch_und_gleich_gross(self):
        from PIL import Image
        groessen = set()
        for datei in sorted(FANKIT.glob("*.png")):
            with Image.open(datei) as bild:
                groessen.add(bild.size)
                self.assertEqual(bild.size[0], bild.size[1], datei.name)
        self.assertEqual(len(groessen), 1,
                         f"uneinheitliche Flächen: {sorted(groessen)}")

    def test_jeder_gepflegte_ranked_brawler_hat_ein_portrait(self):
        """Fuer jeden Namen der Fachliste muss eine Basisdatei aufloesen.

        Geprueft wird gegen die gepflegte Namensliste (fachdaten), nicht
        gegen die Datenbank: der volle Katalog von 106 Ranked-Brawlern
        steht im Betrieb, die Tests laufen auf dem Demo-Seed. Die Liste
        kennt 101 Namen - die uebrigen sind neuer als sie.
        """
        from drafter.fachdaten import role_ability_map as fach
        from drafter.services.ingest.fingerprint import katalog_schluessel

        namen = [n for n in fach.alle_namen() if n not in fach.NICHT_RANKED]
        self.assertGreaterEqual(len(namen), 99, "Namensliste unerwartet kurz")
        vorhanden = {d.stem for d in FANKIT.glob("*.png")}
        ohne = sorted(katalog_schluessel(fach.ALIASE.get(n.lower(), n))
                      for n in namen)
        fehlt = [s for s in ohne if s not in vorhanden]
        self.assertFalse(fehlt, f"ohne Portrait: {fehlt}")

    def test_dateinamen_sind_katalogschluessel(self):
        """Jede Datei heisst wie ihr Brawler - nicht wie eine Skin-Datei.

        `katalog_schluessel` ist dieselbe Identitaet, mit der die
        Oberflaeche und der Import zuordnen. Ein Dateiname, der sie nicht
        ueberlebt, gehoert zu keinem Brawler und wuerde nie angezeigt.
        """
        from drafter.services.ingest.fingerprint import katalog_schluessel
        for datei in sorted(FANKIT.glob("*.png")):
            self.assertEqual(katalog_schluessel(datei.stem), datei.stem,
                             f"{datei.name} ist kein Katalogschlüssel")

    def test_keine_skin_datei_als_portrait(self):
        """Hyper- und Skin-Varianten duerfen nie als Basisbild landen."""
        namen = {d.stem for d in FANKIT.glob("*.png")}
        for verdaechtig in ("hyper-colt", "hyper-dynamike", "tiger-leon",
                            "sirius-mask", "buzz-lightyear"):
            self.assertNotIn(verdaechtig, namen)
