# -*- coding: utf-8 -*-
"""Verhaltenstests: reagiert das Modell richtig auf eine Lage?

Diese Datei prueft **keine Platzierungen**. Ein Platz haengt von allen
zwanzig Kandidaten gleichzeitig ab; er verschiebt sich, sobald irgendwo
ein Attribut angepasst wird, und ein fehlgeschlagener Platz-Test sagt
nicht, was kaputt ist. Schlimmer noch: solche Tests verleiten dazu, an
den Gewichten zu drehen, bis ein Lieblingsbeispiel wieder oben steht -
also genau das Uebertrainieren auf Einzelfaelle, das dem Modell schadet.

Stattdessen wird die **Richtung** geprueft, und zwar an den
Score-Komponenten selbst:

    Aendert sich die Lage so, muss dieser Beitrag steigen/fallen.

Die meisten Tests vergleichen zwei Laufe derselben Engine mit genau
einem Unterschied. Damit ist ein Fehlschlag immer eindeutig zuzuordnen.
"""

from drafter import config
from drafter.services.team_coverage import anforderungen_mit_gegner
from drafter.tests.basis import DrafterTest

# Knockout auf Belle's Rock: die Map verlangt Reichweite und sicheren
# Schaden, aber KEIN Anti-Tank und KEIN Anti-Thrower. Dadurch stammt
# jeder Bedarf in diese Richtung ausschliesslich vom Gegnerteam - genau
# das soll hier gemessen werden.
NEUTRALE_MAP = "belles-rock"


class GegnerErzeugtBedarfTest(DrafterTest):
    """Was der Gegner picked, muss den Teambedarf verschieben."""

    def test_zwei_gegnerische_tanks_erzeugen_anti_tank_bedarf(self):
        basis = self.karte(NEUTRALE_MAP).anforderungs_vektor()
        self.assertLess(basis.get("anti_tank", 0.0), 0.2,
                        "Vorbedingung: diese Map verlangt selbst kein Anti-Tank")

        ohne = anforderungen_mit_gegner(basis, [])
        mit = anforderungen_mit_gegner(
            basis, [self.brawler("bull"), self.brawler("frank")]
        )
        self.assertGreater(mit["anti_tank"], ohne.get("anti_tank", 0.0))
        self.assertGreater(mit["anti_tank"], 0.7)

    def test_anti_tank_beitrag_steigt_gegen_zwei_tanks(self):
        """Der Fall aus der Aufgabenstellung, an der Komponente gemessen."""
        ohne_tanks = self.alle(karte=NEUTRALE_MAP, gegner=["piper", "brock"])
        mit_tanks = self.alle(karte=NEUTRALE_MAP, gegner=["bull", "frank"])

        # Colette ist der Anti-Tank im Demo-Bestand (anti_tank 95).
        vorher = self.wert(ohne_tanks, "colette", config.K_TEAM_NEED)
        nachher = self.wert(mit_tanks, "colette", config.K_TEAM_NEED)
        self.assertGreater(
            nachher, vorher,
            "Gegen zwei Tanks muss der Teambedarfs-Beitrag eines Anti-Tanks steigen",
        )

    def test_anti_tank_profitiert_relativ_staerker_als_ein_brawler_ohne_anti_tank(self):
        """Relativ, nicht absolut - der Kern eines Verhaltenstests.

        Gegen Tanks steigt der Bedarf insgesamt; entscheidend ist, dass
        er fuer den Anti-Tank STAERKER steigt als fuer jemanden ohne
        diese Antwort. Sonst haette sich nur das Niveau verschoben.
        """
        ohne_tanks = self.alle(karte=NEUTRALE_MAP, gegner=["piper", "brock"])
        mit_tanks = self.alle(karte=NEUTRALE_MAP, gegner=["bull", "frank"])

        # Stu hat kein Anti-Tank (0) und ist ansonsten ein brauchbarer Pick.
        abstand_vorher = (
            self.wert(ohne_tanks, "colette", config.K_TEAM_NEED)
            - self.wert(ohne_tanks, "stu", config.K_TEAM_NEED)
        )
        abstand_nachher = (
            self.wert(mit_tanks, "colette", config.K_TEAM_NEED)
            - self.wert(mit_tanks, "stu", config.K_TEAM_NEED)
        )
        self.assertGreater(abstand_nachher, abstand_vorher)

    def test_gegnerischer_thrower_erzeugt_anti_thrower_bedarf(self):
        # Der Referenzkandidat (Piper) darf in KEINER der beiden Lagen
        # selbst gepickt sein, sonst fehlt er in den Empfehlungen und der
        # Vergleich laeuft ins Leere.
        ohne = self.alle(karte=NEUTRALE_MAP, gegner=["belle"])
        mit = self.alle(karte=NEUTRALE_MAP, gegner=["tick"])
        # Max hat anti_thrower 75, Piper hat 0.
        self.assertGreater(
            self.wert(mit, "max", config.K_TEAM_NEED)
            - self.wert(mit, "piper", config.K_TEAM_NEED),
            self.wert(ohne, "max", config.K_TEAM_NEED)
            - self.wert(ohne, "piper", config.K_TEAM_NEED),
        )

    def test_counter_beitrag_reagiert_auf_den_konkreten_gegner(self):
        gegen_tank = self.alle(karte=NEUTRALE_MAP, gegner=["bull"])
        gegen_sniper = self.alle(karte=NEUTRALE_MAP, gegner=["piper"])
        # Gale ist gegen Bull stark und gegen Piper nicht.
        self.assertGreater(
            self.wert(gegen_tank, "gale", config.K_COUNTER),
            self.wert(gegen_sniper, "gale", config.K_COUNTER),
        )


