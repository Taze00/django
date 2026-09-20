# -*- coding: utf-8 -*-
"""Die Skala der Counter-Komponente: feldrelativ plus absolut.

Bis zum 2026-09-20 ging der Rohwert der Counter-Komponente - eine
absolute Paar-Abweichung - unveraendert in den Score, waehrend
Teambedarf und Map-Fit feldrelativ standardisiert waren. Gemessen ueber
30 Last-Pick-Lagen lag das Counter-Feld fast vollstaendig zwischen -0.05
und +0.04; bei Gewicht 0.29 zog der 90.-Perzentil-Kandidat daraus 0.5
von 14.5 moeglichen Punkten. Nicht das Gewicht war falsch, sondern die
Einheit.

Geprueft wird hier ausschliesslich die **Skala**. Was ein Paarwert ist,
wie er aus Messung und Prior entsteht und wie sicher er ist, steht in
test_counter_messung.py und test_paar_hierarchie.py - daran aendert
diese Rechnung nichts, und mehrere Tests halten genau das fest.
"""

from drafter import config
from drafter.models import Brawler, BrawlerStat, CounterStat, Datenquelle
from drafter.services import counters
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import gemessen_mit_prior_provider
from drafter.services.scoring import robuste_z_werte
from drafter.tests.basis import DrafterTest


class RobusteNormalisierungTest(DrafterTest):
    """Die Feldrechnung fuer sich - ohne Draft, ohne Datenbank."""

    def test_identische_werte_ergeben_ueberall_null(self):
        werte = {i: 0.2 for i in range(20)}
        self.assertEqual(set(robuste_z_werte(werte, config.COUNTER_SPUERBAR).values()),
                         {0.0})

    def test_bedeutungslose_unterschiede_bleiben_bedeutungslos(self):
        """Ein Feld aus Rauschen darf keine Hardcounter erzeugen.

        Ohne Untergrenze im Nenner schrumpft der MAD mit dem Rauschen
        mit - aus Abstaenden von Tausendsteln wuerden Vollausschlaege.
        """
        werte = {i: 0.001 * i for i in range(21)}        # Spanne 0.02
        z = robuste_z_werte(werte, config.COUNTER_SPUERBAR)
        self.assertLess(max(abs(v) for v in z.values()), 0.25)

    def test_ein_ausreisser_verschiebt_die_mitte_nicht(self):
        """Genau der Grund fuer Median und MAD statt Mittelwert und sd."""
        ohne = {i: 0.0 for i in range(20)}
        mit = dict(ohne, extrem=5.0)
        z = robuste_z_werte(mit, config.COUNTER_SPUERBAR)
        self.assertEqual(z[0], 0.0, "der Ausreisser hat die Mitte mitgezogen")
        self.assertEqual(z["extrem"], 1.0)

    def test_deutliche_streuung_schoepft_die_skala_aus(self):
        """Bei echter Streuung rechnet der MAD, nicht die Untergrenze.

        Vollausschlag heisst zwei robuste Streuungen vom Median - nicht
        "der Rand des Feldes". Bei einem gleichverteilten Feld von -0.4
        bis +0.4 ist der MAD 0.356, zwei davon sind 0.71: die Raender
        liegen darunter und bekommen deshalb bewusst nicht die volle 1.0.
        """
        werte = {i: -0.4 + 0.08 * i for i in range(11)}   # -0.4 .. +0.4
        z = robuste_z_werte(werte, config.COUNTER_SPUERBAR)
        self.assertAlmostEqual(z[5], 0.0, places=6)
        self.assertLess(z[0], -0.5)
        self.assertGreater(z[10], 0.5)
        self.assertEqual(z[0], -z[10])
        # Wirklich der MAD und nicht die Untergrenze: diese waere viel
        # empfindlicher und haette beide Raender an den Anschlag gelegt.
        eng = robuste_z_werte(werte, 0.0)
        self.assertEqual(eng[0], z[0], "die Untergrenze hat mitgerechnet")


