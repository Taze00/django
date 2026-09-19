# -*- coding: utf-8 -*-
"""Datenraum: alle Statistiken eines Drafts, einmal geladen.

Drei Aufgaben:

1. **Entkopplung.** Der Datenraum fragt einen StatProvider und haelt nur
   noch `StatRecord`s. Ob die Zahlen aus Demo-Seeds, aus Fixtures oder
   spaeter aus der API aggregiert wurden, sieht die Engine nur am Feld
   `source` - an keiner Tabelle, keinem Modell, keiner Abfrage.

2. **Geschwindigkeit.** Eine Empfehlung bewertet rund zwanzig Kandidaten
   gegen bis zu drei Gegner und drei Mitspieler. Der Datenraum holt alles
   Noetige einmal und beantwortet danach jede Frage aus dem Speicher.

3. **Kontext-Spezifitaet.** Zu einem Paar kann es viele Zeilen geben -
   je Map, Modus, Rangbereich und Zeitfenster. Die passendste gewinnt,
   und diese Auswahl steht genau hier, fuer alle Provider gleich.
"""

from django.db.models import Q

from drafter import config
from drafter.models import Brawler
from drafter.services import staerke as staerke_modul
from drafter.services.providers.records import StatAnfrage


def _spezifitaet(zeile, brawl_map, game_mode, rank_pool):
    """Wie gut passt eine Statistikzeile auf den aktuellen Draft?

    Hoeher ist besser. Eine Zeile fuer eine *andere* Map oder einen
    *anderen* Modus ist nicht schwach passend, sondern falsch - sie
    bekommt -1 und wird verworfen.

    Rangfolge der Kriterien, jede Stufe schlaegt alle folgenden:
      Map (4) > Modus (2) > Rangbereich (0.5) > Zeitfenster (<= 0.3) > Stichprobe (<= 0.1)
    """
    punkte = 0.0

    if zeile.brawl_map_id:
        if not brawl_map or zeile.brawl_map_id != brawl_map.id:
            return -1.0
        punkte += 4.0
    if zeile.game_mode_id:
        if not game_mode or zeile.game_mode_id != game_mode.id:
            return -1.0
        punkte += 2.0
    if zeile.rank_pool and rank_pool and zeile.rank_pool == rank_pool:
        punkte += 0.5

    # Aktuelle Meta vor langer Historie. Unbekannte Fenster bekommen
    # nichts - sie sind nicht falsch, aber auch nicht bevorzugt.
    vorrang = config.STAT_FENSTER_VORRANG
    if zeile.window_label in vorrang:
        punkte += 0.3 * (len(vorrang) - vorrang.index(zeile.window_label)) / len(vorrang)

    # Mehr Spiele entscheiden bei sonst gleicher Passung.
    punkte += min(0.1, zeile.games / 1_000_000)
    return punkte


def _ebene(zeile):
    """Auf welcher Ebene beschreibt diese Zeile den Brawler?"""
    if zeile.brawl_map_id:
        return staerke_modul.MAP
    if zeile.game_mode_id:
        return staerke_modul.MODUS
    return staerke_modul.GLOBAL


