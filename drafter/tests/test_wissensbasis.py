# -*- coding: utf-8 -*-
"""Die Wissensbasis: unbekannt ist nicht null, und Demo ist nicht Messung.

Zwei Fehler steckten bis zum 2026-09-20 in der Grundlage:

1. **Ein nicht eingetragenes Attribut galt als 0.** PAM hat 14 von 32
   Eigenschaften gepflegt und galt in den uebrigen 18 als nachweislich
   unfaehig; AMBER ohne Profil in allen 32. Aus Unwissen wurde damit
   eine Behauptung - und aus der Behauptung eine Teamluecke, die ein
   Brawler mit gepflegtem Profil dann "schloss".
2. **Zwanzig von 106 Brawlern hatten ueberhaupt Zahlen.** Wer sie hatte,
   war strukturell im Vorteil, unabhaengig davon, ob die Zahlen
   stimmten. Sie stammen aus einer Sitzung vom 2026-09-14: 263 Werte,
   21 verschiedene Zahlen, 92 % Vielfache von fuenf.

Geloescht wurde nichts - alte Faelle bleiben reproduzierbar.
"""

from drafter import attributes as attr
from drafter.models import Brawler, Datenquelle
from drafter.services import draft_position, mechanik, team_coverage, vertrauen
from drafter.services.draft_engine import DraftEngine
from drafter.tests.basis import DrafterTest


class UnbekanntTest(DrafterTest):
    """Der Unterschied zwischen "weiss nicht" und "kann nicht"."""

    def test_nicht_eingetragen_ist_none(self):
        pam = self.brawler("pam")
        self.assertFalse(pam.bekannt("anti_tank"))
        self.assertIsNone(pam.wert("anti_tank"))

    def test_echte_null_bleibt_echte_null(self):
        """Ein ausdrueckliches 0 ist eine Aussage und bleibt eine."""
        b = Brawler.objects.create(
            name="NULLER", slug="nuller", external_id="94001", is_active=True,
            source=Datenquelle.MANUAL, attributes={"healing": 0, "mobility": 40})
        self.assertTrue(b.bekannt("healing"))
        self.assertEqual(b.wert("healing"), 0.0)
        self.assertIsNone(b.wert("frontline"), "nicht genannt bleibt unbekannt")

    def test_wert_oder_verlangt_eine_ausdrueckliche_entscheidung(self):
        pam = self.brawler("pam")
        self.assertEqual(pam.wert_oder("anti_tank"), 0.0)
        self.assertEqual(pam.wert_oder("anti_tank", 0.5), 0.5)

    def test_bekannte_werte_enthalten_nur_gepflegtes(self):
        pam = self.brawler("pam")
        bekannt = pam.bekannte_werte()
        self.assertIn("healing", bekannt)
        self.assertNotIn("anti_tank", bekannt)
        self.assertLess(len(bekannt), len(attr.ATTRIBUT_KEYS))

    def test_keine_komponente_stuerzt_ueber_unbekannt(self):
        """Der ganze Lauf mit einem Brawler ohne jede Eigenschaft."""
        Brawler.objects.create(
            name="LEERLING", slug="leerling", external_id="94002", is_active=True,
            source=Datenquelle.MANUAL, draft_rolle="tank")
        for ctx in (self.context(karte="hard-rock-mine"),
                    self.context(karte="hard-rock-mine", eigene=["gale"],
                                 gegner=["bull", "tick"])):
            empfehlungen = DraftEngine(ctx).empfehlungen(anzahl=300)
            self.assertTrue(empfehlungen)
            for e in empfehlungen:
                self.assertIsNotNone(e.anzeige_score)


