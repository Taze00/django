# -*- coding: utf-8 -*-
"""Paarwerte: global ist die Basis, der Modus ein Update darauf.

Vor dem 2026-09-20 schrumpfte jede Ebene fuer sich gegen die nackte
log5-Erwartung, und die Engine nahm anschliessend immer die
spezifischste Zeile. Sechs Knockout-Partien verdraengten damit
dreiundzwanzig globale vollstaendig - im Praxisfall #7 bis zum
Vorzeichen (EDGAR+GRAY: global +0.003, Knockout -0.031).

Zwei Dinge werden hier geprueft, und das zweite ist das wichtigere:

1. Die Mischung ist stetig und geht in die richtige Richtung - wenig
   Modusdaten heisst fast global, viele heissen fast Modus.
2. **Keine Partie zaehlt zweimal.** Der Prior der Modus-Zeile ist die
   Differenzmenge global-minus-Modus, nicht die Globalzeile selbst.
   Waere es die Globalzeile, steckten die Modus-Partien darin schon
   einmal drin - und noch einmal in der Beobachtung.
"""

from drafter import config
from drafter.models import (
    Brawler, CounterStat, Datenquelle, GameMode, Patch, SynergyStat,
)
from drafter.models.matches import Match
from drafter.services.aggregation.aggregator import Aggregator
from drafter.services.aggregation.rechnung import (
    Zaehler, erwartet_gegeneinander, rest_zaehler, uebertragener_prior, vorteil,
)
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import BASIS, FixtureMixin, serie

K = config.PAAR_PRIOR_STAERKE


def zaehler(spiele, siege, gewicht=None):
    """Ein Zaehler mit Gewicht = Spielzahl (keine Zeit-/Patchabschlaege)."""
    gewicht = spiele if gewicht is None else gewicht
    anteil = (siege / spiele) if spiele else 0.0
    return Zaehler(games=spiele, wins=siege, gewicht=gewicht,
                   gewicht_siege=gewicht * anteil)


def schaetze(global_spiele, global_siege, modus_spiele, modus_siege,
             erwartet_global=0.5, erwartet_modus=None):
    """Die Modus-Schaetzung, wie der Aggregator sie rechnet."""
    erwartet_modus = erwartet_global if erwartet_modus is None else erwartet_modus
    z_global = zaehler(global_spiele, global_siege)
    z_modus = zaehler(modus_spiele, modus_siege)
    rest = rest_zaehler(z_global, z_modus)
    rest_rate = rest.geglaettet(erwartet_global, K)
    prior = uebertragener_prior(rest_rate, erwartet_global, erwartet_modus)
    return z_modus.geglaettet(prior, K), prior


class MischungTest(DrafterTest):
    """Wie stark traegt der Modus, wie stark der Rest?"""

    def test_zwei_modusspiele_bleiben_fast_beim_rest(self):
        # Rest: 198 Partien, 60 % gewonnen. Modus: 2 Partien, beide verloren.
        wert, prior = schaetze(200, 120, 2, 0)
        self.assertAlmostEqual(prior, 198 / (198 + K) * 0.6061 + K / (198 + K) * 0.5,
                               delta=0.01)
        # Die zwei Partien duerfen den Wert kaum bewegen.
        self.assertAlmostEqual(wert, prior, delta=0.02)
        self.assertGreater(wert, 0.55, "zwei Partien kippen 198 nicht")

    def test_zwanzig_modusspiele_mischen(self):
        wert, prior = schaetze(220, 120, 20, 4)   # Rest 200/116, Modus 20/4 = 20 %
        gewicht = 20 / (20 + K)
        erwartet = gewicht * 0.2 + (1 - gewicht) * prior
        self.assertAlmostEqual(wert, erwartet, places=6)
        self.assertLess(wert, prior, "schlechter Modus zieht nach unten")
        self.assertGreater(wert, 0.35, "aber nicht bis auf den Rohwert")

    def test_fuenfhundert_modusspiele_dominieren(self):
        # global 700/280 = Modus 500/150 (30 %) PLUS Rest 200/130 (65 %).
        # Siege und Partien muessen aufgehen - sonst prueft der Test eine
        # Lage, die es nicht geben kann.
        wert, prior = schaetze(700, 280, 500, 150)
        gewicht = 500 / (500 + K)
        self.assertGreater(gewicht, 0.89)
        self.assertAlmostEqual(wert, gewicht * 0.3 + (1 - gewicht) * prior, places=6)
        self.assertLess(wert, 0.35, "500 Partien setzen sich durch")

    def test_das_modusgewicht_ist_stetig_und_monoton(self):
        """Keine Schwelle - mehr Modusdaten heisst mehr Modusgewicht."""
        vorher = None
        for n in (0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000):
            # Rest bleibt (2000-n)/600, der Modus verliert immer.
            wert, prior = schaetze(2000, 600, n, 0)
            if vorher is not None:
                self.assertLessEqual(wert, vorher + 1e-9,
                                     f"n={n} muss naeher am Modus liegen als n-1")
            vorher = wert
        self.assertLess(vorher, 0.1, "1000 verlorene Partien sind kein 60-%-Paar")

    def test_gleiche_richtung_verstaerkt_sich_nicht_ueber_die_daten_hinaus(self):
        """Global und Modus einig: der Wert bleibt zwischen beiden Raten."""
        wert, _ = schaetze(200, 130, 40, 26)   # beide 65 %
        self.assertGreater(wert, 0.5)
        self.assertLessEqual(wert, 0.65 + 1e-9)

    def test_entgegengesetzte_richtung_landet_dazwischen(self):
        """Global +, Modus -: das Ergebnis liegt zwischen beiden."""
        wert, prior = schaetze(200, 130, 20, 4)   # Rest 70 %, Modus 20 %
        self.assertLess(wert, prior)
        self.assertGreater(wert, 0.2)
        self.assertLess(wert, 0.7)


