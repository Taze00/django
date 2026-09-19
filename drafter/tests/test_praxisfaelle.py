# -*- coding: utf-8 -*-
"""Das Protokoll des Praxistests.

Wichtigste Zusicherung: **Eintragen veraendert nichts.** Ein
Testdatensatz, der das System beeinflusst, das er pruefen soll, beweist
nichts mehr - deshalb pruefen mehrere Tests genau das.
"""

import io

from django.core.management import call_command
from django.core.management.base import CommandError

from drafter.models import (
    Brawler, BrawlerStat, BrawlMap, CounterStat, Ergebnis, Fehlerklasse,
    Praxisfall, SynergyStat,
)
from drafter.tests.basis import DrafterTest


class EintragenTest(DrafterTest):
    def eintragen(self, **extra):
        ausgabe = io.StringIO()
        call_command("praxisfall", map=self.karte().slug, stdout=ausgabe, **extra)
        return Praxisfall.objects.order_by("-id").first(), ausgabe.getvalue()

    def test_ein_fall_haelt_die_empfehlungen_fest(self):
        fall, ausgabe = self.eintragen(gewaehlt="gale")
        self.assertIsNotNone(fall)
        self.assertEqual(fall.brawl_map, self.karte())
        self.assertTrue(fall.empfehlungen, "der Schnappschuss fehlt")
        self.assertEqual(fall.gewaehlt, "gale")
        self.assertIn("gespeichert", ausgabe)

    def test_der_schnappschuss_enthaelt_die_erklaerung(self):
        """Ohne sie waere der Fall spaeter nicht nachvollziehbar."""
        fall, _ = self.eintragen()
        erste = fall.empfehlungen[0]
        self.assertIn("erklaerung", erste)
        for teil in ("current_strength", "draft_fit", "personal",
                     "data_coverage", "statistical_confidence"):
            self.assertIn(teil, erste["erklaerung"], teil)
        self.assertIn("komponenten", erste)
        quellen = {k["quelle"] for k in erste["komponenten"]}
        self.assertTrue(quellen, "die Quellen gehoeren mit ins Protokoll")

    def test_rang_des_gewaehlten_wird_berechnet(self):
        fall, _ = self.eintragen(tiefe=200)
        spitze = fall.spitze[0]
        zweiter, _ = self.eintragen(gewaehlt=spitze, tiefe=200)
        self.assertEqual(zweiter.gewaehlter_rang, 1)
        self.assertEqual(zweiter.gewaehlter_score, zweiter.empfehlungen[0]["score"])

    def test_pick_ausserhalb_der_liste_wird_vermerkt(self):
        # Ein Brawler, der es auf dieser Map nicht in die Spitze schafft.
        liste = self.engine().empfehlungen(anzahl=200)
        hinten = liste[-1].brawler.slug
        fall, ausgabe = self.eintragen(gewaehlt=hinten, tiefe=3)
        self.assertEqual(fall.gewaehlt, hinten)
        self.assertIsNone(fall.gewaehlter_rang)
        self.assertIn("stand nicht", ausgabe)

    def test_phase_kommt_aus_dem_kontext(self):
        leer, _ = self.eintragen()
        spaet, _ = self.eintragen(eigene="gale,sandy", gegner="bull,belle,brock",
                                  gegner_first=True)
        self.assertNotEqual(leer.draft_phase, spaet.draft_phase)
        self.assertEqual(spaet.enemy_picks, ["bull", "belle", "brock"])
        self.assertFalse(spaet.eigener_first_pick)

    def test_unbekannter_brawler_wird_gemeldet(self):
        with self.assertRaises(CommandError):
            self.eintragen(gewaehlt="gibtsnicht")

    def test_unwaehlbare_map_wird_gemeldet(self):
        with self.assertRaises(CommandError):
            call_command("praxisfall", map="gibtsnicht", stdout=io.StringIO())

    def test_modellstand_wird_mitgeschrieben(self):
        fall, _ = self.eintragen()
        self.assertTrue(fall.modellstand,
                        "ohne die Modellversion ist ein Fall nicht auswertbar")


