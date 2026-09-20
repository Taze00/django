# -*- coding: utf-8 -*-
"""Die vier Infrastruktur-Reparaturen vom 2026-09-19.

1. Der Mapkatalog kommt aus beobachteten Ranked-Partien, nicht aus einem
   statischen Demo-Satz.
2. Hot Zone ist ein Modus mit Zielprofil.
3. Draft-Position und Flexibilitaet haengen nicht mehr am Profilbesitz.
4. Fachwissen und Messung im Objective Fit sind gegeneinander kalibriert.
"""

from datetime import timedelta

from django.utils import timezone

from drafter import config
from drafter.models import BrawlMap, Brawler, BrawlerStat, Datenquelle, GameMode
from drafter.models.matches import Match
from drafter.services import objective
from drafter.services.anfrage import context_aus_daten
from drafter.services.draft_engine import DraftEngine
from drafter.services.providers.datenbank import gemessen_mit_prior_provider
from drafter.tests.basis import DrafterTest


class MapkatalogTest(DrafterTest):
    def beobachtet(self, name, modus, partien, tage_alt=1, external_id="99001"):
        karte = BrawlMap.objects.create(
            name=name, slug=name.lower().replace(" ", "-"), external_id=external_id,
            game_mode=modus, is_active=False, source=Datenquelle.API,
            observed_ranked_games=partien,
            last_seen_ranked=timezone.now() - timedelta(days=tage_alt),
        )
        return karte

    def test_beobachtete_map_wird_waehlbar(self):
        karte = self.beobachtet("Neue Arena", self.karte().game_mode, 200)
        self.assertFalse(karte.is_active)
        self.assertTrue(karte.ranked_aktuell)
        self.assertTrue(karte.waehlbar)
        self.assertIn(karte, BrawlMap.objects.waehlbare())

    def test_alte_beobachtung_faellt_aus_dem_fenster(self):
        karte = self.beobachtet("Alte Arena", self.karte().game_mode, 200,
                                tage_alt=config.RANKED_MAP_FENSTER_TAGE + 1)
        self.assertFalse(karte.waehlbar)
        self.assertNotIn(karte, BrawlMap.objects.waehlbare())

    def test_einzelne_partie_hebt_keine_map(self):
        karte = self.beobachtet("Rausch Arena", self.karte().game_mode,
                                config.RANKED_MAP_MIN_PARTIEN - 1)
        self.assertFalse(karte.waehlbar)

    def test_gepflegte_map_bleibt_auch_ohne_beobachtung(self):
        """Historie geht nicht verloren, nur weil die Rotation aussetzt."""
        karte = self.karte()
        self.assertTrue(karte.is_active)
        self.assertEqual(karte.observed_ranked_games, 0)
        self.assertTrue(karte.waehlbar)

    def test_gleiche_namen_mit_verschiedenen_ids_bleiben_getrennt(self):
        """Supercell vergibt denselben Namen mehrfach - die ID entscheidet.

        Bis zum 2026-09-19 verhinderte unique_together(name, game_mode),
        dass die zweite Map ueberhaupt gespeichert werden konnte.
        """
        modus = self.karte().game_mode
        eins = self.beobachtet("Doppelname", modus, 100, external_id="99101")
        zwei = BrawlMap.objects.create(
            name="Doppelname", slug="doppelname-2", external_id="99102",
            game_mode=modus, is_active=False, source=Datenquelle.API,
            observed_ranked_games=100, last_seen_ranked=timezone.now())
        self.assertNotEqual(eins.pk, zwei.pk)
        self.assertEqual(BrawlMap.objects.filter(name="Doppelname").count(), 2)
        waehlbar = BrawlMap.objects.waehlbare().filter(name="Doppelname")
        self.assertEqual(waehlbar.count(), 2, "keine Zusammenfuehrung ueber den Namen")

    def test_kommando_traegt_beobachtung_nach(self):
        from django.core.management import call_command
        import io
        karte = BrawlMap.objects.create(
            name="Frisch", slug="frisch", external_id="99201",
            game_mode=self.karte().game_mode, is_active=False, source=Datenquelle.API)
        Match.objects.create(
            fingerprint="fp-frisch", source=Datenquelle.API,
            played_at=timezone.now(), battle_type="soloRanked", is_ranked=True,
            game_mode=karte.game_mode, brawl_map=karte, mode_name="Gem Grab")
        call_command("aktualisiere_ranked_maps", stdout=io.StringIO())
        karte.refresh_from_db()
        self.assertEqual(karte.observed_ranked_games, 1)
        self.assertIsNotNone(karte.last_seen_ranked)
        # ... und `is_active` bleibt unangetastet.
        self.assertFalse(karte.is_active)


