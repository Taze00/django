# -*- coding: utf-8 -*-
"""Unbekannt ist keine Luecke - der Teambedarf folgt der Wissensabdeckung.

Bis zum 2026-09-20 entstand aus einem eigenen Pick ohne Profil voller
Teambedarf: AMBER stand fuer "das Team hat kein Frontline", dabei war
nur unbekannt, ob sie welches hat. Seit `Teamanalyse.bekannt` wissen wir,
von wie vielen Picks wir etwas wissen - jetzt zaehlt es auch.

Die Rechnung, um die es geht:

    nutzen = Σ (abdeckung[k] · bedarf[k] · zuwachs[k]) / Σ bedarf[k]

Zaehler gesichert, Nenner nicht. Waeren beide gedaempft, kuerzte sich
die Abdeckung bei gleichmaessigem Unwissen weg.
"""

from drafter import attributes as attr
from drafter import config
from drafter.models import Brawler, Datenquelle
from drafter.services import team_coverage, team_need
from drafter.services.draft_engine import DraftEngine
from drafter.tests.basis import DrafterTest

ANFORDERUNG = {"frontline": 0.8, "healing": 0.8}


class AbdeckungsHelfer:
    """Zwei Arten von Picks - und der Unterschied ist der ganze Punkt.

    `beschrieben` hat ein gepflegtes Profil: was dort NICHT steht, gilt
    als bekannt-abwesend ("jemand hat ihn angesehen und es nicht
    genannt"). `unbeschrieben` ist der AMBER-Fall: nie beschrieben, sagt
    zu gar nichts etwas.
    """

    zaehler = 93000

    def beschrieben(self, **werte):
        AbdeckungsHelfer.zaehler += 1
        n = AbdeckungsHelfer.zaehler
        return Brawler.objects.create(
            name=f"B{n}", slug=f"b{n}", external_id=str(n), is_active=True,
            source=Datenquelle.MANUAL, attributes=werte or {"mobility": 50})

    def unbeschrieben(self):
        AbdeckungsHelfer.zaehler += 1
        n = AbdeckungsHelfer.zaehler
        return Brawler.objects.create(
            name=f"U{n}", slug=f"u{n}", external_id=str(n), is_active=True,
            source=Datenquelle.API, draft_rolle="control")


class AbdeckungTest(AbdeckungsHelfer, DrafterTest):
    """Die Zaehlung selbst."""

    def test_alle_bekannt_ergibt_eins(self):
        team = [self.beschrieben(frontline=80), self.beschrieben(frontline=20)]
        self.assertEqual(team_coverage.bekannt_anteil(team, "frontline"), (2, 2))
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        self.assertEqual(analyse.abdeckung["frontline"], 1.0)

    def test_haelfte_bekannt_ergibt_ein_halb(self):
        team = [self.beschrieben(frontline=80), self.unbeschrieben()]
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        self.assertEqual(analyse.abdeckung["frontline"], 0.5)

    def test_niemand_bekannt_ergibt_null(self):
        team = [self.unbeschrieben(), self.unbeschrieben()]
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        self.assertEqual(analyse.abdeckung["frontline"], 0.0)

    def test_beschrieben_aber_nicht_genannt_zaehlt_als_bekannt(self):
        """Der Unterschied, an dem vier Verhaltenstests haengen.

        Wer ein gepflegtes Profil hat, wurde angesehen. Was dort nicht
        steht, ist eine schwache Aussage ueber Abwesenheit - sonst
        wuerde jedes duenne Profil zum blinden Fleck, und eine echte
        Luecke (drei beschriebene Brawler, keiner mit Anti-Tank)
        verschwaende.
        """
        team = [self.beschrieben(healing=50), self.beschrieben(healing=60)]
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        self.assertEqual(analyse.abdeckung["frontline"], 1.0)
        self.assertGreater(analyse.bedarf_gesichert["frontline"], 0.5,
                           "eine echte Luecke bleibt sichtbar")

    def test_leeres_team_gilt_als_vollstaendig(self):
        """Es gibt nichts, was uns entgehen koennte."""
        analyse = team_coverage.Teamanalyse.bauen([], ANFORDERUNG)
        self.assertEqual(analyse.abdeckung["frontline"], 1.0)


