# -*- coding: utf-8 -*-
"""Die Einzelanalyse zeigt die Bewertung - sie erzeugt keine zweite.

Ein Debug-Werkzeug ist nur so viel wert wie seine Treue zum Original.
Zeigte die Analyse andere Zahlen als die Empfehlung, wuerde man bei
jeder Abweichung am falschen Ende suchen - und schlimmer: man wuerde dem
Werkzeug glauben.

Diese Tests halten beide Wege gegeneinander: dieselben Komponenten,
dieselben Werte, dieselben Gewichte, dieselben Quellen, derselbe Score.
Die Paarbeitraege werden gegen genau die Funktionen geprueft, aus denen
die Counter- und Synergie-Komponente ihren Mittelwert bildet.
"""

import io
import json

from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from drafter.models import Brawler, BrawlerStat, Datenquelle
from drafter.services import counters, synergies
from drafter.services.providers.datenbank import gemessener_provider
from drafter.services.analyse import als_dict, paarbeitraege
from drafter.services.draft_engine import DraftEngine
from drafter.tests.basis import DrafterTest

LAGE = dict(karte="hard-rock-mine", eigene=["gale", "belle"],
            gegner=["bull", "tick", "gene"])


class GleicherRechenwegTest(DrafterTest):
    """Analyse und Empfehlung duerfen nie auseinanderlaufen."""

    def setUp(self):
        self.ctx = self.context(**LAGE)
        self.engine = DraftEngine(self.ctx)
        self.liste = self.engine.empfehlungen(anzahl=8)

    def test_spitzenkandidat_stimmt_in_jeder_komponente(self):
        beste = self.liste[0]
        empfehlung, rang, anzahl = DraftEngine(self.ctx).analyse(beste.brawler)

        self.assertEqual(rang, 1)
        self.assertGreater(anzahl, len(self.liste))
        self.assertEqual(empfehlung.anzeige_score, beste.anzeige_score)
        self.assertAlmostEqual(empfehlung.roher_score, beste.roher_score, places=9)
        self.assertAlmostEqual(empfehlung.confidence, beste.confidence, places=9)
        self.assertEqual(empfehlung.stufe, beste.stufe)

        self.assertEqual(set(empfehlung.komponenten), set(beste.komponenten))
        for key, komp in beste.komponenten.items():
            andere = empfehlung.komponenten[key]
            self.assertAlmostEqual(andere.wert, komp.wert, places=9, msg=key)
            self.assertAlmostEqual(andere.gewicht, komp.gewicht, places=9, msg=key)
            self.assertEqual(andere.quelle, komp.quelle, key)
            self.assertEqual(andere.verfuegbar, komp.verfuegbar, key)
            self.assertEqual(andere.anwendbar, komp.anwendbar, key)
            self.assertAlmostEqual(andere.beitrag, komp.beitrag, places=9, msg=key)

    def test_jeder_vorschlag_bekommt_dieselbe_zahl_und_seinen_rang(self):
        for erwarteter_rang, vorschlag in enumerate(self.liste, 1):
            empfehlung, rang, _ = DraftEngine(self.ctx).analyse(vorschlag.brawler)
            self.assertEqual(rang, erwarteter_rang, vorschlag.brawler.slug)
            self.assertEqual(empfehlung.anzeige_score, vorschlag.anzeige_score,
                             vorschlag.brawler.slug)

    def test_auch_wer_nicht_empfohlen_wird_bekommt_seinen_score(self):
        """Der eigentliche Zweck: ein Kandidat weit unten.

        `alle_scores` entsteht im normalen Lauf ueber ALLE Kandidaten -
        die Analyse muss genau diese Zahl liefern, nicht eine eigene.
        """
        vorne = {e.brawler.slug for e in self.liste}
        unten = [b for b in self.engine.raum.verfuegbare(self.ctx.gesperrte_ids)
                 if b.slug not in vorne and self.engine.raum.bewertbar(b)]
        self.assertTrue(unten, "Testlage ohne Kandidaten ausserhalb der Spitze")

        for brawler in unten:
            empfehlung, rang, anzahl = DraftEngine(self.ctx).analyse(brawler)
            self.assertIsNotNone(empfehlung, brawler.slug)
            self.assertEqual(empfehlung.anzeige_score,
                             self.engine.alle_scores[brawler.slug], brawler.slug)
            self.assertGreater(rang, len(self.liste), brawler.slug)
            self.assertLessEqual(rang, anzahl)

    def test_die_analyse_veraendert_die_empfehlungen_nicht(self):
        """Ein Messgeraet darf nicht Teil der Maschine werden."""
        vorher = [(e.brawler.slug, e.anzeige_score) for e in
                  DraftEngine(self.ctx).empfehlungen(anzahl=10)]
        for brawler in (self.brawler("mortis"), self.brawler("piper")):
            DraftEngine(self.ctx).analyse(brawler)
        nachher = [(e.brawler.slug, e.anzeige_score) for e in
                   DraftEngine(self.ctx).empfehlungen(anzahl=10)]
        self.assertEqual(vorher, nachher)

    def test_detail_bleibt_bei_derselben_antwort(self):
        """`detail()` ist jetzt ein Aufruf von `analyse()` - ohne Unterschied."""
        brawler = self.brawler("mortis")
        ueber_detail = DraftEngine(self.ctx).detail(brawler)
        ueber_analyse, _, _ = DraftEngine(self.ctx).analyse(brawler)
        self.assertEqual(ueber_detail.anzeige_score, ueber_analyse.anzeige_score)
        self.assertEqual(ueber_detail.als_dict(ausfuehrlich=True),
                         ueber_analyse.als_dict(ausfuehrlich=True))