class TeamprofilTest(DrafterTest):
    """Ein eigener Pick ohne altes Profil zaehlt trotzdem mit."""

    def setUp(self):
        self.ohne_profil = Brawler.objects.create(
            name="AMBERLING", slug="amberling", external_id="94010", is_active=True,
            source=Datenquelle.API, draft_rolle="control",
            draft_faehigkeiten=["wallbreak"])

    def test_mechanik_eines_picks_erreicht_das_teamprofil(self):
        """Der AMBER-Fall: Rolle und Faehigkeit, aber kein altes Profil."""
        profil = team_coverage.teamprofil([self.ohne_profil])
        self.assertGreater(profil["wallbreak"], 0.0,
                           "die gepflegte Faehigkeit muss ankommen")

    def test_bekannt_anteil_zeigt_die_luecke(self):
        team = [self.brawler("gale"), self.ohne_profil]
        bekannt, gesamt = team_coverage.bekannt_anteil(team, "mobility")
        self.assertEqual(gesamt, 2)
        self.assertEqual(bekannt, 1, "nur GALE sagt etwas zu mobility")

        bekannt, gesamt = team_coverage.bekannt_anteil(team, "wallbreak")
        self.assertEqual(bekannt, 2, "beide sagen etwas zu wallbreak")

    def test_niemand_weiss_etwas_ist_nicht_niemand_kann_etwas(self):
        team = [self.ohne_profil]
        profil = team_coverage.teamprofil(team)
        bekannt, gesamt = team_coverage.bekannt_anteil(team, "zone_control")
        self.assertEqual(profil["zone_control"], 0.0)
        self.assertEqual((bekannt, gesamt), (0, 1),
                         "die 0 im Profil muss als 'unbekannt' lesbar sein")

    def test_analyse_fuehrt_den_bekannt_anteil_mit(self):
        analyse = team_coverage.Teamanalyse.bauen(
            [self.brawler("gale"), self.ohne_profil], {"mobility": 0.5})
        self.assertIn("mobility", analyse.bekannt)
        self.assertEqual(analyse.bekannt["mobility"][1], 2)


class VertrauenTest(DrafterTest):
    """Eine belastbarere Quelle schlaegt die Demo-Schaetzung."""

    def test_demo_wird_auf_baender_zurueckgefuehrt(self):
        pam = self.brawler("pam")
        self.assertEqual(pam.source, Datenquelle.DEMO)
        # survivability steht in der Demo auf 75 - ein Wert, den es im
        # Band gar nicht gibt. Genau das ist der Punkt: die Quelle hat
        # drei Stufen, nicht hundert.
        roh = pam.wert("survivability")
        self.assertEqual(roh, 0.75)
        wert, stufe = vertrauen.wert_mit_stufe(pam, "survivability")
        self.assertEqual(stufe, vertrauen.DEMO)
        self.assertIn(wert, [b[1] for b in vertrauen.BAENDER])
        self.assertNotEqual(wert, roh, "die falsche Genauigkeit faellt weg")

    def test_reihenfolge_der_baender_bleibt_erhalten(self):
        """Gebaendert heisst nicht gleichgemacht - hoch bleibt ueber niedrig."""
        self.assertLess(vertrauen.band(0.35), vertrauen.band(0.60))
        self.assertLess(vertrauen.band(0.60), vertrauen.band(0.90))

    def test_mechanik_schlaegt_demo(self):
        pam = self.brawler("pam")
        wert, stufe = vertrauen.wert_mit_stufe(pam, "healing")
        self.assertEqual(stufe, vertrauen.MECHANIK,
                         "dass PAM heilt, ist eine Tatsache - nicht die 90")

    def test_unbekannt_ist_eine_eigene_stufe(self):
        pam = self.brawler("pam")
        wert, stufe = vertrauen.wert_mit_stufe(pam, "anti_tank")
        self.assertIsNone(wert)
        self.assertEqual(stufe, vertrauen.UNBEKANNT)

    def test_echte_null_wird_nicht_angehoben(self):
        self.assertEqual(vertrauen.band(0.0), 0.0)
        self.assertIsNone(vertrauen.band(None))

    def test_rangfolge_ist_vollstaendig(self):
        self.assertEqual(vertrauen.RANGFOLGE[0], vertrauen.MECHANIK)
        self.assertEqual(vertrauen.RANGFOLGE[-1], vertrauen.UNBEKANNT)
        self.assertEqual(set(vertrauen.LABEL), set(vertrauen.RANGFOLGE))