class GesicherterBedarfTest(AbdeckungsHelfer, DrafterTest):
    """Was von einer Luecke uebrig bleibt, wenn man sie nur halb sieht."""

    def test_voll_bekannte_luecke_bleibt_voll(self):
        team = [self.beschrieben(frontline=0, healing=0),
                self.beschrieben(frontline=0, healing=0)]
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        self.assertEqual(analyse.abdeckung["frontline"], 1.0)
        self.assertAlmostEqual(analyse.bedarf_gesichert["frontline"],
                               analyse.bedarf["frontline"], places=9)
        self.assertGreater(analyse.bedarf_gesichert["frontline"], 0.5,
                           "eine belegte Luecke bleibt eine Luecke")

    def test_halb_bekannte_luecke_zaehlt_halb(self):
        team = [self.beschrieben(frontline=0), self.unbeschrieben()]
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        self.assertAlmostEqual(analyse.bedarf_gesichert["frontline"],
                               analyse.bedarf["frontline"] * 0.5, places=9)

    def test_unbekannte_luecke_verschwindet(self):
        """Der AMBER-Fall: niemand sagt etwas, also ist nichts belegt."""
        team = [self.unbeschrieben(), self.unbeschrieben()]
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        self.assertGreater(analyse.bedarf["frontline"], 0.0,
                           "roh sieht es weiter nach Luecke aus")
        self.assertEqual(analyse.bedarf_gesichert["frontline"], 0.0,
                         "belegt ist davon nichts")
        self.assertNotIn("frontline", [e.key for e, _ in analyse.groesste_luecken()])

    def test_echte_null_bleibt_eine_echte_luecke(self):
        """Ein gepflegtes 0 ist Wissen, keine Wissensluecke."""
        team = [self.beschrieben(frontline=0), self.beschrieben(frontline=0)]
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        self.assertEqual(analyse.abdeckung["frontline"], 1.0)
        self.assertGreater(analyse.bedarf_gesichert["frontline"], 0.5)

    def test_bekannte_staerke_bleibt_erhalten(self):
        team = [self.beschrieben(frontline=90), self.beschrieben(frontline=80)]
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        self.assertGreater(analyse.profil["frontline"], 0.85)
        self.assertLess(analyse.bedarf_gesichert["frontline"], 0.05,
                        "gedeckt ist gedeckt")


class NutzenTest(AbdeckungsHelfer, DrafterTest):
    """Die Wirkung auf den Teambedarf eines Kandidaten."""

    def nutzen(self, team, kandidat):
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        wert, _ = team_need._nutzen(analyse, kandidat)
        return wert

    def test_voll_bekanntes_team_unveraendert(self):
        """2/2 bekannt: die Formel ist identisch mit der alten."""
        team = [self.beschrieben(frontline=0, healing=0),
                self.beschrieben(frontline=0, healing=0)]
        analyse = team_coverage.Teamanalyse.bauen(team, ANFORDERUNG)
        kandidat = self.beschrieben(frontline=90, healing=90)
        zuwachs = analyse.zuwachs(kandidat)
        alt = sum(analyse.bedarf[k] * zuwachs.get(k, 0.0)
                  for k in attr.ATTRIBUT_KEYS) / sum(analyse.bedarf.values())
        neu, _ = team_need._nutzen(analyse, kandidat)
        self.assertAlmostEqual(neu, alt, places=9)

    def test_halbwissen_daempft(self):
        voll = [self.beschrieben(frontline=0, healing=0),
                self.beschrieben(frontline=0, healing=0)]
        halb = [self.beschrieben(frontline=0, healing=0), self.unbeschrieben()]
        kandidat = self.beschrieben(frontline=90, healing=10)
        self.assertLess(self.nutzen(halb, kandidat), self.nutzen(voll, kandidat),
                        "was wir nur halb sehen, zaehlt nur halb")

    def test_ohne_wissen_kein_phantombedarf(self):
        ohne = [self.unbeschrieben(), self.unbeschrieben()]
        kandidat = self.beschrieben(frontline=95)
        self.assertAlmostEqual(self.nutzen(ohne, kandidat), 0.0, places=9,
                               msg="Frontline ist unbekannt, nicht offen")

    def test_daempfung_kuerzt_sich_nicht_weg(self):
        """Der Grund fuer den ungedaempften Nenner.

        Waeren Zaehler UND Nenner gedaempft, haette ein Team ohne jedes
        Wissen denselben Bedarf wie ein vollstaendig bekanntes.
        """
        voll = [self.beschrieben(frontline=0, healing=0),
                self.beschrieben(frontline=0, healing=0)]
        keins = [self.unbeschrieben(), self.unbeschrieben()]
        kandidat = self.beschrieben(frontline=90, healing=90)
        self.assertGreater(self.nutzen(voll, kandidat), 0.5)
        self.assertAlmostEqual(self.nutzen(keins, kandidat), 0.0, places=9)


