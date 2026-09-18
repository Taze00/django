# -*- coding: utf-8 -*-
"""CURRENT STRENGTH: der Schaetzer und was er nicht behaupten darf.

Geprueft werden Richtungen und Groessenordnungen, keine Raenge. Ein Platz
haengt von allen Kandidaten ab; wer darauf testet, dreht am Ende an
Gewichten, bis ein Lieblingsbeispiel wieder oben steht.

Die Faelle mit Namen (OLLIE, MELODIE, GALE, GUS, COLETTE) stammen aus der
Diagnose vom 2026-09-18: Brawler, die mit duenner Datenlage weit vorn
standen, weil fehlende Komponenten hochgerechnet wurden und eine duenne
Map-Zeile eine dicke globale verdraengte. Sie stehen hier nicht, damit
sie einen bestimmten Platz belegen, sondern damit die STRUKTUR ihrer
Bewertung stimmt.
"""

from drafter import config
from drafter.models import Brawler, BrawlerStat, Datenquelle
from drafter.models.stats import CounterStat
from drafter.services import staerke as S
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import gemessen_mit_prior_provider
from drafter.tests.basis import DrafterTest


class PosteriorTest(DrafterTest):
    """Beta-Binomial: kleine Stichprobe zum Prior, grosse zur Messung."""

    def test_kleine_stichprobe_bleibt_beim_prior(self):
        rate, _ = S.posterior(1, 1)
        self.assertAlmostEqual(rate, 0.5, delta=0.01,
                               msg="1 Sieg aus 1 Spiel ist keine 100-%-Aussage")

    def test_grosse_stichprobe_ueberstimmt_den_prior(self):
        rate, _ = S.posterior(2000, 1100)
        self.assertAlmostEqual(rate, 0.55, delta=0.01)

    def test_schaetzung_waechst_monoton_zur_messung(self):
        """Je mehr Partien, desto naeher an der rohen Rate - ohne Sprung."""
        abstaende = []
        for spiele in (1, 10, 50, 500, 2000):
            rate, _ = S.posterior(spiele, spiele * 0.55)
            abstaende.append(abs(rate - 0.55))
        self.assertEqual(abstaende, sorted(abstaende, reverse=True))

    def test_sicherheit_waechst_mit_der_stichprobe(self):
        werte = [S.Staerke(*S.posterior(n, n * 0.55), spiele=n).confidence
                 for n in (1, 10, 50, 500, 2000)]
        self.assertEqual(werte, sorted(werte))
        self.assertLess(werte[0], 0.05, "10 Partien sind keine Gewissheit")
        self.assertGreater(werte[-1], 0.5)

    def test_wilson_bestaetigt_die_groessenordnung(self):
        """Kontrollrechnung: der Posterior liegt im Wilson-Intervall."""
        for spiele, siege in ((10, 7), (50, 30), (500, 280), (2000, 1100)):
            rate, _ = S.posterior(spiele, siege)
            unten, oben = S.wilson(spiele, siege)
            self.assertTrue(unten <= rate <= oben, f"{siege}/{spiele}")


class Zeile:
    """Eine Statistikzeile, so viel wie der Schaetzer davon liest."""

    def __init__(self, spiele, siege, modus=None, karte=None, pick=0.0):
        self.games, self.wins = spiele, siege
        self.game_mode_id, self.brawl_map_id = modus, karte
        self.raw_rate = self.adjusted_rate = None
        self.is_demo = False
        self.pick_rate = pick


