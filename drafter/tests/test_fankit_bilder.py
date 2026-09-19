"""Import der Fan-Kit-Bilder und das Bild-URL-Feld.

Die Testbilder sind hier erzeugte Farbflaechen - keine Supercell-Dateien.
Geprueft wird die Zuordnung und was mit den Dateien passiert, nicht ihr
Inhalt.
"""

import io
import json
import tempfile
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management import call_command
from PIL import Image

from drafter.management.commands.import_fankit_bilder import schluessel
from drafter.models import Brawler, BrawlMap
from drafter.models.base import pruefe_bild_url
from drafter.tests.basis import DrafterTest


def bild_schreiben(pfad, groesse=(512, 512)):
    Image.new("RGBA", groesse, (200, 80, 40, 255)).save(pfad)


class SchluesselTest(DrafterTest):
    def test_fuellwoerter_trennzeichen_und_versionsnummern_fallen_weg(self):
        self.assertEqual(schluessel("Gale_Portrait_02"), "gale")
        self.assertEqual(schluessel("el-primo portrait"), "elprimo")
        self.assertEqual(schluessel("Mr. P"), "mrp")

    def test_ziffern_am_anfang_bleiben(self):
        self.assertEqual(schluessel("8-BIT"), "8bit")
        self.assertEqual(schluessel("8_bit_portrait_1"), "8bit")


class BildUrlTest(DrafterTest):
    def test_pfad_auf_dem_eigenen_server_ist_erlaubt(self):
        pruefe_bild_url("/static/drafter/fankit/brawler/gale.png?v=1234abcd")
        pruefe_bild_url("https://example.org/gale.png")
        pruefe_bild_url("")

    def test_protokollrelative_und_kaputte_werte_werden_abgewiesen(self):
        for wert in ("//fremd.example/gale.png", "gale.png", "javascript:alert(1)"):
            with self.assertRaises(ValidationError, msg=wert):
                pruefe_bild_url(wert)

    def test_modell_validiert_das_feld(self):
        gale = self.brawler("gale")
        gale.image_url = "/static/drafter/fankit/brawler/gale.png"
        gale.full_clean()