class SkalaBasis(DrafterTest):
    """Gemeinsamer Aufbau: ein gemessenes Feld und setzbare Matchups."""

    KARTE = "hard-rock-mine"
    GEGNER = ["bull", "tick", "poco"]

    def setUp(self):
        # Ein gemessenes Feld, damit "vorn" und "hinten" ueberhaupt
        # bestimmbar sind - sonst gibt es keine Lage im Feld.
        for i, b in enumerate(Brawler.objects.filter(is_active=True)[:20]):
            rate = 0.48 + 0.002 * i
            BrawlerStat.objects.create(
                brawler=b, games=300, sample_size=300, wins=round(300 * rate),
                raw_rate=rate, adjusted_rate=rate, confidence=0.5,
                source=Datenquelle.API, window_label="90d",
            )

    # --- Bausteine ------------------------------------------------------
    def counter(self, slug, gegner_slug, vorteil, spiele=800, confidence=0.8):
        """Gemessenes Matchup in kanonischer Richtung (kleinere ID zuerst)."""
        kandidat, gegner = self.brawler(slug), self.brawler(gegner_slug)
        a, b = ((kandidat, gegner) if kandidat.id < gegner.id else (gegner, kandidat))
        wert = vorteil if a.id == kandidat.id else -vorteil
        CounterStat.objects.update_or_create(
            brawler=a, enemy=b, window_label="90d", source=Datenquelle.API,
            defaults=dict(games=spiele, sample_size=spiele, advantage=wert,
                          confidence=confidence),
        )

    def lauf(self, eigene=("gale",), gegner=None, karte=None):
        ctx = self.context(karte=karte or self.KARTE, eigene=eigene,
                           gegner=self.GEGNER if gegner is None else gegner)
        engine = DraftEngine(ctx, provider=gemessen_mit_prior_provider())
        return engine.empfehlungen(anzahl=10_000, mit_details=0)

    def komp(self, liste, slug):
        return self.komponente(liste, slug, config.K_COUNTER)