class HierarchieTest(DrafterTest):
    """Global, Modus und Map zaehlen zusammen - nicht gegeneinander."""

    def test_duenne_map_zeile_verdraengt_keine_dicke_globale(self):
        dick = {"global": Zeile(2000, 1000)}
        mit_duenn = {"global": Zeile(2000, 1000), "map": Zeile(4, 4, karte=1)}
        ohne = S.schaetze(dick, kontext_ebene=S.MAP)
        mit = S.schaetze(mit_duenn, kontext_ebene=S.MAP)
        self.assertLess(abs(mit.rate - ohne.rate), 0.03,
                        "4 Partien duerfen die Schaetzung nicht kippen")

    def test_mehr_daten_senken_die_sicherheit_nie(self):
        """Der Fehler der frueheren Kettenform: 4 Map-Partien machten unsicherer."""
        stufen = [
            {"global": Zeile(2000, 1000)},
            {"global": Zeile(2000, 1000), "modus": Zeile(400, 210, modus=1)},
            {"global": Zeile(2000, 1000), "modus": Zeile(400, 210, modus=1),
             "map": Zeile(120, 70, karte=1)},
        ]
        werte = [S.schaetze(z, kontext_ebene=S.MAP) for z in stufen]
        self.assertEqual([round(s.n_effektiv, 3) for s in werte],
                         sorted(round(s.n_effektiv, 3) for s in werte))
        self.assertEqual([round(s.confidence, 6) for s in werte],
                         sorted(round(s.confidence, 6) for s in werte))

    def test_partien_zaehlen_genau_einmal(self):
        """Die Ebenen sind verschachtelt - die globale Zeile enthaelt die Map-Partien."""
        s = S.schaetze(
            {"global": Zeile(100, 60), "map": Zeile(100, 60, karte=1)},
            kontext_ebene=S.MAP,
        )
        self.assertAlmostEqual(s.n_effektiv, 100, delta=0.01,
                               msg="dieselben 100 Partien, nicht 125")

    def test_jede_ebene_weist_ihren_beitrag_aus(self):
        s = S.schaetze(
            {"global": Zeile(1000, 550), "map": Zeile(200, 120, karte=1)},
            kontext_ebene=S.MAP,
        )
        ebenen = s.als_dict()["ebenen"]
        self.assertEqual(ebenen["map"]["gewicht"], 1.0)
        self.assertLess(ebenen["global"]["gewicht"], 1.0)
        self.assertAlmostEqual(ebenen["map"]["rate"], 0.6, places=3)
        self.assertAlmostEqual(ebenen["global"]["rate"], 0.55, places=3)
        self.assertAlmostEqual(
            s.n_effektiv,
            sum(e["effektive_spiele"] for e in ebenen.values()), delta=0.5)

    def test_ohne_messung_gilt_das_profil(self):
        s = S.schaetze({}, profil_rate=0.545)
        self.assertEqual(s.quelle, S.PROFILE)
        self.assertEqual(s.rate, 0.545)

    def test_ohne_alles_ist_nichts_bekannt(self):
        s = S.schaetze({})
        self.assertFalse(s.bekannt)
        self.assertIsNone(s.wert)
        self.assertEqual(s.confidence, 0.0)


class SelectionBiasTest(DrafterTest):
    """Selten gespielt senkt die Sicherheit, nicht den Wert."""

    def test_seltener_brawler_bekommt_keinen_abzug_auf_den_wert(self):
        haeufig = S.schaetze({"global": Zeile(200, 120)}, pickrate=0.10)
        selten = S.schaetze({"global": Zeile(200, 120)}, pickrate=0.004)
        self.assertEqual(haeufig.rate, selten.rate)
        self.assertLess(selten.confidence, haeufig.confidence)

    def test_grosse_stichprobe_entkraeftet_den_verdacht(self):
        """Wer selten gewaehlt wird, aber oft gemessen ist, ist kein Sonderfall."""
        duenn = S.schaetze({"global": Zeile(40, 26)}, pickrate=0.004)
        dick = S.schaetze({"global": Zeile(4000, 2600)}, pickrate=0.004)
        self.assertLess(dick.bias, duenn.bias)


class PaarSicherheitTest(DrafterTest):
    """Counter und Synergie: Sicherheit aus der Stichprobe DES PAARES."""

    def test_sicherheit_haengt_an_der_paarstichprobe(self):
        werte = [S.paar_confidence(n) for n in (0, 3, 30, 120, 400)]
        self.assertEqual(werte, sorted(werte))
        self.assertLess(werte[1], 0.1, "3 Partien sind keine Aussage")

    def messe_counter(self, kandidat, gegner, spiele, vorteil=0.2):
        CounterStat.objects.create(
            brawler=self.brawler(kandidat), enemy=self.brawler(gegner),
            games=spiele, sample_size=spiele, advantage=vorteil,
            confidence=0.9, source=Datenquelle.API, window_label="90d",
        )

    def test_drei_duenne_matchups_ergeben_keine_hohe_sicherheit(self):
        """Frueher: 0.45 + 0.2 x Zahl der Gegner - drei Gegner hiessen 1.0."""
        for gegner in ("bull", "tick", "poco"):
            self.messe_counter("gale", gegner, 3)
        engine = DraftEngine(self.context(gegner=["bull", "tick", "poco"],
                                          first_pick=False),
                             provider=gemessen_mit_prior_provider())
        komp = self.komponente(engine.empfehlungen(anzahl=200), "gale", config.K_COUNTER)
        self.assertTrue(komp.verfuegbar)
        self.assertLess(komp.confidence, 0.3,
                        "je drei Partien belegen kein Matchup")

    def test_dicke_matchups_ergeben_hoehere_sicherheit(self):
        for gegner in ("bull", "tick", "poco"):
            self.messe_counter("gale", gegner, 400)
        engine = DraftEngine(self.context(gegner=["bull", "tick", "poco"],
                                          first_pick=False),
                             provider=gemessen_mit_prior_provider())
        komp = self.komponente(engine.empfehlungen(anzahl=200), "gale", config.K_COUNTER)
        self.assertGreater(komp.confidence, 0.5)