class ImportTest(DrafterTest):
    def setUp(self):
        self.quelle = Path(tempfile.mkdtemp())
        self.ziel = Path(tempfile.mkdtemp())

    def importieren(self, *extra, **opts):
        ausgabe = io.StringIO()
        call_command("import_fankit_bilder", *extra, ziel=str(self.ziel),
                     ohne_collectstatic=True, stdout=ausgabe, **opts)
        return ausgabe.getvalue()

    def test_eindeutige_dateien_werden_zugeordnet_und_verkleinert(self):
        bild_schreiben(self.quelle / "Gale_Portrait.png")
        bild_schreiben(self.quelle / "El_Primo_portrait.png")
        self.importieren(brawler=str(self.quelle))

        url = self.brawler("gale").image_url
        self.assertRegex(url, r"^/static/drafter/fankit/brawler/gale\.png\?v=[0-9a-f]{8}$")
        with Image.open(self.ziel / "brawler" / "gale.png") as bild:
            # proportional verkleinert, nicht beschnitten
            self.assertEqual(bild.size, (160, 160))

    def test_seitenverhaeltnis_bleibt_erhalten(self):
        """Quadratische Flaeche, unverzerrtes Motiv.

        Seit dem 2026-09-20 landet jedes Portrait auf einer einheitlichen
        quadratischen Leinwand - sonst wirken Brawler im gleich grossen
        Rahmen der Oberflaeche verschieden gross. Das Motiv selbst wird
        dabei nur proportional verkleinert, nie gestreckt und nie
        beschnitten: die sichtbare Flaeche behaelt ihr Verhaeltnis.
        """
        bild_schreiben(self.quelle / "Gale.png", groesse=(400, 800))
        self.importieren(brawler=str(self.quelle))
        with Image.open(self.ziel / "brawler" / "gale.png") as bild:
            self.assertEqual(bild.size, (160, 160))
            sichtbar = bild.convert("RGBA").split()[3].getbbox()
            breite = sichtbar[2] - sichtbar[0]
            hoehe = sichtbar[3] - sichtbar[1]
            self.assertEqual((breite, hoehe), (80, 160))

    def test_mehrdeutige_dateien_werden_nicht_geraten(self):
        bild_schreiben(self.quelle / "gale_portrait_1.png")
        bild_schreiben(self.quelle / "gale-portrait.png")
        ausgabe = self.importieren(brawler=str(self.quelle))
        self.assertIn("Mehrdeutig", ausgabe)
        self.assertEqual(self.brawler("gale").image_url, "")

    def test_zuordnung_loest_mehrdeutigkeit_und_unbekannte_namen(self):
        bild_schreiben(self.quelle / "gale_portrait_1.png")
        bild_schreiben(self.quelle / "gale-portrait.png")
        bild_schreiben(self.quelle / "unbekannt_42x.png")
        zuordnung = self.quelle / "zuordnung.json"
        zuordnung.write_text(json.dumps({
            "gale-portrait.png": "gale", "unbekannt_42x.png": "sandy",
        }))
        self.importieren(brawler=str(self.quelle), zuordnung=str(zuordnung))
        self.assertTrue(self.brawler("gale").image_url)
        self.assertTrue(self.brawler("sandy").image_url)

    def test_ohne_treffer_wird_gemeldet(self):
        bild_schreiben(self.quelle / "gibt_es_nicht.png")
        ausgabe = self.importieren(brawler=str(self.quelle))
        self.assertIn("Ohne Treffer", ausgabe)
        self.assertIn("gibt_es_nicht.png", ausgabe)

    def test_trockenlauf_schreibt_nichts(self):
        bild_schreiben(self.quelle / "Gale.png")
        self.importieren(brawler=str(self.quelle), trocken=True)
        self.assertEqual(self.brawler("gale").image_url, "")
        self.assertFalse((self.ziel / "brawler").exists())

    def test_fremdes_bild_wird_nicht_ueberschrieben(self):
        Brawler.objects.filter(slug="gale").update(image_url="https://example.org/gale.png")
        bild_schreiben(self.quelle / "Gale.png")
        self.importieren(brawler=str(self.quelle))
        self.assertEqual(self.brawler("gale").image_url, "https://example.org/gale.png")

    def test_maps_ueber_namen(self):
        bild_schreiben(self.quelle / "Hard_Rock_Mine.png", groesse=(600, 1000))
        self.importieren(maps=str(self.quelle))
        karte = BrawlMap.objects.get(slug="hard-rock-mine")
        self.assertTrue(karte.image_url.startswith("/static/drafter/fankit/maps/hard-rock-mine.png"))
        # Quadratisch wird nur das Portrait: eine Map ist ein Spielfeld
        # und behaelt ihr Seitenverhaeltnis.
        with Image.open(self.ziel / "maps" / "hard-rock-mine.png") as bild:
            self.assertEqual(bild.size, (144, 240))

    def test_api_liefert_die_bilder_an_allen_stellen(self):
        from django.urls import reverse
        bild_schreiben(self.quelle / "Gale.png")
        self.importieren(brawler=str(self.quelle))
        url = self.brawler("gale").image_url

        katalog = self.client.get(reverse("drafter:api_katalog")).json()
        self.assertEqual(next(b for b in katalog["brawler"] if b["slug"] == "gale")["image_url"], url)
        antwort = self.client.post(
            reverse("drafter:api_recommend"), data=json.dumps({"map": "hard-rock-mine"}),
            content_type="application/json",
        ).json()
        for liste in (antwort["empfehlungen"], antwort["ban_empfehlungen"]):
            for eintrag in liste:
                if eintrag["slug"] == "gale":
                    self.assertEqual(eintrag["image_url"], url)
