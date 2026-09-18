# -*- coding: utf-8 -*-
"""Balance zwischen CURRENT STRENGTH und DRAFT FIT.

Vier synthetische Lagen, keine Brawlernamen. Geprueft wird die Statik des
Modells, nicht eine Rangliste:

    A  starke Messung, wenig Wissen, neutraler Draft
    B  schwache Messung, volles Wissen, neutraler Draft
    C  schwache Messung, aber ausserordentlich gutes Counter-Fit
    D  starke Messung, aber schlechtes konkretes Fit

Erwartet: A > B (wer messbar laeuft, steht vor dem, ueber den wir nur
viel wissen). C darf A ueberholen, wenn das konkrete Fit stark genug ist -
sonst waere die Empfehlung eine Tierlist. D faellt gegenueber A, weil das
konkrete Fit schlecht ist.

"Neutraler Draft" wird nicht behauptet, sondern hergestellt: B bekommt die
Eigenschaften des Brawlers, dessen Map-Fit auf dieser Map am naechsten bei
0 liegt. Sonst haenge das Ergebnis daran, welches Profil zufaellig kopiert
wurde.
"""

from drafter import config
from drafter.models import Brawler, BrawlerStat, Datenquelle
from drafter.models.stats import CounterStat
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import gemessen_mit_prior_provider
from drafter.tests.basis import DrafterTest

FELD_SPIELE = 300