class KeineDoppelzaehlungTest(DrafterTest):
    """Der Kern: dieselbe Partie darf nicht Prior UND Beobachtung sein."""

    def test_rest_ist_die_differenzmenge(self):
        rest = rest_zaehler(zaehler(100, 60), zaehler(30, 10))
        self.assertEqual((rest.games, rest.wins), (70, 50))
        self.assertAlmostEqual(rest.gewicht, 70.0)
        self.assertAlmostEqual(rest.gewicht_siege, 50.0)

    def test_modusdaten_stecken_nicht_im_prior(self):
        """Prior der Modus-Zeile haengt nur an Partien ausserhalb des Modus.

        Gegenprobe: zwei Lagen mit identischem Rest, aber verschiedenem
        Modusausgang muessen denselben Prior haben.
        """
        _, prior_a = schaetze(100, 60, 20, 20)   # Modus 20 Siege
        _, prior_b = schaetze(100, 40, 20, 0)    # Rest identisch (80/40), Modus 0 Siege
        self.assertAlmostEqual(prior_a, prior_b, places=9)

    def test_ohne_daten_ausserhalb_bleibt_die_nackte_erwartung(self):
        """Kam das Paar NUR in diesem Modus vor, gibt es nichts zu uebertragen."""
        _, prior = schaetze(30, 21, 30, 21)      # global == modus, Rest leer
        self.assertAlmostEqual(prior, 0.5, places=9)

    def test_der_rest_kann_nicht_negativ_werden(self):
        rest = rest_zaehler(zaehler(5, 2), zaehler(9, 7))
        self.assertEqual((rest.games, rest.wins), (0, 0))
        self.assertAlmostEqual(rest.gewicht, 0.0)

    def test_eine_partie_zaehlt_genau_einmal(self):
        """Gewichtsprobe: Beobachtung + Rest ergeben wieder das Ganze."""
        z_global, z_modus = zaehler(137, 71), zaehler(41, 25)
        rest = rest_zaehler(z_global, z_modus)
        self.assertEqual(rest.games + z_modus.games, z_global.games)
        self.assertEqual(rest.wins + z_modus.wins, z_global.wins)
        self.assertAlmostEqual(rest.gewicht + z_modus.gewicht, z_global.gewicht)


class UebertragungTest(DrafterTest):
    """Uebertragen wird die Abweichung, nicht die Rate."""

    def test_abweichung_wandert_die_rate_nicht(self):
        # Ausserhalb: 3 Punkte ueber einer Erwartung von 0.53.
        prior = uebertragener_prior(0.56, 0.53, 0.47)
        self.assertAlmostEqual(prior, 0.50, places=9)

    def test_keine_abweichung_heisst_erwartung_der_feinen_ebene(self):
        self.assertAlmostEqual(uebertragener_prior(0.53, 0.53, 0.41), 0.41, places=9)

    def test_prior_bleibt_im_gueltigen_bereich(self):
        self.assertLess(uebertragener_prior(0.99, 0.10, 0.95), 1.0)
        self.assertGreater(uebertragener_prior(0.01, 0.90, 0.05), 0.0)