class KeineRueckwirkungTest(DrafterTest):
    """Das Protokoll fuettert nichts zurueck."""

    def test_eintragen_aendert_keine_statistik(self):
        vorher = {
            "brawler": list(BrawlerStat.objects.values_list("id", "adjusted_rate")),
            "counter": list(CounterStat.objects.values_list("id", "advantage")),
            "synergie": list(SynergyStat.objects.values_list("id", "synergy")),
            "profile": list(Brawler.objects.values_list("id", "attributes",
                                                        "draft_values")),
            "maps": list(BrawlMap.objects.values_list("id", "requirements")),
        }
        call_command("praxisfall", map=self.karte().slug, gewaehlt="gale",
                     ergebnis="win", stdout=io.StringIO())
        self.assertEqual(
            vorher["brawler"],
            list(BrawlerStat.objects.values_list("id", "adjusted_rate")))
        self.assertEqual(
            vorher["counter"], list(CounterStat.objects.values_list("id", "advantage")))
        self.assertEqual(
            vorher["synergie"], list(SynergyStat.objects.values_list("id", "synergy")))
        self.assertEqual(
            vorher["profile"],
            list(Brawler.objects.values_list("id", "attributes", "draft_values")))
        self.assertEqual(
            vorher["maps"], list(BrawlMap.objects.values_list("id", "requirements")))

    def test_ein_fall_aendert_die_naechste_empfehlung_nicht(self):
        from drafter.services.anfrage import context_aus_daten
        from drafter.services.draft_engine import DraftEngine

        def spitze():
            return [(e.brawler.slug, e.anzeige_score) for e in
                    DraftEngine(context_aus_daten({"map": self.karte().slug}))
                    .empfehlungen(anzahl=10)]

        vorher = spitze()
        for _ in range(3):
            call_command("praxisfall", map=self.karte().slug, gewaehlt="gale",
                         ergebnis="loss", auffaellig=True, klasse="MODUS",
                         stdout=io.StringIO())
        self.assertEqual(vorher, spitze())

    def test_konkurrenz_wird_nur_protokolliert(self):
        call_command("praxisfall", map=self.karte().slug,
                     konkurrenz="Colette, PIPER, gale", stdout=io.StringIO())
        fall = Praxisfall.objects.latest("id")
        self.assertEqual(fall.competitor_top, ["colette", "piper", "gale"])
        # Keine Spur davon in den Empfehlungen.
        for e in fall.empfehlungen:
            self.assertNotIn("competitor", str(e).lower())

    def test_unbekannte_konkurrenz_wird_gemeldet_statt_gespeichert(self):
        """Ein nicht aufloesbarer Name darf nicht stumm im Protokoll landen.

        `overlap()` vergleicht die fremde Liste mit unseren Slugs. Ein
        Name, den der Katalog nicht kennt, trifft dort nie - die
        Uebereinstimmung saehe kleiner aus, als sie ist, und zwar ohne
        jeden Hinweis. Lieber abbrechen.
        """
        with self.assertRaises(CommandError) as fehler:
            call_command("praxisfall", map=self.karte().slug,
                         konkurrenz="gale,gibtsnicht", stdout=io.StringIO())
        self.assertIn("konkurrenz", str(fehler.exception))
        self.assertIn("gibtsnicht", str(fehler.exception))


class MarkierenTest(DrafterTest):
    def test_nachtraegliches_einordnen(self):
        call_command("praxisfall", map=self.karte().slug, stdout=io.StringIO())
        fall = Praxisfall.objects.latest("id")
        call_command("praxisfall", markieren=fall.id, klasse="PRIOR",
                     notiz="Sandy trägt ohne Messung", ergebnis="loss",
                     stdout=io.StringIO())
        fall.refresh_from_db()
        self.assertEqual(fall.fehlerklasse, Fehlerklasse.PRIOR)
        self.assertTrue(fall.auffaellig)
        self.assertEqual(fall.ergebnis, Ergebnis.NIEDERLAGE)
        self.assertIn("Sandy", fall.notizen)

    def test_kein_fehler_markiert_nicht_als_auffaellig(self):
        call_command("praxisfall", map=self.karte().slug, stdout=io.StringIO())
        fall = Praxisfall.objects.latest("id")
        call_command("praxisfall", markieren=fall.id, klasse="KEIN_FEHLER",
                     stdout=io.StringIO())
        fall.refresh_from_db()
        self.assertFalse(fall.auffaellig)


class OverlapTest(DrafterTest):
    def test_overlap_zaehlt_die_gemeinsamen(self):
        call_command("praxisfall", map=self.karte().slug, tiefe=10,
                     stdout=io.StringIO())
        fall = Praxisfall.objects.latest("id")
        unsere = fall.spitze
        fall.competitor_top = [unsere[0], "gibtsnicht", unsere[2]]
        fall.save()
        self.assertEqual(fall.overlap(1), 1)
        self.assertEqual(fall.overlap(3), 2)

    def test_ohne_fremde_liste_keine_zahl(self):
        call_command("praxisfall", map=self.karte().slug, stdout=io.StringIO())
        self.assertIsNone(Praxisfall.objects.latest("id").overlap(3))


class BerichtTest(DrafterTest):
    def bericht(self, **extra):
        ausgabe = io.StringIO()
        call_command("praxisbericht", stdout=ausgabe, **extra)
        return ausgabe.getvalue()

    def test_bericht_ohne_faelle(self):
        self.assertIn("Noch keine Fälle", self.bericht())

    def test_bericht_zeigt_verteilung_und_raenge(self):
        for gewaehlt in ("gale", "sandy", "belle"):
            call_command("praxisfall", map=self.karte().slug, gewaehlt=gewaehlt,
                         tiefe=200, stdout=io.StringIO())
        text = self.bericht()
        self.assertIn("Nach Modus", text)
        self.assertIn("Nach Draftphase", text)
        self.assertIn("Gewählte Empfehlung", text)
        self.assertIn("Noch keine Fälle aus", text)

    def test_wiederkehrende_fehlerklasse_wird_hervorgehoben(self):
        for _ in range(2):
            call_command("praxisfall", map=self.karte().slug, auffaellig=True,
                         klasse="PRIOR", notiz="Prior trägt", stdout=io.StringIO())
        text = self.bericht()
        self.assertIn("PRIOR", text)
        self.assertIn("wiederkehrend", text)

    def test_uebereinstimmung_wird_als_beobachtung_ausgewiesen(self):
        call_command("praxisfall", map=self.karte().slug, konkurrenz="gale,sandy",
                     stdout=io.StringIO())
        text = self.bericht()
        self.assertIn("Top1", text)
        self.assertIn("Kein Qualitätsmaß", text)