class EigenesTeamErzeugtBedarfTest(DrafterTest):
    """Was wir selbst gepickt haben, muss den Bedarf ebenso verschieben."""

    def test_zwei_nahkaempfer_lassen_reichweite_relativ_profitieren(self):
        """Der zweite Fall aus der Aufgabenstellung.

        Gemessen wird der ABSTAND zwischen einem Reichweiten-Kandidaten
        und einem weiteren Nahkaempfer. Er muss groesser werden, sobald
        das eigene Team schon zwei Nahkaempfer hat.
        """
        ausgewogen = self.alle(karte=NEUTRALE_MAP, eigene=["belle", "sandy"])
        zwei_nahkaempfer = self.alle(karte=NEUTRALE_MAP, eigene=["bull", "rosa"])

        def abstand(empfehlungen):
            return (
                self.wert(empfehlungen, "piper", config.K_TEAM_NEED)
                - self.wert(empfehlungen, "darryl", config.K_TEAM_NEED)
            )

        self.assertGreater(abstand(zwei_nahkaempfer), abstand(ausgewogen))

    def test_kontrolle_profitiert_ebenfalls_von_einem_nahkampflastigen_team(self):
        ausgewogen = self.alle(karte="hart-rock-mine", eigene=["belle", "sandy"])
        zwei_nahkaempfer = self.alle(karte="hart-rock-mine", eigene=["bull", "rosa"])
        self.assertGreater(
            self.wert(zwei_nahkaempfer, "gale", config.K_TEAM_NEED),
            self.wert(ausgewogen, "gale", config.K_TEAM_NEED),
        )

    def test_redundanz_waechst_mit_jedem_weiteren_gleichartigen_pick(self):
        keiner = self.alle(karte="hart-rock-mine", eigene=["belle"])
        einer = self.alle(karte="hart-rock-mine", eigene=["belle", "bull"])
        zwei = self.alle(karte="hart-rock-mine", eigene=["bull", "frank"])

        strafe = lambda e: self.wert(e, "rosa", config.K_REDUNDANCY)
        self.assertLessEqual(strafe(einer), strafe(keiner))
        self.assertLess(strafe(zwei), strafe(einer))
        self.assertLess(strafe(zwei), 0.0)

    def test_synergie_reagiert_auf_die_eigenen_picks(self):
        # Gale schuetzt eine empfindliche Backline - neben Piper mehr
        # wert als neben einem Tank, der sich selbst schuetzt.
        neben_piper = self.alle(karte=NEUTRALE_MAP, eigene=["piper"])
        neben_rosa = self.alle(karte=NEUTRALE_MAP, eigene=["rosa"])
        self.assertGreater(
            self.wert(neben_piper, "gale", config.K_SYNERGY),
            self.wert(neben_rosa, "gale", config.K_SYNERGY),
        )