class BalanceTest(DrafterTest):
    GEGNER = ["bull", "tick", "poco"]

    def setUp(self):
        # Ein gemessenes Feld, gegen das sich "stark" und "schwach"
        # ueberhaupt bestimmen laesst - sonst gibt es keine Lage im Feld.
        for i, b in enumerate(Brawler.objects.filter(is_active=True)[:20]):
            rate = 0.47 + 0.003 * i
            BrawlerStat.objects.create(
                brawler=b, games=FELD_SPIELE, sample_size=FELD_SPIELE,
                wins=round(FELD_SPIELE * rate), raw_rate=rate, adjusted_rate=rate,
                confidence=0.5, source=Datenquelle.API, window_label="90d",
            )

    # --- Bausteine ------------------------------------------------------
    def kandidat(self, name, rate, profil_von=None, rolle=""):
        b = Brawler.objects.create(
            name=name, slug=name.lower(), external_id=f"9{abs(hash(name)) % 10000:04d}",
            is_active=True, source=Datenquelle.MANUAL, draft_rolle=rolle,
        )
        if profil_von is not None:
            b.attributes = dict(profil_von.attributes)
            b.draft_values = dict(profil_von.draft_values)
            b.role = profil_von.role
            b.tags = list(profil_von.tags or [])
            b.save()
        BrawlerStat.objects.create(
            brawler=b, games=1200, sample_size=1200, wins=round(1200 * rate),
            raw_rate=rate, adjusted_rate=rate, confidence=0.6,
            source=Datenquelle.API, window_label="90d",
        )
        return b

    def counter(self, kandidat, gegner_slug, vorteil, spiele=800):
        """Gemessenes Matchup - kanonische Richtung, wie der Constraint verlangt."""
        gegner = self.brawler(gegner_slug)
        a, b = (kandidat, gegner) if kandidat.id < gegner.id else (gegner, kandidat)
        wert = vorteil if a.id == kandidat.id else -vorteil
        CounterStat.objects.create(
            brawler=a, enemy=b, games=spiele, sample_size=spiele, advantage=wert,
            confidence=0.8, source=Datenquelle.API, window_label="90d",
        )

    def neutrales_profil(self, karte="hard-rock-mine"):
        """Der Brawler, dessen Map-Fit hier am wenigsten ausschlaegt."""
        engine = DraftEngine(self.context(karte=karte),
                             provider=gemessen_mit_prior_provider())
        kandidaten = [
            e for e in engine.empfehlungen(anzahl=300)
            if e.brawler.hat_profil and e.komponenten[config.K_MAP_MODE].verfuegbar
        ]
        return min(kandidaten,
                   key=lambda e: abs(e.komponenten[config.K_MAP_MODE].wert)).brawler

    def score(self, slug, **kwargs):
        engine = DraftEngine(self.context(**kwargs), provider=gemessen_mit_prior_provider())
        e = self.empfehlung(engine.empfehlungen(anzahl=300), slug)
        self.assertIsNotNone(e, f"{slug} wurde nicht bewertet")
        return e

    # --- Die vier Faelle ------------------------------------------------
    def test_a_schlaegt_b(self):
        """Gemessene Staerke ohne Wissen vor Wissen ohne gemessene Staerke."""
        neutral = self.neutrales_profil()
        self.kandidat("AAA", rate=0.60)                       # A: stark, kein Profil
        self.kandidat("BBB", rate=0.42, profil_von=neutral)   # B: schwach, volles Profil
        a, b = self.score("aaa"), self.score("bbb")
        self.assertGreater(a.roher_score, b.roher_score)
        # ... und zwar aus der Staerke, nicht aus einem Draft-Fit-Vorteil.
        self.assertGreater(a.gruppen_beitrag(config.G_CURRENT_STRENGTH),
                           b.gruppen_beitrag(config.G_CURRENT_STRENGTH))

    def test_c_ueberholt_a_wenn_das_fit_stark_genug_ist(self):
        """Gestaffelt statt an einem Punkt: ab wann kippt das Fit die Meta?

        Geprueft wird der Zusammenhang, nicht eine Schwelle - ein fester
        Grenzwert waere eine Rangregel. C liegt knapp unter dem Feld, A
        deutlich darueber; mit wachsendem Counter-Vorteil muss C steigen
        und A irgendwann ueberholen.
        """
        self.kandidat("AAA", rate=0.60)
        lage = dict(gegner=self.GEGNER, first_pick=False)
        a = self.score("aaa", **lage).roher_score

        verlauf = []
        for i, vorteil in enumerate((0.10, 0.35, 0.60, 0.90)):
            c = self.kandidat(f"CC{i}", rate=0.48)
            for gegner in self.GEGNER:
                self.counter(c, gegner, vorteil=vorteil)
            verlauf.append(self.score(f"cc{i}", **lage).roher_score)

        self.assertEqual(verlauf, sorted(verlauf), "besseres Fit muss besser stehen")
        self.assertLess(verlauf[0], a, "ein schwaches Fit kippt die Meta nicht")
        self.assertGreater(verlauf[-1], a, "ein sehr starkes Fit muss sie kippen")

    def test_meta_bodensatz_laesst_sich_nicht_wegkontern(self):
        """Wer im Feld ganz unten steht, kommt auch mit Traummatchup nicht vorbei.

        Bewusst festgehalten, weil es eine Entscheidung ist und keine
        Nebenwirkung: der Abstand zwischen dem oberen und dem unteren Rand
        des Feldes ist groesser, als ein einzelnes Counter-Fit tragen kann.
        """
        self.kandidat("AAA", rate=0.60)
        c = self.kandidat("CCC", rate=0.42)
        for gegner in self.GEGNER:
            self.counter(c, gegner, vorteil=0.95)
        lage = dict(gegner=self.GEGNER, first_pick=False)
        a, cc = self.score("aaa", **lage), self.score("ccc", **lage)
        self.assertGreater(cc.gruppen_beitrag(config.G_DRAFT_FIT),
                           abs(cc.gruppen_beitrag(config.G_CURRENT_STRENGTH)))
        self.assertLess(cc.roher_score, a.roher_score)

    def test_d_faellt_durch_schlechtes_fit(self):
        """Starke Meta, aber der konkrete Draft bestraft ihn."""
        self.kandidat("AAA", rate=0.60)
        d = self.kandidat("DDD", rate=0.60)
        for gegner in self.GEGNER:
            self.counter(d, gegner, vorteil=-0.85)
        lage = dict(gegner=self.GEGNER, first_pick=False)
        a, dd = self.score("aaa", **lage), self.score("ddd", **lage)
        self.assertLess(dd.roher_score, a.roher_score)
        self.assertLess(dd.gruppen_beitrag(config.G_DRAFT_FIT), 0)

    def test_staerke_allein_macht_keine_tierlist(self):
        """Der Meta-Anteil bleibt begrenzt - Draft Fit muss ihn kippen koennen."""
        a = self.kandidat("AAA", rate=0.60)
        lage = dict(gegner=self.GEGNER, first_pick=False)
        e = self.score("aaa", **lage)
        cs = abs(e.gruppen_beitrag(config.G_CURRENT_STRENGTH))
        moeglich = config.PHASEN_GEWICHTE[config.PHASE_MID][config.K_COUNTER] * 50
        self.assertLess(cs, moeglich,
                        "die Meta darf nicht mehr wiegen als ein volles Counter-Fit")