class SymmetrieTest(DrafterTest):
    """Was die Aenderung NICHT anfassen darf."""

    def test_counter_gegenrichtung_bleibt_exakt_das_negativ(self):
        """vorteil(p, e) und vorteil(1-p, 1-e) sind gegengleich.

        Die Gegenrichtung wird nicht gespeichert, sondern abgeleitet -
        das gilt unabhaengig davon, welcher Prior die Schaetzung erzeugt
        hat. Geprueft wird die Rechenregel selbst.
        """
        for rate, erwartet in ((0.62, 0.50), (0.31, 0.47), (0.50, 0.55), (0.9, 0.1)):
            hin = vorteil(rate, erwartet)
            her = vorteil(1.0 - rate, 1.0 - erwartet)
            self.assertAlmostEqual(hin + her, 0.0, places=12, msg=f"{rate}/{erwartet}")

    def test_log5_erwartung_ist_gegengleich(self):
        for pa, pb in ((0.55, 0.48), (0.5, 0.5), (0.61, 0.39)):
            self.assertAlmostEqual(
                erwartet_gegeneinander(pa, pb) + erwartet_gegeneinander(pb, pa), 1.0,
                places=12)

    def test_synergie_ist_symmetrisch_im_paar(self):
        """A+B und B+A ergeben dieselbe Schaetzung - die Reihenfolge zaehlt nicht."""
        from drafter.services.aggregation.rechnung import erwartet_miteinander
        self.assertAlmostEqual(erwartet_miteinander(0.53, 0.47),
                               erwartet_miteinander(0.47, 0.53), places=12)
        wert_a, _ = schaetze(120, 70, 30, 12, erwartet_global=erwartet_miteinander(0.53, 0.47))
        wert_b, _ = schaetze(120, 70, 30, 12, erwartet_global=erwartet_miteinander(0.47, 0.53))
        self.assertAlmostEqual(wert_a, wert_b, places=12)