class Datenraum:
    """Vorgeladene Statistiken fuer genau einen Draft-Kontext."""

    def __init__(self, brawl_map=None, game_mode=None, patch=None, rank_pool=None, provider=None):
        self.brawl_map = brawl_map
        self.game_mode = game_mode or (brawl_map.game_mode if brawl_map else None)
        self.patch = patch
        self.rank_pool = rank_pool
        self.provider = provider

        self.brawler = []
        self._nach_id = {}
        self._counter = {}    # (brawler_id, gegner_id)   -> StatRecord
        self._synergie = {}   # (kleinere_id, groessere_id) -> StatRecord
        self._stat = {}       # brawler_id                -> StatRecord
        self._build = {}      # (brawler_id, art, slug)   -> StatRecord
        # Groesste GEMESSENE Stichprobe je Brawler ueber alle Zeilen, die
        # auf diesen Draft anwendbar sind (Map, Modus, gesamt) - Grundlage
        # der Datenstufe. Bewusst nicht nur die Zeile, die `stat()` liefert:
        # die spezifischste Zeile (Map mit 3 Spielen) sagt nichts darueber,
        # ob es fuer den Brawler insgesamt genug Messungen gibt.
        self._spiele = {}     # brawler_id                -> int
        # Gemessene Zeilen GETRENNT nach Ebene: global / modus / map.
        # Frueher gewann die spezifischste Zeile allein - eine Map-Zeile
        # mit 4 Partien verdraengte damit eine globale mit 400. Die
        # Schaetzung in services/staerke.py setzt die Ebenen stattdessen
        # aufeinander (grob ist Prior fuer fein) und braucht sie deshalb
        # alle drei.
        self._ebenen = {}     # brawler_id -> {"global"|"modus"|"map": StatRecord}
        # Modus-Zeilen ueber ALLE Modi - nur fuer die Flexibilitaet, die
        # gerade den Vergleich zwischen Modi braucht. Lazy, siehe unten.
        self._modus_zeilen = None
        # Gepflegte Werte (demo/manual) GETRENNT von den gemessenen. Sie
        # sind der Prior je Komponente - siehe `quellen.py`. Leer, wenn der
        # Provider keine getrennte Prior-Quelle mitbringt.
        self._stat_prior = {}
        self._counter_prior = {}
        self._synergie_prior = {}
        self._build_prior = {}
        self._geladen = False

    # --- Laden ----------------------------------------------------------
    def laden(self):
        if self._geladen:
            return self

        if self.provider is None:
            # Spaet importiert: die Registry kennt alle Provider, der
            # Datenraum soll keinen davon kennen muessen.
            from drafter.services.providers.registry import hole_stat_provider
            self.provider = hole_stat_provider()

        # Der Brawler-Katalog ist keine Statistik, sondern gepflegte
        # Domaene (Attribute, Rollen) - er kommt deshalb weiter direkt aus
        # der Datenbank. Balanceaenderungen gleich mitladen: die
        # Patchgewichtung fragt sie fuer jeden Kandidaten ab.
        #
        # Der volle Katalog: aktive Brawler UND alle, die die offizielle
        # API kennt. Letztere haben meist kein Profil; ob und wie sie
        # bewertet werden, entscheidet `stufe()` - nicht der Ausschluss
        # aus dem Pool. Frueher standen hier nur aktive, und alles andere
        # war fuer die Engine unsichtbar, auch mit Messdaten.
        # `ranked_verfuegbar=False` heisst: im Ranked-Modus nicht waehlbar.
        # Solche Brawler sind weder Kandidat noch Datenluecke - sie fehlen
        # nicht, sie gehoeren nicht hierher. Im Katalog bleiben sie.
        self.brawler = list(
            Brawler.objects.filter(Q(is_active=True) | Q(external_id__isnull=False))
            .filter(ranked_verfuegbar=True)
            .prefetch_related("balance_changes__patch")
        )
        self._nach_id = {b.id: b for b in self.brawler}
        ids = frozenset(self._nach_id)

        anfrage = StatAnfrage(
            brawler_ids=ids,
            game_mode_id=self.game_mode.id if self.game_mode else None,
            brawl_map_id=self.brawl_map.id if self.brawl_map else None,
            rank_pool=self.rank_pool or "",
        )
        # Mischt der Provider Messung und Prior (OverlayStatProvider), werden
        # beide Seiten einzeln geladen: welche Quelle je Komponente gilt,
        # entscheidet die Komponente, nicht eine Zeilenauswahl vorab.
        messung = getattr(self.provider, "gemessen", self.provider)
        prior = getattr(self.provider, "prior", None)
        if prior is not None:
            self._stat_prior = self._bestes_je_schluessel(
                prior.brawler_stats(anfrage), lambda r: r.brawler_id, ids)
            self._counter_prior = self._bestes_je_schluessel(
                prior.counter_stats(anfrage), lambda r: (r.brawler_id, r.partner_id), ids)
            self._synergie_prior = self._bestes_je_schluessel(
                prior.synergy_stats(anfrage),
                lambda r: tuple(sorted((r.brawler_id, r.partner_id))), ids)
            self._build_prior = self._bestes_je_schluessel(
                prior.build_stats(anfrage),
                lambda r: (r.brawler_id, r.item_kind, r.item_slug), ids)

        brawler_zeilen = messung.brawler_stats(anfrage)
        self._stat = self._bestes_je_schluessel(
            brawler_zeilen, lambda r: r.brawler_id, ids,
        )
        ebenen_rang = {}
        for zeile in brawler_zeilen:
            if zeile.brawler_id not in ids or not zeile.ist_gemessen:
                continue
            punkte = _spezifitaet(zeile, self.brawl_map, self.game_mode, self.rank_pool)
            if punkte < 0:
                continue
            self._spiele[zeile.brawler_id] = max(
                self._spiele.get(zeile.brawler_id, 0), zeile.games or 0
            )
            ebene = _ebene(zeile)
            schluessel = (zeile.brawler_id, ebene)
            rang = (punkte, zeile.games or 0)
            if rang > ebenen_rang.get(schluessel, (-1, -1)):
                ebenen_rang[schluessel] = rang
                self._ebenen.setdefault(zeile.brawler_id, {})[ebene] = zeile
        self._counter = self._bestes_je_schluessel(
            messung.counter_stats(anfrage), lambda r: (r.brawler_id, r.partner_id), ids,
        )
        self._synergie = self._bestes_je_schluessel(
            messung.synergy_stats(anfrage),
            lambda r: tuple(sorted((r.brawler_id, r.partner_id))), ids,
        )
        self._build = self._bestes_je_schluessel(
            messung.build_stats(anfrage),
            lambda r: (r.brawler_id, r.item_kind, r.item_slug), ids,
        )
        self._geladen = True
        return self

    def _bestes_je_schluessel(self, records, schluessel, ids):
        """Je Schluessel die passendste Zeile behalten.

        Datensaetze zu Brawlern ausserhalb des aktiven Katalogs werden
        verworfen - ein Provider muss nicht wissen, wer gerade aktiv ist.
        """
        gewaehlt = {}
        bewertung = {}
        for record in records:
            if record.brawler_id not in ids:
                continue
            if record.partner_id is not None and record.partner_id not in ids:
                continue
            punkte = _spezifitaet(record, self.brawl_map, self.game_mode, self.rank_pool)
            if punkte < 0:
                continue
            k = schluessel(record)
            rang = (1 if record.ist_gemessen else 0, punkte)
            if rang > bewertung.get(k, (-1, -1)):
                gewaehlt[k] = record
                bewertung[k] = rang
        return gewaehlt

    # --- Abfragen -------------------------------------------------------
    # --- Prior (gepflegte Werte) ---------------------------------------
    def stat_prior(self, brawler):
        return self._stat_prior.get(brawler.id)

    def counter_prior(self, brawler, gegner):
        return self._counter_prior.get((brawler.id, gegner.id))

    def synergie_prior(self, a, b):
        schluessel = (a.id, b.id) if a.id < b.id else (b.id, a.id)
        return self._synergie_prior.get(schluessel)

    def staerke(self, brawler):
        """CURRENT STRENGTH: geschaetzte Siegquote samt Unsicherheit.

        Die Ebenen global/Modus/Map gehen als Kette in die Schaetzung
        (services/staerke.py), der gepflegte Wert ist ihr Prior. Ohne
        jede Messung bleibt der gepflegte Wert allein (Profile), ohne
        beides ist die Auskunft unbekannt - nicht 50 %.
        """
        zeilen = dict(self._ebenen.get(brawler.id, {}))
        prior = self.stat_prior(brawler)
        if prior is None:
            # Ohne getrennte Prior-Quelle (reiner Demo-Provider) steht der
            # gepflegte Wert im Messplatz - dann ist ER der Prior.
            kandidat = self._stat.get(brawler.id)
            if kandidat is not None and not kandidat.ist_gemessen:
                prior = kandidat
        profil_rate = prior.adjusted_rate if prior is not None else None
        return staerke_modul.schaetze(
            zeilen, profil_rate=profil_rate, pickrate=self.pickrate(brawler),
            profil_record=prior, kontext_ebene=self.kontext_ebene,
        )

    @property
    def kontext_ebene(self):
        """Auf welcher Ebene wird gefragt - Map, Modus oder global?"""
        if self.brawl_map is not None:
            return staerke_modul.MAP
        if self.game_mode is not None:
            return staerke_modul.MODUS
        return staerke_modul.GLOBAL

    def pickrate(self, brawler):
        """Anteil der Partien, in denen er gewaehlt wurde - feinste Ebene zuerst.

        Nur aus Messungen: eine gepflegte Pickrate gibt es nicht.
        """
        zeilen = self._ebenen.get(brawler.id, {})
        for ebene in (staerke_modul.MAP, staerke_modul.MODUS, staerke_modul.GLOBAL):
            zeile = zeilen.get(ebene)
            if zeile is not None and (zeile.pick_rate or 0) > 0:
                return zeile.pick_rate
        return None

    def counter(self, brawler, gegner):
        """Vorteil von `brawler` gegen `gegner` laut Statistik, sonst None.

        None heisst ausdruecklich "keine Auskunft" und nicht "kein
        Vorteil" - die Counter-Komponente faellt dann auf ihre
        Heuristik zurueck und kennzeichnet das auch so.
        """
        return self._counter.get((brawler.id, gegner.id))

    def synergie(self, a, b):
        schluessel = (a.id, b.id) if a.id < b.id else (b.id, a.id)
        return self._synergie.get(schluessel)

    def stat(self, brawler):
        return self._stat.get(brawler.id)

    def build_stat(self, brawler, art, slug):
        # Builds: Messung, sonst gepflegt. Eine Mischung lohnt hier nicht -
        # sie verschieben nur die Regelwahl (BUILD_STAT_EINFLUSS).
        messung = self._build.get((brawler.id, art, slug))
        if messung is not None and (messung.games or 0) > 0:
            return messung
        return self._build_prior.get((brawler.id, art, slug)) or messung

    def ebenen(self, brawler):
        """Die gemessenen Zeilen je Ebene: {"global"|"modus"|"map": Zeile}.

        Fuer alles, was die Ebenen einzeln braucht - etwa die Modus-Eignung
        in services/objective.py, die Modus gegen global stellt.
        """
        return dict(self._ebenen.get(brawler.id, {}))

    def modus_zeilen(self, brawler):
        """Gemessene Zeilen je MODUS - ueber alle Modi, nicht nur diesen.

        Der Datenraum filtert sonst auf den aktuellen Kontext; fuer die
        Frage "laeuft er ueberall aehnlich" braucht es aber gerade den
        Vergleich zwischen den Modi. Deshalb eine eigene Abfrage, einmal
        je Draft gecacht.
        """
        if self._modus_zeilen is None:
            self._modus_zeilen = {}
            anfrage = StatAnfrage(brawler_ids=frozenset(self._nach_id))
            # Ueber den Provider, nicht an ihm vorbei: die Engine fragt
            # Statistiken ausschliesslich ueber das Protokoll ab. Ein
            # Provider ohne Modusvergleich liefert eine leere Liste, und
            # die Flexibilitaet faellt dann eben aus.
            quelle = getattr(self.provider, "gemessen", self.provider)
            zeilen = quelle.modus_stats(anfrage)
            # JE MODUS nur eine Zeile - die mit den meisten Partien. Zu
            # jedem Modus gibt es mehrere Zeitfenster (7d, 30d, 90d,
            # seit_patch); alle mitzuzaehlen machte aus sechs Modi
            # vierundzwanzig und zaehlte dieselben Partien mehrfach.
            beste = {}
            for zeile in zeilen:
                schluessel = (zeile.brawler_id, zeile.game_mode_id)
                vorhanden = beste.get(schluessel)
                if vorhanden is None or (zeile.games or 0) > (vorhanden.games or 0):
                    beste[schluessel] = zeile
            for (brawler_id, _), zeile in beste.items():
                self._modus_zeilen.setdefault(brawler_id, []).append(zeile)
        return self._modus_zeilen.get(brawler.id, [])

    def gemessene_spiele(self, brawler):
        return self._spiele.get(brawler.id, 0)

    def stufe(self, brawler):
        """profil | gemessen | fachwissen | katalog - siehe config.

        Keine Mindestzahl von Partien: EINE gemessene Partie ist eine
        Beobachtung, keine zwanzig. Wie wenig sie wiegt, entscheiden
        Posterior und Confidence, nicht ein Tuersteher. Ohne jede
        Beobachtung entscheidet, ob wenigstens die Rolle bekannt ist.
        """
        if brawler.hat_profil:
            return "profil"
        if self.gemessene_spiele(brawler) > 0:
            return "gemessen"
        from drafter.services.rollenwissen import hat_fachwissen
        if hat_fachwissen(brawler):
            return "fachwissen"
        return "katalog"

    def bewertbar(self, brawler):
        return self.stufe(brawler) != "katalog"

    def hat_statistik(self):
        return bool(self._stat or self._counter)

    @property
    def quelle(self):
        """Name des Providers - fuer die Datenlage in der Oberflaeche."""
        return self.provider.name if self.provider is not None else None

    @property
    def nur_demo(self):
        """Beruht alles auf nicht gemessenen Werten?

        Ohne jede Statistik: ja. Das ist die ehrliche Antwort - dann
        rechnet die Engine ausschliesslich mit Heuristiken.
        """
        alle = (
            list(self._stat.values()) + list(self._counter.values())
            + list(self._synergie.values()) + list(self._build.values())
            + list(self._stat_prior.values()) + list(self._counter_prior.values())
            + list(self._synergie_prior.values())
        )
        return all(r.is_demo for r in alle) if alle else True

    def verfuegbare(self, gesperrte_ids):
        return [b for b in self.brawler if b.id not in gesperrte_ids]