class PaarbeitraegeTest(DrafterTest):
    """Die Einzelwerte stammen aus denselben Funktionen wie der Mittelwert."""

    def setUp(self):
        self.ctx = self.context(**LAGE)
        self.engine = DraftEngine(self.ctx)
        self.brawler_ = self.brawler("mortis")
        self.paare = paarbeitraege(self.brawler_, self.ctx, self.engine.raum)

    def test_jeder_gegner_und_jeder_mitspieler_steht_drin(self):
        self.assertEqual([z["slug"] for z in self.paare["counter"]],
                         [b.slug for b in self.ctx.enemy_picks])
        self.assertEqual([z["slug"] for z in self.paare["synergie"]],
                         [b.slug for b in self.ctx.own_picks])

    def test_counterwerte_sind_die_der_komponente(self):
        for zeile, gegner in zip(self.paare["counter"], self.ctx.enemy_picks):
            wert, _, quelle = counters.vorteil(self.brawler_, gegner, self.engine.raum)
            self.assertAlmostEqual(zeile["wert"], round(wert, 3), places=9, msg=gegner.slug)
            self.assertEqual(zeile["bekannt"], quelle is not None, gegner.slug)

    def test_synergiewerte_sind_die_der_komponente(self):
        for zeile, mitspieler in zip(self.paare["synergie"], self.ctx.own_picks):
            wert, _, quelle = synergies.paar(self.brawler_, mitspieler, self.engine.raum)
            self.assertAlmostEqual(zeile["wert"], round(wert, 3), places=9,
                                   msg=mitspieler.slug)
            self.assertEqual(zeile["bekannt"], quelle is not None, mitspieler.slug)

    def test_der_mittelwert_der_paare_ergibt_die_komponente(self):
        """Gegenprobe auf die Formel - nicht ihre Wiederholung.

        Die Counter-Komponente ist Mittel x 0,7 + schlechtester x 0,3 ueber
        die BEKANNTEN Paare. Stimmt das nicht mehr ueberein, zeigt die
        Tabelle etwas anderes als der Score.
        """
        komp = counters.komponente(self.brawler_, self.ctx, self.engine.raum)
        werte = [z["wert"] for z in self.paare["counter"] if z["bekannt"]]
        self.assertTrue(werte)
        erwartet = sum(werte) / len(werte) * 0.7 + min(werte) * 0.3
        self.assertAlmostEqual(komp.wert, erwartet, places=2)

    def test_unbekanntes_paar_fehlt_nicht_sondern_sagt_es(self):
        ohne = self.brawler("mortis")
        leer = paarbeitraege(ohne, self.context(karte="hard-rock-mine"),
                             self.engine.raum)
        self.assertEqual(leer["counter"], [])
        self.assertEqual(leer["synergie"], [])