class MechanikTest(DrafterTest):
    """Aus der Fachquelle wird nur abgeleitet, was definitorisch dasteht."""

    def anlegen(self, **felder):
        felder.setdefault("external_id", "94020")
        return Brawler.objects.create(
            name="MECHA", slug="mecha", is_active=True,
            source=Datenquelle.API, **felder)

    def test_wallbreak_folgt_aus_der_faehigkeit(self):
        b = self.anlegen(draft_faehigkeiten=["wallbreak"])
        self.assertIs(mechanik.mechaniken(b)["has_wallbreak"], True)

    def test_sniper_rolle_setzt_die_reichweitenklasse(self):
        b = self.anlegen(draft_rolle="sniper")
        self.assertEqual(mechanik.mechaniken(b)["range_category"], "sniper")

    def test_knockback_stun_bleibt_unscharf(self):
        """Die Quelle nennt beide in einem Eintrag - welches, sagt sie nicht."""
        b = self.anlegen(draft_faehigkeiten=["knockback_stun"])
        mech = mechanik.mechaniken(b)
        self.assertNotIn("has_knockback", mech)
        self.assertNotIn("has_stun", mech)
        self.assertIs(mech["hat_knockback_oder_stun"], True)

    def test_was_die_quelle_nicht_sagt_bleibt_unbekannt(self):
        b = self.anlegen(draft_rolle="control")
        mech = mechanik.mechaniken(b)
        for key in ("has_healing", "has_shield", "mobility_category"):
            self.assertNotIn(key, mech)
        self.assertIn("has_healing", mechanik.luecken(b))

    def test_nicht_gelistet_heisst_nicht_abwesend(self):
        """Eine Liste ist kein Verzeichnis - wer fehlt, ist unbekannt."""
        b = self.anlegen(draft_rolle="tank", draft_faehigkeiten=[])
        self.assertNotIn("has_wallbreak", mechanik.mechaniken(b))

    def test_altes_profil_liefert_nur_ja_nein(self):
        pam = self.brawler("pam")
        self.assertIs(mechanik.mechaniken(pam)["has_healing"], True)
        self.assertEqual(mechanik.attributwert(pam, "healing"), mechanik.VORHANDEN)

    def test_handgepflegte_mechanik_hat_vorrang(self):
        b = self.anlegen(draft_faehigkeiten=["wallbreak"],
                         mechanik={"has_wallbreak": False})
        self.assertIs(mechanik.mechaniken(b)["has_wallbreak"], False)


class DraftwerteTest(DrafterTest):
    """Die sechs Handwerte sind aus dem Scoring raus - und bleiben lesbar."""

    def test_demo_draftwerte_speisen_das_scoring_nicht(self):
        pam = self.brawler("pam")
        self.assertIsNotNone(pam.draftwert("flexibility_value"),
                             "historisch weiter lesbar")
        self.assertIsNone(draft_position.gepflegter_draftwert(pam, "flexibility_value"),
                          "aber nicht mehr im Scoring")

    def test_belastbare_quelle_zaehlt_weiter(self):
        pam = self.brawler("pam")
        pam.source = Datenquelle.MANUAL
        pam.save(update_fields=["source"])
        self.assertIsNotNone(
            draft_position.gepflegter_draftwert(pam, "flexibility_value"))

    def test_fehlender_wert_bleibt_none(self):
        b = Brawler.objects.create(
            name="OHNEDRAFT", slug="ohnedraft", external_id="94030",
            is_active=True, source=Datenquelle.MANUAL)
        self.assertIsNone(b.draftwert("flexibility_value"))

    def test_komponente_liefert_immer_eine_komponente(self):
        """Nicht verfuegbar heisst `verfuegbar=False`, nicht None."""
        pam = self.brawler("pam")
        komp = draft_position.komponente(pam, self.context(first_pick=True))
        self.assertIsNotNone(komp)
        self.assertFalse(komp.verfuegbar)


class HistorieTest(DrafterTest):
    """Nichts wurde geloescht."""

    def test_alte_werte_stehen_unveraendert_in_der_datenbank(self):
        pam = self.brawler("pam")
        self.assertEqual(pam.attributes.get("healing"), 90)
        self.assertEqual(pam.draft_values.get("flexibility_value"), 65)
        self.assertEqual(len(pam.attributes), 14)
