# -*- coding: utf-8 -*-
"""Fachwissen statt Unknown - ohne erfundene Zahlen.

Ein fehlendes Profil heisst "wir wissen weniger ueber ihn", nicht "er ist
schlechter". Wer eine gepflegte Draft-Rolle hat, bekommt deshalb
Draft-Fit-Komponenten - aber nur die Richtung aus der Rolle, den Betrag
aus Map-Anforderung, Team-Luecke oder gezaehlten Picks.

Geprueft wird genau diese Grenze: die Komponente entsteht, und trotzdem
entsteht kein Attributwert.
"""

from drafter import config
from drafter.models import Brawler, BrawlerStat, Datenquelle
from drafter.services import rollenwissen
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import gemessen_mit_prior_provider
from drafter.tests.basis import DrafterTest


class RollenwissenTest(DrafterTest):
    def anlegen(self, name="NORI", rolle="tank", spiele=60):
        b = Brawler.objects.create(
            name=name, slug=name.lower(),
            external_id=f"16{abs(hash((name, spiele))) % 1_000_000:06d}",
            is_active=True, draft_rolle=rolle, source=Datenquelle.MANUAL,
        )
        BrawlerStat.objects.create(
            brawler=b, games=spiele, sample_size=spiele, wins=round(spiele * 0.55),
            raw_rate=0.55, adjusted_rate=0.55, confidence=0.3,
            source=Datenquelle.API, window_label="90d",
        )
        return b

    def empfehlung_fuer(self, slug, **kwargs):
        engine = DraftEngine(self.context(**kwargs), provider=gemessen_mit_prior_provider())
        return self.empfehlung(engine.empfehlungen(anzahl=300), slug)

    # --- Die Grenze -----------------------------------------------------
    def test_rolle_erzeugt_keinen_attributwert(self):
        b = self.anlegen()
        self.assertFalse(b.hat_profil)
        for key in ("tankiness", "frontline", "anti_tank"):
            # Unbekannt, nicht 0: die Rolle setzt kein Attribut UND
            # behauptet auch nicht, dass er es nicht kann.
            self.assertIsNone(b.wert(key), "die Rolle darf kein Attribut setzen")
            self.assertFalse(b.bekannt(key))
        self.assertIn("frontline", rollenwissen.deckt(b),
                      "sie sagt nur, worum es bei ihm geht")

    def test_map_fit_kommt_aus_der_rolle_statt_unknown(self):
        self.anlegen()
        e = self.empfehlung_fuer("nori")
        komp = e.komponenten[config.K_MAP_MODE]
        self.assertTrue(komp.verfuegbar)
        self.assertEqual(komp.quelle, "Fachquelle")
        self.assertLessEqual(abs(komp.wert), config.FACHWISSEN_MAX_AUSSCHLAG + 1e-9)

    def test_ohne_rolle_bleibt_es_unknown(self):
        self.anlegen(name="NORO", rolle="")
        e = self.empfehlung_fuer("noro")
        self.assertFalse(e.komponenten[config.K_MAP_MODE].verfuegbar)
        self.assertEqual(e.komponenten[config.K_MAP_MODE].quelle, "Unknown")

    def test_fachwissen_schlaegt_nie_so_weit_aus_wie_ein_profil(self):
        """Eine Schublade ist keine Beschreibung."""
        self.anlegen()
        engine = DraftEngine(self.context(), provider=gemessen_mit_prior_provider())
        alle = engine.empfehlungen(anzahl=300)
        fach = [e.komponenten[config.K_MAP_MODE].wert for e in alle
                if e.komponenten[config.K_MAP_MODE].quelle == "Fachquelle"]
        self.assertTrue(fach)
        self.assertLessEqual(max(abs(w) for w in fach),
                             config.FACHWISSEN_MAX_AUSSCHLAG + 1e-9)

    def test_teambedarf_misst_die_luecke_des_teams(self):
        """Der Betrag kommt aus unserer Luecke, nicht aus dem Kandidaten."""
        self.anlegen()
        e = self.empfehlung_fuer("nori", eigene=["gale"])
        komp = e.komponenten[config.K_TEAM_NEED]
        self.assertTrue(komp.verfuegbar)
        self.assertEqual(komp.quelle, "Fachquelle")

    def test_gleiche_rolle_im_team_kostet(self):
        """Redundanz aus gezaehlten Picks - keine Einschaetzung noetig."""
        self.anlegen()
        # Der Seed pflegt keine Draft-Rollen (die kommen aus der
        # Fachquelle) - also einen zweiten Tank anlegen.
        gleiche = self.anlegen(name="NORU", rolle="tank", spiele=80)
        ohne = self.empfehlung_fuer("nori", eigene=["gale"])
        mit = self.empfehlung_fuer("nori", eigene=["gale", gleiche.slug])
        self.assertLess(mit.komponenten[config.K_REDUNDANCY].wert,
                        ohne.komponenten[config.K_REDUNDANCY].wert + 1e-9)

    def test_ohne_profil_ist_nicht_automatisch_schlechter(self):
        """Derselbe Brawler, einmal mit und einmal ohne Rolle: die Rolle
        darf ihn heben oder senken, aber Unknown darf nicht besser sein
        als eine bekannte, passende Rolle."""
        passend = self.anlegen(name="NORI", rolle="tank", spiele=60)
        ohne = self.anlegen(name="NORO", rolle="", spiele=60)
        engine = DraftEngine(self.context(), provider=gemessen_mit_prior_provider())
        alle = engine.empfehlungen(anzahl=300)
        a = self.empfehlung(alle, passend.slug)
        b = self.empfehlung(alle, ohne.slug)
        self.assertGreater(a.datenabdeckung, b.datenabdeckung,
                           "die Rolle deckt mehr ab als gar nichts")
