# -*- coding: utf-8 -*-
"""Ein kaputter Eintrag darf nie einen ganzen Battlelog kosten.

Hintergrund: am 2026-09-17 nahm ein Fehler mitten im Import eine bereits
gespeicherte Rohantwort wieder zurueck - samt 17 Partien, die nur in
dieser einen API-Antwort standen. Ohne die Antwort war der Fehler
hinterher nicht mehr nachvollziehbar und die Partien nur ueber einen
neuen Abruf zu bekommen.

Die Tests halten beide Lehren fest:
1. Die Rohantwort wird ZUERST und dauerhaft gespeichert.
2. Fehlschlaege gelten je Partie, nicht je Lieferung - mit einer Meldung,
   die Fingerprint, Partie-ID und Map/Modus-ID nennt.
"""

from unittest import mock

from django.db import DatabaseError

from drafter.models import BrawlMap, GameMode
from drafter.models.matches import Match, RawPayload
from drafter.services.ingest.importer import MatchImporter
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import FixtureMixin, partie


class ImportRobustheitTest(FixtureMixin, DrafterTest):
    def test_rohantwort_bleibt_wenn_der_import_scheitert(self):
        echt = MatchImporter._match

        def zweite_partie_scheitert(self, record, payload, quelle, bericht):
            if record.map == "Undermine":
                raise DatabaseError("simulierter Fehler beim Speichern")
            return echt(self, record, payload, quelle, bericht)

        with mock.patch.object(MatchImporter, "_match", zweite_partie_scheitert):
            bericht = self.importiere(
                partie(karte="Hard Rock Mine"),
                partie(karte="Undermine", minuten=10),
                partie(karte="Hard Rock Mine", minuten=20),
            )

        self.assertEqual(bericht.fehlerhaft, 1)
        self.assertEqual(bericht.neu, 2, "die anderen beiden Partien stehen")
        self.assertEqual(RawPayload.objects.count(), 1, "die Rohantwort bleibt erhalten")
        payload = RawPayload.objects.get()
        self.assertEqual(payload.payload["matches"][1]["map"], "Undermine")

    def test_fehlermeldung_nennt_fingerprint_und_ids(self):
        def scheitert(self, record, payload, quelle, bericht):
            raise DatabaseError("simulierter Fehler")

        with mock.patch.object(MatchImporter, "_match", scheitert):
            bericht = self.importiere(partie(karte="Undermine", modus="Gem Grab"))

        meldung = " ".join(bericht.meldungen)
        self.assertIn("fingerprint", meldung)
        self.assertIn("Undermine", meldung)
        self.assertIn("Gem Grab", meldung)
        self.assertIn("Partie-ID", meldung)

    def test_verlorene_partien_sind_aus_der_rohantwort_wiederholbar(self):
        """Der eigentliche Zweck: nach einem Fehler reicht ein zweiter Lauf."""
        echt = MatchImporter._match
        fehlerhaft = {"an": True}

        def einmal_scheitern(self, record, payload, quelle, bericht):
            if fehlerhaft["an"] and record.map == "Undermine":
                raise DatabaseError("simulierter Fehler")
            return echt(self, record, payload, quelle, bericht)

        pfad = self.schreibe(self._datei_mit_zwei_partien())
        with mock.patch.object(MatchImporter, "_match", einmal_scheitern):
            MatchImporter(self._provider(pfad)).ausfuehren()
        self.assertEqual(Match.objects.count(), 1)

        # Zweiter Anlauf aus derselben Datei - die Rohantwort liegt vor,
        # die fehlende Partie kommt nach, die vorhandene bleibt Dublette.
        fehlerhaft["an"] = False
        bericht = MatchImporter(self._provider(pfad)).ausfuehren()
        self.assertEqual(Match.objects.count(), 2)
        self.assertEqual(bericht.bereits_importiert, 1,
                         "dieselbe Rohantwort wird nicht doppelt gespeichert")

    def _datei_mit_zwei_partien(self):
        from drafter.tests.fixture_helfer import datei
        return datei([partie(karte="Hard Rock Mine"), partie(karte="Undermine", minuten=10)])

    def _provider(self, pfad):
        from drafter.services.providers.fixture import FixtureDataProvider
        return FixtureDataProvider(pfad)


class GleicherNameAndereIdTest(FixtureMixin, DrafterTest):
    """Map-/Modus-Identitaet haengt an der API-ID, nicht am Namen."""

    def importiere_mit_katalog(self, *matches):
        from drafter.services.providers.fixture import FixtureDataProvider
        from drafter.tests.fixture_helfer import datei
        pfad = self.schreibe(datei(matches, herkunft="synthetisch"))
        return MatchImporter(FixtureDataProvider(pfad), katalog_ergaenzen=True).ausfuehren()

    def test_zwei_ids_mit_demselben_namen_zerstoeren_den_import_nicht(self):
        bericht = self.importiere_mit_katalog(
            partie(karte="Doppelname", modus="Brawl Ball", map_id="901",
                   mode_id="801"),
            partie(karte="Doppelname", modus="Brawl Ball", map_id="902",
                   mode_id="801", minuten=10),
        )
        self.assertEqual(bericht.neu, 2)
        self.assertEqual(bericht.fehlerhaft, 0)
        # Eine der beiden IDs bekommt den Eintrag, die andere wird gemeldet
        # statt geraten - und die Partie wird trotzdem gespeichert.
        self.assertTrue(bericht.id_widersprueche)
        gespeichert = set(Match.objects.values_list("external_map_id", flat=True))
        self.assertEqual(gespeichert, {"901", "902"})

    def test_gleicher_modusname_andere_id_bekommt_eigenen_eintrag(self):
        self.importiere_mit_katalog(
            partie(modus="Wipeout", karte="Karte A", mode_id="701",
                   map_id="911"),
            partie(modus="Wipeout", karte="Karte B", mode_id="702",
                   map_id="912", minuten=10),
        )
        ids = set(GameMode.objects.filter(external_id__in=["701", "702"])
                  .values_list("external_id", flat=True))
        self.assertEqual(ids, {"701", "702"}, "die ID entscheidet, nicht der Name")

    def test_katalogfehler_kostet_nur_den_katalogeintrag(self):
        """Laesst sich der Eintrag nicht anlegen, wird die Partie trotzdem gespeichert."""
        from django.db import IntegrityError

        echt = BrawlMap.objects.create

        def scheitert(**felder):
            if felder.get("external_id") == "903":
                raise IntegrityError("simulierter Slug-Konflikt")
            return echt(**felder)

        with mock.patch.object(BrawlMap.objects, "create", scheitert):
            bericht = self.importiere_mit_katalog(
                partie(karte="Neue Karte", modus="Brawl Ball", map_id="903",
                       mode_id="803"),
            )
        self.assertEqual(bericht.neu, 1)
        self.assertEqual(bericht.fehlerhaft, 0)
        self.assertTrue(bericht.id_widersprueche)
        self.assertFalse(BrawlMap.objects.filter(external_id="903").exists())
        self.assertEqual(Match.objects.get().external_map_id, "903",
                         "die Partie behält ihre Map-ID, auch ohne Katalogeintrag")
