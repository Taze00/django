# -*- coding: utf-8 -*-
"""Matchup-Zuordnung und Rohscore.

Die Zuordnung wird gegen eine Brute-Force-Rechnung geprueft, nicht gegen
erwartete Paare: welches Paar "richtig" ist, haengt an den Daten - dass
die Gesamtsumme maximal ist, nicht.
"""

import random
from itertools import permutations
from unittest import mock

from drafter.services import coach
from drafter.services.counters import vorteil
from drafter.services.scoring import Empfehlung, Komponente
from drafter.tests.basis import DrafterTest


def _bestmoegliche_summe(eigene, gegner, wert):
    """Referenz: jede injektive Zuordnung durchprobieren."""
    if len(eigene) <= len(gegner):
        return max(
            sum(wert(a, b) for a, b in zip(eigene, auswahl))
            for auswahl in permutations(gegner, len(eigene))
        )
    return max(
        sum(wert(a, b) for a, b in zip(auswahl, gegner))
        for auswahl in permutations(eigene, len(gegner))
    )


class GlobaleZuordnungTest(DrafterTest):
    def setUp(self):
        from drafter.services.daten import Datenraum
        self.raum = Datenraum(brawl_map=self.karte()).laden()
        self.alle = list(self.brawler("gale").__class__.objects.all())

    def _pruefe_zufallsdrafts(self, anzahl_eigene, anzahl_gegner, durchlaeufe=40):
        zufall = random.Random(anzahl_eigene * 10 + anzahl_gegner)
        wert = lambda a, b: vorteil(a, b, self.raum)[0]
        for _ in range(durchlaeufe):
            pool = zufall.sample(self.alle, anzahl_eigene + anzahl_gegner)
            eigene, gegner = pool[:anzahl_eigene], pool[anzahl_eigene:]
            ergebnis = coach.matchup_zuordnung(eigene, gegner, self.raum)

            erreicht = sum(wert(self.brawler(m["unser_slug"]), self.brawler(m["gegner_slug"]))
                           for m in ergebnis)
            self.assertAlmostEqual(
                erreicht, _bestmoegliche_summe(eigene, gegner, wert), places=6,
                msg=f"{[b.name for b in eigene]} vs {[b.name for b in gegner]}",
            )
            # Niemand doppelt, und die kleinere Seite komplett zugeordnet.
            self.assertEqual(len({m["unser"] for m in ergebnis}), len(ergebnis))
            self.assertEqual(len({m["gegner"] for m in ergebnis}), len(ergebnis))
            self.assertEqual(len(ergebnis), min(anzahl_eigene, anzahl_gegner))

    def test_drei_gegen_drei_ist_global_optimal(self):
        self._pruefe_zufallsdrafts(3, 3)

    def test_drei_eigene_gegen_zwei_gegner_ist_global_optimal(self):
        """Hier lag der Fehler: der dritte eigene Spieler fiel heraus."""
        self._pruefe_zufallsdrafts(3, 2)

    def test_zwei_eigene_gegen_drei_gegner_ist_global_optimal(self):
        self._pruefe_zufallsdrafts(2, 3)

    def test_zuordnung_ist_nicht_greedy(self):
        """Konstruierter Fall, an dem das beste Einzelmatchup zuerst scheitert.

            gegen   X     Y     Z
            A      0.90  0.80  0.00
            B      0.85 -0.50 -0.50
            C      0.00  0.00  0.00

        Greedy nimmt A-X (0.90), dann bleibt B nur -0.50: Summe 0.40.
        Optimal ist B-X, A-Y, C-Z: Summe 1.65.
        """
        a, b, c = self.brawler("gale"), self.brawler("belle"), self.brawler("max")
        x, y, z = self.brawler("bull"), self.brawler("tick"), self.brawler("piper")
        tabelle = {
            (a.id, x.id): 0.90, (a.id, y.id): 0.80, (a.id, z.id): 0.00,
            (b.id, x.id): 0.85, (b.id, y.id): -0.50, (b.id, z.id): -0.50,
            (c.id, x.id): 0.00, (c.id, y.id): 0.00, (c.id, z.id): 0.00,
        }
        with mock.patch.object(
            coach, "vorteil", lambda p, q, raum: (tabelle[(p.id, q.id)], None, "test")
        ):
            ergebnis = coach.matchup_zuordnung([a, b, c], [x, y, z], self.raum)

        paare = {(m["unser"], m["gegner"]) for m in ergebnis}
        self.assertEqual(paare, {("Belle", "Bull"), ("Gale", "Tick"), ("Max", "Piper")})
        self.assertAlmostEqual(sum(m["vorteil"] for m in ergebnis), 1.65, places=2)

    def test_ausgabe_folgt_der_teamreihenfolge(self):
        eigene = [self.brawler(s) for s in ("max", "gale", "belle")]
        gegner = [self.brawler(s) for s in ("bull", "tick", "gene")]
        ergebnis = coach.matchup_zuordnung(eigene, gegner, self.raum)
        self.assertEqual([m["unser"] for m in ergebnis], ["Max", "Gale", "Belle"])


class RohscoreTest(DrafterTest):
    def _empfehlung(self, *beitraege):
        komponenten = {
            f"k{i}": Komponente(key=f"k{i}", wert=-1.0, gewicht=abs(b))
            for i, b in enumerate(beitraege)
        }
        return Empfehlung(brawler=self.brawler("gale"), komponenten=komponenten)

    def test_score_wird_geklemmt_der_rohscore_nicht(self):
        e = self._empfehlung(0.8, 0.7)   # Summe -1.5
        self.assertAlmostEqual(e.roher_score, -1.5)
        self.assertEqual(e.score, -1.0)
        self.assertEqual(e.anzeige_score, 0)
        self.assertAlmostEqual(e.als_dict()["score_roh"], -1.5)

    def test_rohscore_unterscheidet_was_der_geklemmte_score_gleichsetzt(self):
        tief = self._empfehlung(0.8, 0.7)      # -1.5
        weniger_tief = self._empfehlung(0.6, 0.6)  # -1.2
        self.assertEqual(tief.score, weniger_tief.score)
        self.assertLess(tief.roher_score, weniger_tief.roher_score)

    def test_engine_sortiert_nach_rohscore(self):
        liste = self.engine(eigene=["gale"], gegner=["bull", "tick"]).empfehlungen(
            anzahl=50, mit_details=0
        )
        rohwerte = [e.roher_score for e in liste]
        self.assertEqual(rohwerte, sorted(rohwerte, reverse=True))