class CounterSkalaTest(SkalaBasis):
    """Die Komponente im echten Lauf, mit gesetzten Matchups."""

    # --- Die Formel -----------------------------------------------------
    def test_wert_ist_feldanteil_plus_absoluter_anteil(self):
        """Die Formel steht nicht nur im Kommentar - sie wird nachgerechnet."""
        liste = self.lauf()
        roh = {e.brawler.id: e.komponenten[config.K_COUNTER].rohwert
               for e in liste
               if e.komponenten[config.K_COUNTER].rohwert is not None}
        self.assertTrue(roh, "kein Kandidat mit Counter-Rohwert")
        feld = robuste_z_werte(roh, config.COUNTER_SPUERBAR)
        for e in liste:
            k = e.komponenten[config.K_COUNTER]
            if k.rohwert is None:
                continue
            erwartet = (config.COUNTER_ANTEIL_FELD * feld[e.brawler.id]
                        + config.COUNTER_ANTEIL_ABSOLUT * k.rohwert)
            self.assertAlmostEqual(k.wert, max(-1.0, min(1.0, erwartet)), places=9,
                                   msg=e.brawler.slug)

    def test_der_absolute_anteil_bleibt_erhalten(self):
        """Ein reiner z-Wert waere falsch - der Betrag muss mitzaehlen.

        Zwei Kandidaten an derselben Stelle des Feldes, aber mit
        verschiedenem Rohwert, duerfen nicht denselben Wert bekommen.
        """
        liste = self.lauf()
        paare = [(e.komponenten[config.K_COUNTER].rohwert,
                  e.komponenten[config.K_COUNTER].wert) for e in liste
                 if e.komponenten[config.K_COUNTER].rohwert is not None]
        # Zwei Kandidaten am oberen Anschlag des Feldanteils: dort ist der
        # Feldanteil fuer beide 1.0, unterscheiden kann sie nur der Betrag.
        oben = sorted(paare, key=lambda p: -p[0])[:2]
        if oben[0][0] > oben[1][0] + 1e-9:
            self.assertGreater(oben[0][1], oben[1][1],
                               "gleicher Wert trotz groesserem Rohvorteil")

    # --- Richtung -------------------------------------------------------
    def test_klar_bester_counter_bekommt_positiven_feldanteil(self):
        for gegner in self.GEGNER:
            self.counter("brock", gegner, 0.45)
        liste = self.lauf()
        k = self.komp(liste, "brock")
        roh = {e.brawler.id: e.komponenten[config.K_COUNTER].rohwert for e in liste
               if e.komponenten[config.K_COUNTER].rohwert is not None}
        self.assertGreater(robuste_z_werte(roh, config.COUNTER_SPUERBAR)[
            self.brawler("brock").id], 0.5)
        self.assertGreater(k.wert, k.rohwert,
                           "der Feldanteil hebt den klaren Counter nicht")

    def test_klar_schlechtester_counter_bekommt_negativen_feldanteil(self):
        for gegner in self.GEGNER:
            self.counter("brock", gegner, -0.45)
        liste = self.lauf()
        k = self.komp(liste, "brock")
        roh = {e.brawler.id: e.komponenten[config.K_COUNTER].rohwert for e in liste
               if e.komponenten[config.K_COUNTER].rohwert is not None}
        self.assertLess(robuste_z_werte(roh, config.COUNTER_SPUERBAR)[
            self.brawler("brock").id], -0.5)
        self.assertLess(k.wert, k.rohwert)

    def test_die_skalierung_erreicht_eine_spuerbare_punktzahl(self):
        """Der eigentliche Zweck: Counter darf sein Gewicht auch ausspielen.

        Vorher zog der beste Counter des Feldes rund 3 von 14.5 moeglichen
        Punkten - ein Bruchteil dessen, was Gewicht 0.29 verspricht.
        """
        for gegner in self.GEGNER:
            self.counter("brock", gegner, 0.45)
        liste = self.lauf(eigene=("gale", "sandy"))       # Last Pick
        e = self.empfehlung(liste, "brock")
        k = e.komponenten[config.K_COUNTER]
        self.assertEqual(k.gewicht, config.PHASEN_GEWICHTE[config.PHASE_LAST][
            config.K_COUNTER])
        self.assertGreater(k.beitrag * 50, 6.0)

    # --- Sonderfaelle des Pools -----------------------------------------
    def test_ohne_gegner_bleibt_die_komponente_neutral(self):
        liste = self.lauf(gegner=())
        for e in liste:
            k = e.komponenten[config.K_COUNTER]
            self.assertFalse(k.anwendbar)
            self.assertEqual(k.wert, 0.0)
            self.assertIsNone(k.rohwert, "ohne Gegner wird nichts skaliert")

    def test_ohne_paardaten_bleibt_die_komponente_unbekannt(self):
        """Nicht berechenbar bleibt nicht berechenbar - nicht 0, nicht skaliert."""
        gegner = self.brawler("bull")
        ohne = Brawler.objects.create(
            name="OHNEPAAR", slug="ohnepaar", external_id="99123",
            is_active=True, source=Datenquelle.MANUAL, draft_rolle="tank",
        )
        BrawlerStat.objects.create(
            brawler=ohne, games=200, sample_size=200, wins=100, raw_rate=0.5,
            adjusted_rate=0.5, confidence=0.4, source=Datenquelle.API,
            window_label="90d",
        )
        liste = self.lauf(gegner=[gegner.slug])
        e = self.empfehlung(liste, "ohnepaar")
        if e is not None:
            k = e.komponenten[config.K_COUNTER]
            self.assertFalse(k.verfuegbar)
            self.assertIsNone(k.rohwert)
            self.assertEqual(k.beitrag, 0.0)

    def test_ein_einziger_kandidat_bekommt_keinen_feldanteil(self):
        """Ohne Feld gibt es keine Position im Feld - nur den Betrag."""
        b = self.brawler("brock")
        komp = counters.komponente(b, self.context(
            karte=self.KARTE, gegner=self.GEGNER), self._raum())
        einzeln = counters.komponenten_fuer_pool(
            [b], self.context(karte=self.KARTE, gegner=self.GEGNER), self._raum())[b.id]
        self.assertAlmostEqual(
            einzeln.wert, config.COUNTER_ANTEIL_ABSOLUT * komp.wert, places=9)

    def _raum(self):
        from drafter.services.daten import Datenraum
        k = self.karte(self.KARTE)
        return Datenraum(brawl_map=k, game_mode=k.game_mode,
                         provider=gemessen_mit_prior_provider()).laden()

    # --- Was die Skalierung NICHT tut -----------------------------------
    def test_die_confidence_wird_nicht_mitskaliert(self):
        """Der Kern von "Confidence nicht aufblasen", exakt geprueft.

        Die Sicherheit der Komponente ist nach der Feldrechnung
        BITGLEICH die, die die Paar-Stichproben hergeben. Sie steht in
        derselben Komponente wie der Wert, also waere sie leicht
        versehentlich mitgezogen - dann wuerde eine gute Position im
        Feld wie Evidenz aussehen.
        """
        for gegner in self.GEGNER:
            self.counter("brock", gegner, 0.45, spiele=3, confidence=0.1)
        ctx = self.context(karte=self.KARTE, gegner=self.GEGNER)
        raum = self._raum()
        vorher = counters.komponente(self.brawler("brock"), ctx, raum)
        k = self.komp(self.lauf(), "brock")
        self.assertEqual(k.confidence, vorher.confidence)
        self.assertLess(k.confidence, 0.25,
                        "duenne Paar-Evidenz wurde zu sicherer Evidenz")

    def test_duenne_evidenz_steigt_im_feld_ohne_sicherer_zu_werden(self):
        """Gute Position im Feld, duenne Belege - beides muss sichtbar bleiben.

        Drei Partien je Matchup: die Paar-Shrinkage hat den Vorteil
        bereits auf einen Bruchteil zusammengezogen (das ist richtig so
        und bleibt unangetastet). Die Feldrechnung hebt ihn danach
        gegenueber dem Feld - die Sicherheit hebt sie nicht mit.
        """
        for gegner in self.GEGNER:
            self.counter("brock", gegner, 0.45, spiele=3, confidence=0.1)
        k = self.komp(self.lauf(), "brock")
        self.assertGreater(k.wert, k.rohwert,
                           "das Feld hebt den besten Counter nicht")
        self.assertLess(k.confidence, 0.25)

    def test_paarwerte_selbst_bleiben_unberuehrt(self):
        """Die Skalierung sitzt NACH der Paarrechnung, nicht in ihr.

        Der Paarwert ist NICHT 0.45: die Messung wird mit dem gepflegten
        Prior gemischt, und dass sie das tut, gehoert zu
        test_counter_messung.py. Hier zaehlt nur, dass die Feldrechnung
        daran nichts aendert - vor und nach dem Pool derselbe Wert.
        """
        self.counter("brock", "bull", 0.45)
        raum = self._raum()
        ctx = self.context(karte=self.KARTE, gegner=self.GEGNER)
        vorher = counters.vorteil(self.brawler("brock"), self.brawler("bull"), raum)
        counters.komponenten_fuer_pool(list(raum.brawler), ctx, raum)
        nachher = counters.vorteil(self.brawler("brock"), self.brawler("bull"), raum)
        self.assertEqual(vorher, nachher)
        self.assertTrue(str(vorher[2]).startswith("Measured"))
        self.assertGreater(vorher[0], 0.3, "die Messung schlaegt nicht durch")

    def test_rohwert_bleibt_der_alte_komponentenwert(self):
        """`rohwert` ist exakt das, was `komponente()` vorher geliefert hat."""
        for gegner in self.GEGNER:
            self.counter("brock", gegner, 0.3)
        ctx = self.context(karte=self.KARTE, gegner=self.GEGNER)
        raum = self._raum()
        einzeln = counters.komponente(self.brawler("brock"), ctx, raum)
        liste = self.lauf()
        self.assertAlmostEqual(self.komp(liste, "brock").rohwert, einzeln.wert,
                               places=9)