class AntwortTest(DrafterTest):
    """Was die Oberflaeche bekommt."""

    def setUp(self):
        self.ctx = self.context(**LAGE)
        self.engine = DraftEngine(self.ctx)
        # `alle_scores` entsteht erst im Lauf - ohne ihn ist es leer.
        self.liste = self.engine.empfehlungen(anzahl=8)

    def test_antwort_traegt_rang_feldgroesse_und_paare(self):
        brawler = self.brawler("mortis")
        empfehlung, rang, anzahl = self.engine.analyse(brawler)
        daten = als_dict(empfehlung, rang, anzahl, self.ctx, self.engine.raum)

        self.assertEqual(daten["rang"], rang)
        self.assertEqual(daten["kandidaten"], anzahl)
        self.assertEqual(len(daten["matchups"]["counter"]), len(self.ctx.enemy_picks))
        self.assertEqual(len(daten["matchups"]["synergie"]), len(self.ctx.own_picks))
        # Der Kern bleibt die gewoehnliche Empfehlung.
        for schluessel in ("score", "komponenten", "erklaerung", "confidence",
                           "datenabdeckung", "current_strength_beitrag", "draft_fit"):
            self.assertIn(schluessel, daten)

    def test_api_liefert_dieselbe_zahl_wie_die_empfehlungsliste(self):
        lage = {"map": "hard-rock-mine", "own_picks": ["gale", "belle"],
                "enemy_picks": ["bull", "tick", "gene"]}
        liste = self.client.post(reverse("drafter:api_recommend"),
                                 data=json.dumps(lage),
                                 content_type="application/json").json()
        oben = liste["empfehlungen"][0]

        antwort = self.client.post(reverse("drafter:api_detail"),
                                   data=json.dumps({**lage, "brawler": oben["slug"]}),
                                   content_type="application/json")
        self.assertEqual(antwort.status_code, 200)
        daten = antwort.json()
        self.assertEqual(daten["score"], oben["score"])
        self.assertEqual(daten["rang"], 1)
        self.assertEqual(daten["komponenten"], oben["komponenten"])

    def test_api_bewertet_auch_wen_niemand_vorschlaegt(self):
        lage = {"map": "hard-rock-mine", "own_picks": ["gale", "belle"],
                "enemy_picks": ["bull", "tick", "gene"]}
        liste = self.client.post(reverse("drafter:api_recommend"),
                                 data=json.dumps(lage),
                                 content_type="application/json").json()
        vorne = {e["slug"] for e in liste["empfehlungen"]}
        unten = next(s for s in self.engine.alle_scores if s not in vorne
                     and s not in {"gale", "belle", "bull", "tick", "gene"})

        daten = self.client.post(reverse("drafter:api_detail"),
                                 data=json.dumps({**lage, "brawler": unten}),
                                 content_type="application/json").json()
        self.assertEqual(daten["score"], self.engine.alle_scores[unten])
        self.assertGreater(daten["rang"], len(liste["empfehlungen"]))