class AufschluesselungTest(DrafterTest):
    """Die Aufschluesselung muss vollstaendig und stimmig sein."""

    LAGEN = (
        {},
        dict(gegner=["bull"]),
        dict(eigene=["gale"], gegner=["bull", "tick"]),
        dict(eigene=["gale", "belle"], gegner=["bull", "tick", "mortis"]),
    )

    def test_jede_empfehlung_traegt_alle_komponenten(self):
        for lage in self.LAGEN:
            for e in self.engine(**lage).empfehlungen():
                zeilen = e.als_dict()["komponenten"]
                self.assertEqual(
                    [z["key"] for z in zeilen],
                    list(config.KOMPONENTEN_REIHENFOLGE),
                    msg=f"{e.brawler.name} in Lage {lage}",
                )

    def test_die_zehn_geforderten_komponenten_sind_dabei(self):
        gefordert = {
            config.K_MAP_MODE, config.K_META, config.K_COUNTER, config.K_SYNERGY,
            config.K_TEAM_NEED, config.K_DRAFT_POSITION, config.K_FLEXIBILITY,
            config.K_PERSONAL, config.K_REDUNDANCY, config.K_WEAKNESS,
        }
        zeilen = self.engine(gegner=["bull"]).empfehlungen()[0].als_dict()["komponenten"]
        self.assertTrue(gefordert <= {z["key"] for z in zeilen})

    def test_die_beitraege_ergeben_den_score(self):
        """Ohne diese Zusage waere die Aufschluesselung Dekoration."""
        for lage in self.LAGEN:
            for e in self.engine(**lage).empfehlungen():
                daten = e.als_dict()
                summe = sum(z["beitrag"] for z in daten["komponenten"])
                self.assertAlmostEqual(
                    50 + summe, daten["score"], delta=1.0,
                    msg=f"{e.brawler.name}: Summe {summe} passt nicht zu {daten['score']}",
                )

    def test_beitrag_ist_wert_mal_gewicht(self):
        for z in self.engine(gegner=["bull"]).empfehlungen()[0].als_dict()["komponenten"]:
            self.assertAlmostEqual(z["beitrag"], z["wert"] * z["gewicht"] * 50, delta=0.2)

    def test_strafkomponenten_sind_nie_positiv(self):
        for lage in self.LAGEN:
            for e in self.engine(**lage).empfehlungen(anzahl=50, mit_details=0):
                for key in config.STRAF_KOMPONENTEN:
                    self.assertLessEqual(
                        e.komponenten[key].wert, 0.0,
                        msg=f"{e.brawler.name}/{key} in Lage {lage}",
                    )

    def test_groesster_treiber_ist_wirklich_der_groesste(self):
        for e in self.engine(eigene=["gale"], gegner=["bull"]).empfehlungen():
            groesster = max(
                e.komponenten.values(), key=lambda k: abs(k.beitrag)
            )
            self.assertEqual(e.groesster_treiber.key, groesster.key)


class PersoenlicheSicherheitIsoliertTest(DrafterTest):
    """Die persoenliche Sicherheit darf NUR ihre eigene Komponente bewegen."""

    def test_andere_komponenten_bleiben_unveraendert(self):
        lage = dict(gegner=["bull"])
        ohne = self.alle(**lage)
        mit = self.alle(
            **lage,
            personal={self.brawler("gale").id: {
                "confidence": 100, "favorite": True, "avoid": False,
            }},
        )
        for key in config.KOMPONENTEN_REIHENFOLGE:
            if key in (config.K_PERSONAL, config.K_UNCERTAINTY):
                continue
            self.assertAlmostEqual(
                self.wert(mit, "gale", key), self.wert(ohne, "gale", key), places=6,
                msg=f"{key} haette sich nicht aendern duerfen",
            )
        self.assertGreater(
            self.wert(mit, "gale", config.K_PERSONAL),
            self.wert(ohne, "gale", config.K_PERSONAL),
        )


class DemoDatenlageTest(DrafterTest):
    """Demo bleibt Demo - in jeder Ausgabe des Systems."""

    DECKEL = 0.35

    def test_keine_empfehlung_ueberschreitet_den_demo_deckel(self):
        for lage in ({}, dict(gegner=["bull"]), dict(eigene=["gale"], gegner=["bull"])):
            for e in self.engine(**lage).empfehlungen(anzahl=50, mit_details=0):
                self.assertLessEqual(e.confidence, self.DECKEL)

    def test_endanalyse_weist_die_demo_lage_aus(self):
        analyse = self.engine(
            eigene=["gale", "belle", "max"], gegner=["buster", "gene", "tick"]
        ).endanalyse()
        self.assertTrue(analyse["datenlage"]["nur_demo"])
        self.assertLessEqual(analyse["datenlage"]["confidence"], self.DECKEL)
        self.assertIn("Demo", analyse["datenlage"]["hinweis"])
        self.assertLessEqual(analyse["siegchance"]["confidence"], self.DECKEL)
        self.assertTrue(analyse["siegchance"]["ist_heuristik"])