class PhasenTest(SkalaBasis):
    """First, Mid und Last duerfen sich NUR ueber die Phasengewichte unterscheiden.

    Es gibt keine Phasen-Sonderregel in der Skalierung - und es soll
    auch keine geben. Der Nachweis besteht aus zwei Haelften: der
    Beitrag ist in JEDER Phase exakt Wert x Phasengewicht (die Phase
    wirkt also rein multiplikativ), und die Gewichte selbst sind die
    unveraenderten aus config.
    """

    def test_die_phase_wirkt_ausschliesslich_ueber_ihr_gewicht(self):
        for gegner in self.GEGNER:
            self.counter("brock", gegner, 0.4)
        # Die Phase haengt am Informationsstand: ein Gegner ist noch
        # frueh, drei Gegner plus zwei eigene Picks ist der Last Pick.
        lagen = (((), self.GEGNER[:1]),
                 ((), self.GEGNER),
                 (("gale", "sandy"), self.GEGNER))
        gesehen = {}
        for eigene, gegner in lagen:
            liste = self.lauf(eigene=eigene, gegner=gegner)
            e = self.empfehlung(liste, "brock")
            k = e.komponenten[config.K_COUNTER]
            phase = self.context(karte=self.KARTE, eigene=eigene,
                                 gegner=gegner).phase
            erwartet = config.gewichte_fuer(phase)[config.K_COUNTER]
            self.assertEqual(k.gewicht, erwartet, phase)
            self.assertAlmostEqual(k.beitrag, k.wert * erwartet, places=12)
            gesehen[phase] = k.gewicht
        # Der Verlauf ist der aus config - hier wird nichts nachjustiert.
        self.assertLess(gesehen[config.PHASE_EARLY], gesehen[config.PHASE_MID])
        self.assertLess(gesehen[config.PHASE_MID], gesehen[config.PHASE_LAST])

    def test_die_gewichte_selbst_sind_unveraendert(self):
        """Die Skalierung ist kein Anlass, an den Gewichten zu drehen."""
        self.assertEqual(config.PHASEN_GEWICHTE[config.PHASE_FIRST_PICK][
            config.K_COUNTER], 0.02)
        self.assertEqual(config.PHASEN_GEWICHTE[config.PHASE_MID][
            config.K_COUNTER], 0.20)
        self.assertEqual(config.PHASEN_GEWICHTE[config.PHASE_LAST][
            config.K_COUNTER], 0.29)

    def test_first_pick_bleibt_unberuehrt(self):
        """Ohne Gegner gibt es nichts zu skalieren - der First Pick aendert sich nicht."""
        liste = self.lauf(eigene=(), gegner=())
        self.assertEqual(liste[0].komponenten[config.K_COUNTER].gewicht, 0.02)
        for e in liste:
            self.assertEqual(e.komponenten[config.K_COUNTER].wert, 0.0)
            self.assertIsNone(e.komponenten[config.K_COUNTER].rohwert)