class HotZoneTest(DrafterTest):
    def test_kein_modus_ohne_waehlbare_map(self):
        """Ein Modus ohne Map ist ein Knopf ins Leere.

        Faellt bei Hot Zone auf: der Modus ist gepflegt, seine Maps kommen
        aber aus der Beobachtung - setzt die Rotation laenger aus als das
        Fenster, hat er keine.
        """
        from django.urls import reverse
        daten = self.client.get(reverse("drafter:api_katalog")).json()
        for modus in daten["modi"]:
            self.assertTrue(modus["maps"], modus["slug"])

    def test_modus_ist_draftbar(self):
        modus = GameMode.objects.get(slug="hot-zone")
        self.assertTrue(modus.is_active)
        self.assertTrue(modus.base_requirements)

    def test_zielprofil_nutzt_nur_vorhandenes_vokabular(self):
        from drafter import attributes as attr
        modus = GameMode.objects.get(slug="hot-zone")
        for key in modus.base_requirements:
            self.assertIn(key, attr.ATTRIBUT_KEYS, key)

    def test_zone_time_und_sustain_sind_kombinationen(self):
        """Keine neuen Felder - die Idee steckt in vorhandenen Begriffen."""
        from drafter import attributes as attr
        for erfunden in ("zone_time", "sustain", "anti_heal"):
            self.assertNotIn(erfunden, attr.ATTRIBUT_KEYS)
        anforderungen = GameMode.objects.get(slug="hot-zone").base_requirements
        for teil in ("zone_control", "survivability", "healing"):
            self.assertIn(teil, anforderungen)

    def test_keine_hot_zone_sonderlogik_im_objective(self):
        with open(objective.__file__, encoding="utf-8") as datei:
            inhalt = datei.read().lower()
        for name in ("hot_zone", "hotzone", "hot zone"):
            self.assertNotIn(name, inhalt)