class AggregatorTest(FixtureMixin, DrafterTest):
    """Durch den echten Aggregator, nicht nur durch die Formel.

    Die Rechnung kann stimmen und trotzdem falsch verdrahtet sein -
    etwa wenn die Modus-Zeile vor der Globalzeile entsteht und deren
    Zaehler noch gar nicht kennt.
    """

    def setUp(self):
        super().setUp()
        Patch.objects.all().delete()

    def aggregiere(self):
        return Aggregator((Datenquelle.SYNTHETIC,), stichtag=BASIS.date(),
                          fenster=["90d"]).ausfuehren()

    def counter(self, a, b, **filter):
        filter.setdefault("window_label", "90d")
        filter.setdefault("rank_pool", "alle")
        if not any(k.startswith("game_mode") for k in filter):
            filter["game_mode__isnull"] = True
        ids = sorted((Brawler.objects.get(slug=a).id, Brawler.objects.get(slug=b).id))
        return CounterStat.objects.get(brawler_id=ids[0], enemy_id=ids[1],
                                       source=Datenquelle.SYNTHETIC, **filter)

    def synergie(self, a, b, **filter):
        filter.setdefault("window_label", "90d")
        filter.setdefault("rank_pool", "alle")
        if not any(k.startswith("game_mode") for k in filter):
            filter["game_mode__isnull"] = True
        ids = sorted((Brawler.objects.get(slug=a).id, Brawler.objects.get(slug=b).id))
        return SynergyStat.objects.get(brawler_a_id=ids[0], brawler_b_id=ids[1],
                                       source=Datenquelle.SYNTHETIC, **filter)

    def test_kleiner_modus_folgt_dem_rest_statt_ihn_zu_verdraengen(self):
        """Der Praxisfall in klein: viele Partien woanders, drei hier.

        GALE und BELLE stehen zusammen in 40 Gem-Grab-Partien mit 30
        Siegen - und in 3 Knockout-Partien ohne Sieg. Vor der Aenderung
        stand in der Knockout-Zeile eine eigene, fast nur vom Prior
        getragene Schaetzung; jetzt traegt mit, was in Gem Grab gemessen
        wurde.
        """
        self.importiere(*serie(40, 30, modus="Gem Grab", karte="Hard Rock Mine"))
        self.importiere(*serie(3, 0, modus="Knockout", karte="Belle's Rock",
                               minuten=900))
        self.aggregiere()

        knockout = GameMode.objects.get(slug="knockout")
        modus = self.synergie("gale", "belle", game_mode=knockout)
        global_ = self.synergie("gale", "belle")

        self.assertEqual((modus.games, modus.wins), (3, 0))
        self.assertEqual(global_.games, 43)
        # Trotz 0 von 3 darf die Modus-Zeile nicht ins Negative kippen:
        # 40 Partien ausserhalb sagen deutlich etwas anderes.
        self.assertGreater(modus.synergy, 0.0,
                           "drei Partien duerfen vierzig nicht ueberstimmen")
        self.assertLess(modus.synergy, global_.synergy,
                        "sie duerfen aber auch nicht folgenlos bleiben")

    def wert_mit_aussen(self, partien_aussen, siege_aussen, partien_modus=120,
                        siege_modus=30):
        """Synergie der Knockout-Zeile, wenn AUSSERHALB so gespielt wurde.

        Zweimal mit verschiedenen Aussendaten gerechnet zeigt direkt, wie
        stark der Rest die Modus-Zeile bewegt - ohne auswendig gelernte
        Zahlen und ohne Annahme darueber, wo die Erwartung liegt. (Die
        liegt naemlich nicht bei 50 %: sind beide Partner schwach, ist
        schon eine 25-%-Paarquote mehr als die additiven Log-Odds
        erwarten lassen.)
        """
        Match.objects.filter(source=Datenquelle.SYNTHETIC).delete()
        self.importiere(*serie(partien_modus, siege_modus, modus="Knockout",
                               karte="Belle's Rock"))
        if partien_aussen:
            self.importiere(*serie(partien_aussen, siege_aussen, modus="Gem Grab",
                                   karte="Hard Rock Mine", minuten=3000))
        self.aggregiere()
        return self.synergie("gale", "belle",
                             game_mode=GameMode.objects.get(slug="knockout")).synergy

    def schwankung(self, partien_modus, siege_modus):
        """Wie stark bewegt derselbe Aussen-Unterschied diese Modus-Zeile?

        Aussen einmal 45 von 60 gewonnen, einmal 15 von 60 - der Modus
        bleibt beide Male gleich. Der Abstand der beiden Ergebnisse ist
        die Empfindlichkeit der Modus-Zeile gegenueber dem Rest.
        """
        gewonnen = self.wert_mit_aussen(60, 45, partien_modus, siege_modus)
        verloren = self.wert_mit_aussen(60, 15, partien_modus, siege_modus)
        return gewonnen - verloren

    def test_kleine_modusstichprobe_haengt_staerker_am_rest_als_eine_grosse(self):
        """Der Kern der Aenderung, ohne auswendig gelernte Zahlen.

        Drei Modusspiele muessen sich von derselben Aussenlage deutlich
        staerker bewegen lassen als hundertzwanzig. Beide Male ist der
        Rest identisch; nur die eigene Stichprobe unterscheidet sich.
        """
        klein = self.schwankung(3, 0)
        gross = self.schwankung(120, 30)
        self.assertGreater(klein, 0.05, "drei Partien muessen dem Rest folgen")
        self.assertGreater(klein, 3 * gross,
                           f"klein={klein:.4f} muss deutlich empfindlicher sein "
                           f"als gross={gross:.4f}")
        self.assertLess(gross, 0.05, "120 Partien bleiben weitgehend bei sich")

    def test_ohne_partien_ausserhalb_bleibt_alles_wie_vorher(self):
        """Kommt ein Paar nur in einem Modus vor, gibt es nichts zu uebertragen.

        Beide Zeilen zaehlen dieselben Partien. Bitgleich sind sie
        trotzdem nicht: jede Ebene misst gegen ihre EIGENE Erwartung, und
        die Einzelraten je Modus schrumpfen anders als die globalen. Der
        Rest ist leer, der Prior also die reine Erwartung - genau das
        Verhalten von vor der Aenderung.
        """
        self.importiere(*serie(20, 5, modus="Knockout", karte="Belle's Rock"))
        self.aggregiere()

        knockout = GameMode.objects.get(slug="knockout")
        modus = self.synergie("gale", "belle", game_mode=knockout)
        global_ = self.synergie("gale", "belle")
        self.assertEqual((modus.games, modus.wins), (global_.games, global_.wins))
        self.assertAlmostEqual(modus.synergy, global_.synergy, delta=0.05)

    def test_counter_bleibt_eine_zeile_je_paar(self):
        """Die Hierarchie aendert nichts an der kanonischen Speicherung."""
        self.importiere(*serie(30, 18, modus="Knockout", karte="Belle's Rock"))
        self.aggregiere()
        gale = Brawler.objects.get(slug="gale")
        buster = Brawler.objects.get(slug="buster")
        hin = CounterStat.objects.filter(brawler=gale, enemy=buster,
                                         source=Datenquelle.SYNTHETIC).count()
        her = CounterStat.objects.filter(brawler=buster, enemy=gale,
                                         source=Datenquelle.SYNTHETIC).count()
        self.assertEqual(min(hin, her), 0, "nie beide Richtungen gespeichert")
        self.assertGreater(max(hin, her), 0)

    def test_synergie_ist_unabhaengig_von_der_paarreihenfolge(self):
        self.importiere(*serie(25, 15, modus="Knockout", karte="Belle's Rock"))
        self.aggregiere()
        self.assertEqual(self.synergie("gale", "belle").synergy,
                         self.synergie("belle", "gale").synergy)