class StrafenTest(DrafterTest):
    """Was gedaempft wird - und was ausdruecklich nicht."""

    def test_angreifbarkeit_behauptet_nichts_unbelegtes(self):
        """Eine Restluecke, die niemand sehen kann, ist keine Gefahr."""
        ctx = self.context(karte="hard-rock-mine", eigene=["gale"],
                           gegner=["bull", "frank"])
        engine = DraftEngine(ctx)
        analyse = engine.eigene_analyse
        for key in ("anti_tank", "long_range"):
            komp = team_need.angreifbarkeit(self.brawler("pam"), analyse, ctx)
            self.assertLessEqual(komp.wert, 0.0, "Strafen sind nie positiv")

    def test_redundanz_wird_nicht_gedaempft(self):
        """"Wir haben schon genug" stuetzt sich nur auf Bekanntes.

        Das Teamprofil kann durch weitere bekannte Picks nur steigen -
        wer 0.9 gemessen hat, hat mindestens 0.9. Eine Daempfung wuerde
        eine belegte Aussage schwaechen statt eine unbelegte zu
        verhindern.
        """
        ctx = self.context(karte="hard-rock-mine", eigene=["gale"],
                           gegner=["bull", "tick"])
        engine = DraftEngine(ctx)
        komp = team_need.redundanz(self.brawler("sandy"), engine.eigene_analyse, ctx)
        self.assertLessEqual(komp.wert, 0.0)


class KeineSonderbehandlungTest(DrafterTest):
    """Es zaehlt die Information, nicht die Herkunft."""

    def test_zwei_gleich_bekannte_teams_ergeben_dasselbe(self):
        """Demo-Profil oder gepflegt: bei gleichem Wissen gleiches Ergebnis."""
        demo = Brawler.objects.create(
            name="DEMOISH", slug="demoish", external_id="93300", is_active=True,
            source=Datenquelle.DEMO, attributes={"frontline": 80, "healing": 80})
        manuell = Brawler.objects.create(
            name="MANUELL", slug="manuell", external_id="93301", is_active=True,
            source=Datenquelle.MANUAL, attributes={"frontline": 80, "healing": 80})
        a = team_coverage.Teamanalyse.bauen([demo], ANFORDERUNG)
        b = team_coverage.Teamanalyse.bauen([manuell], ANFORDERUNG)
        self.assertEqual(a.abdeckung["frontline"], b.abdeckung["frontline"])


class PamFallTest(DrafterTest):
    """Der Praxisfall bleibt reproduzierbar."""

    def test_lage_laeuft_durch_und_liefert_eine_rangfolge(self):
        ctx = self.context(karte="hard-rock-mine", eigene=["gale", "pam"],
                           gegner=["bull", "tick", "gene"])
        engine = DraftEngine(ctx)
        top = engine.empfehlungen(anzahl=10)
        self.assertTrue(top)
        analyse = engine.eigene_analyse
        self.assertTrue(analyse.abdeckung)
        for key, wert in analyse.abdeckung.items():
            self.assertGreaterEqual(wert, 0.0)
            self.assertLessEqual(wert, 1.0)
        for key, gesichert in analyse.bedarf_gesichert.items():
            self.assertLessEqual(gesichert, analyse.bedarf[key] + 1e-9,
                                 f"{key}: gesichert darf nie ueber roh liegen")