class DraftlageTest(DrafterTest):
    """Draft-Position und Flexibilitaet ohne Profilvorteil."""

    def engine(self, **kwargs):
        return DraftEngine(self.context(**kwargs), provider=gemessen_mit_prior_provider())

    def test_felder_liegen_bei_null(self):
        """Profilbesitz ist eine Information, kein Bonus.

        Seit dem 2026-09-20 noch strenger: die Demo-Draftwerte speisen
        Draft-Position und Flexibilitaet gar nicht mehr. Ohne gemessene
        Ableitung ist beides schlicht nicht verfuegbar - ein gepflegtes
        Profil allein erzeugt hier keinen Wert mehr.
        """
        empfehlungen = self.engine().empfehlungen(anzahl=300)
        for key in (config.K_DRAFT_POSITION, config.K_FLEXIBILITY):
            werte = [e.komponenten[key].wert for e in empfehlungen
                     if e.komponenten[key].verfuegbar]
            if werte:
                self.assertAlmostEqual(sum(werte) / len(werte), 0.0, delta=0.15,
                                       msg=f"{key}: das Feld ist nicht zentriert")
            mit_profil = [e for e in empfehlungen if e.brawler.hat_profil]
            self.assertTrue(mit_profil, "Testlage ohne profilierte Brawler")
            for e in mit_profil:
                if e.komponenten[key].verfuegbar:
                    self.assertNotEqual(
                        e.komponenten[key].quelle, "Profile Prior",
                        f"{key}: gepflegte Draftwerte duerfen nicht mehr tragen")

    def test_unbekannt_bleibt_neutral(self):
        ohne = Brawler.objects.create(name="NORU", slug="noru", external_id="99301",
                                      is_active=True, source=Datenquelle.MANUAL)
        BrawlerStat.objects.create(
            brawler=ohne, games=40, sample_size=40, wins=20, raw_rate=0.5,
            adjusted_rate=0.5, confidence=0.3, source=Datenquelle.API,
            window_label="90d")
        e = self.empfehlung(self.engine().empfehlungen(anzahl=300), "noru")
        for key in (config.K_DRAFT_POSITION, config.K_FLEXIBILITY):
            komp = e.komponenten[key]
            if not komp.verfuegbar:
                self.assertEqual(komp.beitrag, 0.0)

    def test_gemessene_ableitung_dreht_mit_der_phase(self):
        """Wer stark vom Gegner abhaengt: blind riskant, als Last Pick wertvoll."""
        erste = self.engine().empfehlungen(anzahl=300)
        letzte = self.engine(eigene=["gale", "sandy"],
                             gegner=["bull", "belle", "brock"],
                             first_pick=False).empfehlungen(anzahl=300)
        def gemessen(liste):
            return {e.brawler.slug: e.komponenten[config.K_DRAFT_POSITION].wert
                    for e in liste
                    if e.komponenten[config.K_DRAFT_POSITION].quelle == "Measured + Prior"}
        a, b = gemessen(erste), gemessen(letzte)
        gemeinsam = set(a) & set(b)
        if gemeinsam:
            gedreht = sum(1 for s in gemeinsam if a[s] * b[s] <= 0)
            self.assertGreater(gedreht, len(gemeinsam) * 0.5,
                               "das Vorzeichen muss mit der Draftposition drehen")


class ObjectiveKalibrierungTest(DrafterTest):
    """Fachwissen zieht sich mit wachsender Evidenz zurueck."""

    def anteile(self, n):
        w = n / (n + config.OBJECTIVE_EVIDENZ_K) if n else 0.0
        return w, (1 - w) * config.OBJECTIVE_FACHWISSEN_DAEMPFUNG

    def test_staffelung_ist_monoton(self):
        mess, fach = zip(*(self.anteile(n) for n in (0, 20, 200, 1000)))
        self.assertEqual(list(mess), sorted(mess))
        self.assertEqual(list(fach), sorted(fach, reverse=True))

    def test_ohne_daten_bleibt_fachwissen_konservativ(self):
        _, fach = self.anteile(0)
        self.assertLessEqual(fach, 0.5)
        # Der groesste rein qualitative Ausschlag liegt unter dem halben
        # Vollausschlag einer Messung.
        self.assertLess(fach * config.FACHWISSEN_MAX_AUSSCHLAG, 0.5)

    def test_viel_evidenz_verdraengt_das_fachwissen(self):
        w, fach = self.anteile(1000)
        self.assertGreater(w, 0.85)
        self.assertLess(fach, 0.06)

    def test_kein_harter_mindestwert(self):
        """Zwischen 19 und 20 Partien darf es keine Kante geben."""
        a = self.anteile(19)[0]
        b = self.anteile(20)[0]
        self.assertLess(abs(a - b), 0.01)

    def test_messung_schlaegt_fachwissen_bei_grosser_stichprobe(self):
        raum = DraftEngine(self.context(),
                           provider=gemessen_mit_prior_provider()).raum.laden()
        kandidaten = list(raum.brawler)
        alle = objective.fuer_pool(kandidaten, raum, self.karte().anforderungs_vektor())
        mit_messung = [a for a in alle.values() if a.mess_anteil >= 0.5]
        ohne = [a for a in alle.values() if a.verfuegbar and a.mess_anteil == 0]
        if mit_messung and ohne:
            self.assertGreater(max(abs(a.wert) for a in mit_messung),
                               max(abs(a.wert) for a in ohne),
                               "gemessene Aussagen muessen weiter ausschlagen koennen")