class KatalogeintragTest(DrafterTest):
    """Der eigentliche Debug-Fall: ein Brawler ohne gepflegtes Profil.

    Seit den Datenstufen (2026-09-18) bewertet die Engine auch
    Katalogeintraege, sobald Messwerte vorliegen - sie stehen im Gitter
    und bekommen einen Rang. Der Detailweg hat sie bis zum 2026-09-20
    trotzdem abgewiesen (`is_active=True`), womit sich ausgerechnet der
    Fall nicht aufklaeren liess, fuer den die Analyse gemacht ist.
    """

    def setUp(self):
        self.nori = Brawler.objects.create(
            name="NORI", slug="nori", external_id="16000099", is_active=False)
        BrawlerStat.objects.create(
            brawler=self.nori, games=120, wins=66, raw_rate=0.55,
            adjusted_rate=0.55, confidence=0.4, source=Datenquelle.API,
            window_label="90d")

    def test_engine_bewertet_ihn(self):
        engine = DraftEngine(self.context(karte="hard-rock-mine"),
                             provider=gemessener_provider())
        empfehlung, rang, _ = engine.analyse(self.nori)
        self.assertIsNotNone(empfehlung)
        self.assertEqual(empfehlung.stufe, "gemessen")
        self.assertIsNotNone(rang)

    def test_api_findet_ihn_statt_ihn_unbekannt_zu_nennen(self):
        antwort = self.client.post(
            reverse("drafter:api_detail"),
            data=json.dumps({"map": "hard-rock-mine", "brawler": "nori"}),
            content_type="application/json")
        self.assertNotIn("Unbekannter Brawler", antwort.content.decode())

    def test_kommando_findet_ihn_auch(self):
        ausgabe = io.StringIO()
        call_command("drafter_analyse", karte="hard-rock-mine", brawler="NORI",
                     stdout=ausgabe)
        self.assertIn("NORI", ausgabe.getvalue())


class KommandoTest(DrafterTest):
    def laufen(self, **o):
        ausgabe = io.StringIO()
        call_command("drafter_analyse", stdout=ausgabe, **o)
        return ausgabe.getvalue()

    def test_ausgabe_nennt_rang_score_und_beide_paartabellen(self):
        text = self.laufen(karte="hard-rock-mine", brawler="mortis",
                           eigene="gale,belle", gegner="bull,tick,gene")
        self.assertIn(self.brawler("mortis").name, text)
        self.assertIn("Rang:", text)
        self.assertIn("Counter je Gegner", text)
        self.assertIn("Synergie je Mitspieler", text)
        for slug in ("bull", "tick", "gene", "gale", "belle"):
            self.assertIn(self.brawler(slug).name, text)

    def test_zahlen_stimmen_mit_der_engine_ueberein(self):
        ctx = self.context(**LAGE)
        empfehlung, rang, anzahl = DraftEngine(ctx).analyse(self.brawler("mortis"))
        text = self.laufen(karte="hard-rock-mine", brawler="mortis",
                           eigene="gale,belle", gegner="bull,tick,gene")
        self.assertIn(f"Rang:              {rang} von {anzahl}", text)
        self.assertIn(f"Score:             {empfehlung.anzeige_score}/100", text)

    def test_json_ausgabe_ist_die_api_antwort(self):
        text = self.laufen(karte="hard-rock-mine", brawler="mortis",
                           eigene="gale,belle", gegner="bull,tick,gene", json=True)
        daten = json.loads(text)
        self.assertEqual(daten["slug"], "mortis")
        self.assertIn("matchups", daten)
        self.assertIn("komponenten", daten)

    def test_name_statt_slug_und_beliebige_schreibweise(self):
        """Getippt wird, was man sieht - in jeder Schreibweise."""
        name = self.brawler("mortis").name
        for eingabe in (name, name.upper(), name.lower(), "mortis"):
            self.assertIn(name, self.laufen(karte="hard-rock-mine", brawler=eingabe),
                          eingabe)

    def test_unbekannter_brawler_wird_gemeldet(self):
        with self.assertRaises(CommandError) as fehler:
            self.laufen(karte="hard-rock-mine", brawler="gibtsnicht")
        self.assertIn("brawler", str(fehler.exception))

    def test_unbekannte_map_wird_gemeldet(self):
        with self.assertRaises(CommandError) as fehler:
            self.laufen(karte="gibtsnicht", brawler="mortis")
        self.assertIn("Map", str(fehler.exception))

    def test_gepickter_brawler_wird_gemeldet_statt_bewertet(self):
        with self.assertRaises(CommandError) as fehler:
            self.laufen(karte="hard-rock-mine", brawler="gale", eigene="gale")
        self.assertIn("gepickt", str(fehler.exception))