class TrennungTest(DrafterTest):
    """WISSEN, DRAFT FIT und CURRENT STRENGTH bleiben getrennt."""

    def test_wissen_landet_nie_in_der_aktuellen_staerke(self):
        """Ein Brawler ohne jede Siegquote hat keine Staerke - auch mit Profil."""
        ohne_stat = Brawler.objects.create(
            name="NORI", slug="nori", external_id="16000099", is_active=True,
            source=Datenquelle.MANUAL,
        )
        for schluessel, wert in self.brawler("gale").attributes.items():
            ohne_stat.attributes[schluessel] = wert
        ohne_stat.save()
        raum = DraftEngine(self.context(),
                           provider=gemessen_mit_prior_provider()).raum
        self.assertTrue(ohne_stat.hat_profil, "Vorbedingung: Profil gepflegt")
        self.assertFalse(raum.staerke(ohne_stat).bekannt)

    def test_gruppen_stehen_einzeln_in_der_ausgabe(self):
        e = self.empfehlung(self.engine().empfehlungen(anzahl=200), "gale")
        daten = e.als_dict()
        self.assertIn("draft_fit", daten)
        self.assertIn("current_strength", daten)
        gruppen = {k["key"]: k["gruppe"] for k in daten["komponenten"]}
        self.assertEqual(gruppen[config.K_META], config.G_CURRENT_STRENGTH)
        self.assertEqual(gruppen[config.K_MAP_MODE], config.G_DRAFT_FIT)

    def test_summe_der_gruppen_ist_der_score(self):
        e = self.empfehlung(self.engine().empfehlungen(anzahl=200), "gale")
        summe = sum(e.gruppen_beitrag(g) for g in
                    (config.G_CURRENT_STRENGTH, config.G_DRAFT_FIT, config.G_PERSOENLICH))
        self.assertAlmostEqual(summe / 50, e.roher_score, places=6)


class DiagnosefaelleTest(DrafterTest):
    """Die fuenf Brawler aus der Diagnose - strukturell, nicht nach Platz."""

    FAELLE = ("ollie", "melodie", "gale", "gus", "colette")

    def vorhanden(self):
        return [s for s in self.FAELLE if Brawler.objects.filter(slug=s).exists()]

    def test_duenne_datenlage_erzeugt_keine_hohe_sicherheit(self):
        engine = DraftEngine(self.context(gegner=["bull"], first_pick=False),
                             provider=gemessen_mit_prior_provider())
        empfehlungen = engine.empfehlungen(anzahl=200)
        for slug in self.vorhanden():
            e = self.empfehlung(empfehlungen, slug)
            if e is None or e.datenabdeckung >= 0.5:
                continue
            self.assertLess(e.confidence, 0.5,
                            f"{slug}: halbe Datenlage, aber hohe Sicherheit")

    def test_score_ist_nie_mehr_als_die_summe_seiner_teile(self):
        engine = DraftEngine(self.context(eigene=["gale"], gegner=["bull", "tick"]),
                             provider=gemessen_mit_prior_provider())
        for e in engine.empfehlungen(anzahl=200):
            self.assertAlmostEqual(
                e.roher_score, sum(k.beitrag for k in e.komponenten.values()),
                places=9, msg=e.brawler.slug)

    def test_eine_einzige_bekannte_komponente_traegt_nur_ihr_gewicht(self):
        """Der OLLIE-Fall: viel unbekannt, eine positive Messung."""
        nori = Brawler.objects.create(name="NORI", slug="nori",
                                      external_id="16000099", is_active=False)
        BrawlerStat.objects.create(
            brawler=nori, games=30, sample_size=30, wins=18,
            raw_rate=0.6, adjusted_rate=0.6, confidence=0.15,
            source=Datenquelle.API, window_label="90d",
        )
        engine = DraftEngine(self.context(), provider=gemessen_mit_prior_provider())
        e = self.empfehlung(engine.empfehlungen(anzahl=200), "nori")
        self.assertIsNotNone(e)
        bekannt = [k for k in e.komponenten.values() if k.verfuegbar and k.gewicht > 0]
        self.assertLessEqual(
            e.roher_score, sum(k.beitrag for k in bekannt) + 1e-9)
        self.assertLess(e.datenabdeckung, 0.5)
