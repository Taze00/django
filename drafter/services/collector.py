# -*- coding: utf-8 -*-
"""Kontrollierter Collector fuer High-Level-Partien der offiziellen API.

Ein Lauf, vier Schritte - jeder begrenzt:

    1. Katalog     /brawlers                  -> IDs eintragen, neue Brawler inaktiv anlegen
    2. Saat        /rankings/global/players   -> bis zu 200 Spieler, Tiefe 0
    3. Battlelogs  /players/{tag}/battlelog   -> hoechstens `max_spieler` Abrufe
    4. Entdecken   Mitspieler aus soloRanked  -> Tiefe + 1, nur bis `max_tiefe`

**Keine unkontrollierte Rekursion.** Drei Bremsen zugleich: das Budget
(`max_spieler` Battlelogs je Lauf), die Tiefe (jenseits von `max_tiefe`
werden Spieler nicht einmal gespeichert) und der Abrufabstand (derselbe
Spieler fruehestens nach `COLLECTOR_ABRUF_ABSTAND_STUNDEN` erneut).

**Warum die Trophaeen-Rangliste als Saat?** Eine Ranked-Rangliste nach Elo
gibt es in der API nicht (geprueft am 2026-09-15: /rankings/global/players,
/rankings/global/brawlers/{id} und /rankings/global/clubs antworten, alle
nach Trophaeen). Die Top 200 sind aktive Spieler auf hohem Niveau; ob und
wie viel Ranked sie spielen, zeigt erst ihr Battlelog. Entdeckt wird
deshalb nur aus soloRanked-Partien - dort sitzen Ranked-Spieler auf
aehnlichem Rang.

**Fehler:**

    401/403   Lauf abbrechen - Key oder IP-Freigabe betreffen jede Anfrage
    429       nach den Wiederholungen des Clients: Lauf abbrechen, Spieler bleibt offen
    404       Spieler markieren, Pause, weiter zum naechsten
    5xx/Netz  nach den Wiederholungen: Spieler mit wachsender Pause markieren,
              weiter; nach COLLECTOR_ABBRUCH_NACH_FEHLERN in Folge Lauf beenden

Aggregiert wird hier nichts. Der Collector speichert Rohantworten und
importiert Partien - was daraus folgt, rechnet die Aggregation.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import timedelta

from django.db.models import F, Q
from django.utils import timezone

from drafter import config
from drafter.models import Brawler, Datenquelle
from drafter.models.collector import CollectorRun, TrackedPlayer
from drafter.models.matches import RawPayload
from drafter.services.brawl_api_client import (
    PFAD_BRAWLER, ApiFehler, BrawlApiClient, KeinKeyFehler, NetzwerkFehler, NichtGefundenFehler,
    RatenlimitFehler, ServerFehler, UngueltigerKeyFehler, ZugriffVerweigertFehler,
    pfad_battlelog, pfad_rangliste_spieler, tag_bereinigen,
)
from drafter.services.ingest.importer import MatchImporter, inhalts_hash
from drafter.services.ingest.parser import (
    FORMAT_OFFIZIELLE_BRAWLER, FORMAT_OFFIZIELLE_RANGLISTE, FORMAT_OFFIZIELLER_BATTLELOG,
    ParserFehler, parse_offizieller_battlelog,
)
from drafter.services.katalog import brawler_abgleichen
from drafter.services.providers.basis import MatchProvider
from drafter.services.providers.official_api import (
    dateiname, speichere_mitschnitt, verpacke_mitschnitt,
)
from drafter.services.providers.records import Lieferung


class LaufAbgebrochen(Exception):
    """Der Lauf endet vorzeitig - mit Grund, ohne Ausnahme nach aussen."""


class _EineLieferung(MatchProvider):
    """Ein einzelner Battlelog als MatchProvider - der Importer bleibt unveraendert."""

    name = "collector"

    def __init__(self, lieferung):
        self._lieferung = lieferung

    def lieferungen(self):
        yield self._lieferung


@dataclass
class SammelBericht:
    abbruch: str = ""
    katalog: list = field(default_factory=list)
    rangliste_gesehen: int = 0
    rangliste_neu: int = 0
    spieler_abgefragt: int = 0
    battlelogs_ok: int = 0
    battlelog_eintraege: int = 0
    fehler: Counter = field(default_factory=Counter)
    spieler_entdeckt: int = 0
    partien_gelesen: int = 0
    neu: int = 0
    duplikate: int = 0
    konflikte: int = 0
    uebersprungen: int = 0
    ungueltig: int = 0
    neu_nach_typ: Counter = field(default_factory=Counter)
    duplikate_nach_typ: Counter = field(default_factory=Counter)
    katalog_neu: list = field(default_factory=list)
    katalog_verknuepft: list = field(default_factory=list)
    id_widersprueche: list = field(default_factory=list)
    unbekannte_brawler: set = field(default_factory=set)
    api: dict = field(default_factory=dict)

    def uebernehmen(self, imp):
        """Zahlen eines Importberichts aufaddieren."""
        self.partien_gelesen += imp.matches_gelesen
        self.neu += imp.neu
        self.duplikate += imp.duplikate
        self.konflikte += imp.konflikte
        self.uebersprungen += imp.uebersprungen
        self.ungueltig += imp.ungueltig
        self.neu_nach_typ.update(imp.neu_nach_typ)
        self.duplikate_nach_typ.update(imp.duplikate_nach_typ)
        self.katalog_neu += imp.katalog_neu
        self.katalog_verknuepft += imp.katalog_verknuepft
        self.id_widersprueche += imp.id_widersprueche
        self.unbekannte_brawler |= imp.unbekannte_brawler
        if imp.fehlerhaft:
            self.fehler["import"] += imp.fehlerhaft

    def als_dict(self):
        return {
            "abbruch": self.abbruch,
            "katalog": self.katalog,
            "rangliste_gesehen": self.rangliste_gesehen,
            "rangliste_neu": self.rangliste_neu,
            "spieler_abgefragt": self.spieler_abgefragt,
            "battlelogs_ok": self.battlelogs_ok,
            "battlelog_eintraege": self.battlelog_eintraege,
            "fehler": dict(self.fehler),
            "spieler_entdeckt": self.spieler_entdeckt,
            "partien_gelesen": self.partien_gelesen,
            "neu": self.neu,
            "duplikate": self.duplikate,
            "konflikte": self.konflikte,
            "uebersprungen": self.uebersprungen,
            "ungueltig": self.ungueltig,
            "neu_nach_typ": dict(self.neu_nach_typ),
            "duplikate_nach_typ": dict(self.duplikate_nach_typ),
            "katalog_neu": self.katalog_neu,
            "katalog_verknuepft": self.katalog_verknuepft,
            "id_widersprueche": self.id_widersprueche,
            "unbekannte_brawler": sorted(self.unbekannte_brawler),
            "api": self.api,
        }

    def zeilen(self):
        typ = lambda zaehler: ", ".join(f"{t} {n}" for t, n in sorted(zaehler.items())) or "–"
        zeilen = [
            f"Lauf:                 {'abgebrochen' if self.abbruch else 'beendet'}",
        ]
        if self.abbruch:
            zeilen.append(f"  Grund:              {self.abbruch}")
        zeilen += self.katalog
        zeilen += [
            f"Rangliste:            {self.rangliste_gesehen} Spieler gesehen, "
            f"{self.rangliste_neu} neu aufgenommen",
            f"Spieler abgefragt:    {self.spieler_abgefragt} "
            f"(Battlelogs gelesen {self.battlelogs_ok}, Einträge {self.battlelog_eintraege})",
            f"API-Fehler:           {typ(self.fehler)}",
            f"Spieler entdeckt:     {self.spieler_entdeckt} (nur aus soloRanked)",
            f"Partien gelesen:      {self.partien_gelesen} "
            f"(übersprungen {self.uebersprungen}, ungültig {self.ungueltig})",
            f"  neu:                {self.neu} ({typ(self.neu_nach_typ)})",
            f"  Dubletten entfernt: {self.duplikate} ({typ(self.duplikate_nach_typ)})",
            f"  Konflikte:          {self.konflikte}",
        ]
        if self.katalog_neu:
            zeilen.append(f"Katalog neu (inaktiv): {', '.join(self.katalog_neu)}")
        if self.katalog_verknuepft:
            zeilen.append(f"Katalog verknüpft:    {', '.join(self.katalog_verknuepft)}")
        zeilen.append(f"ID-Widersprüche:      {len(self.id_widersprueche)}")
        zeilen += [f"  ! {w}" for w in self.id_widersprueche[:10]]
        if self.unbekannte_brawler:
            zeilen.append(f"Unbekannte Brawler:   {', '.join(sorted(self.unbekannte_brawler))}")
        api = self.api or {}
        zeilen.append(
            f"API:                  {api.get('anfragen', 0)} Anfragen, Status {api.get('status', {})}, "
            f"{api.get('wiederholungen', 0)} Wiederholungen, "
            f"{api.get('wartezeit_sekunden', 0)} s gewartet"
        )
        zeilen.append(
            f"Rate-Limit-Header:    {', '.join(api.get('ratenlimit_header') or []) or 'keine'}"
            f" | Retry-After: {api.get('retry_after') or 'keins'}"
        )
        return zeilen


class Collector:
    def __init__(self, client=None, max_spieler=None, max_tiefe=None, abruf_abstand=None,
                 rangliste=True, katalog=True, spieler_tags=(), datei_verzeichnis=None,
                 jetzt=None):
        self.client = client if client is not None else BrawlApiClient()
        self.max_spieler = int(
            config.COLLECTOR_MAX_SPIELER if max_spieler is None else max_spieler
        )
        if self.max_spieler < 0:
            raise ValueError("max_spieler darf nicht negativ sein")
        tiefe = int(config.COLLECTOR_MAX_TIEFE if max_tiefe is None else max_tiefe)
        if not 0 <= tiefe <= config.COLLECTOR_TIEFE_OBERGRENZE:
            raise ValueError(
                f"max_tiefe muss zwischen 0 und {config.COLLECTOR_TIEFE_OBERGRENZE} liegen"
            )
        self.max_tiefe = tiefe
        self.abruf_abstand = (
            timedelta(hours=config.COLLECTOR_ABRUF_ABSTAND_STUNDEN)
            if abruf_abstand is None else abruf_abstand
        )
        self.rangliste = rangliste
        self.katalog = katalog
        self.spieler_tags = [tag_bereinigen(t) for t in spieler_tags]
        self.datei_verzeichnis = datei_verzeichnis
        self._jetzt = jetzt or timezone.now
        self._katalog_nachgeladen = False

    # --- Ablauf ---------------------------------------------------------
    def ausfuehren(self):
        if not self.client.einsatzbereit:
            raise KeinKeyFehler(
                "BRAWL_STARS_API_KEY ist nicht gesetzt - es wurde nichts abgerufen."
            )
        lauf = CollectorRun.objects.create(parameters=self._parameter())
        bericht = SammelBericht()
        try:
            if self.katalog:
                self._katalog(bericht)
            self._manuelle_saat()
            if self.rangliste:
                self._rangliste(bericht)
            self._battlelogs(bericht)
        except LaufAbgebrochen as grund:
            bericht.abbruch = str(grund)
        except (UngueltigerKeyFehler, ZugriffVerweigertFehler, RatenlimitFehler) as fehler:
            bericht.fehler[str(fehler.status)] += 1
            bericht.abbruch = str(fehler)
        finally:
            bericht.api = self.client.statistik.als_dict()
            lauf.finished_at = timezone.now()
            lauf.status = CollectorRun.Status.ABORTED if bericht.abbruch \
                else CollectorRun.Status.FINISHED
            lauf.abort_reason = bericht.abbruch[:500]
            lauf.report = bericht.als_dict()
            lauf.save()
        return bericht

    def _parameter(self):
        return {
            "max_spieler": self.max_spieler,
            "max_tiefe": self.max_tiefe,
            "abruf_abstand_stunden": round(self.abruf_abstand.total_seconds() / 3600, 2),
            "rangliste": self.rangliste,
            "katalog": self.katalog,
            "spieler_tags": self.spieler_tags,
            "dateien": bool(self.datei_verzeichnis),
        }

    # --- Rohantworten ---------------------------------------------------
    def _roh_speichern(self, antwort, referenz, format_name, art):
        """Antwort unveraendert ablegen - als RawPayload, auf Wunsch auch als Datei."""
        huelle = verpacke_mitschnitt(antwort, referenz, format_name)
        if self.datei_verzeichnis is not None:
            speichere_mitschnitt(
                huelle, self.datei_verzeichnis,
                dateiname(art, referenz, antwort.abgerufen_am),
            )
        RawPayload.objects.get_or_create(
            content_hash=inhalts_hash(huelle),
            defaults=dict(
                source=Datenquelle.API, format=format_name[:60], reference=str(referenz)[:300],
                payload=huelle, fetched_at=antwort.abgerufen_am,
                parse_status=RawPayload.ParseStatus.UNSUPPORTED,
                parse_message="Gespeichert, nicht ausgewertet - enthält keine Partien.",
            ),
        )
        return huelle

    # --- Schritt 1: Katalog ---------------------------------------------
    def _katalog(self, bericht):
        try:
            antwort = self.client.abrufen(PFAD_BRAWLER)
        except (ServerFehler, NetzwerkFehler) as fehler:
            if Brawler.objects.exclude(external_id=None).exists():
                bericht.katalog.append(
                    f"/brawlers nicht abrufbar ({fehler.status or 'Netz'}) - "
                    f"es gelten die bereits eingetragenen IDs"
                )
                return
            raise LaufAbgebrochen(
                f"/brawlers nicht abrufbar und noch keine Brawler-IDs im Katalog: {fehler}"
            ) from None
        self._roh_speichern(antwort, "alle", FORMAT_OFFIZIELLE_BRAWLER, "brawlers")
        items = antwort.daten.get("items") if isinstance(antwort.daten, dict) else None
        if not isinstance(items, list):
            raise LaufAbgebrochen("/brawlers enthält keine Liste 'items'")
        bericht.katalog += brawler_abgleichen(items).zeilen()

    # --- Schritt 2: Saat ------------------------------------------------
    def _manuelle_saat(self):
        for tag in self.spieler_tags:
            spieler, neu = TrackedPlayer.objects.get_or_create(
                tag=tag, defaults={"origin": TrackedPlayer.Origin.MANUAL, "depth": 0},
            )
            if not neu and spieler.depth != 0:
                spieler.depth = 0
                spieler.save(update_fields=["depth", "updated_at"])

    def _rangliste(self, bericht):
        try:
            antwort = self.client.abrufen(pfad_rangliste_spieler("global"))
        except (ServerFehler, NetzwerkFehler) as fehler:
            bericht.katalog.append(
                f"Rangliste nicht abrufbar ({fehler.status or 'Netz'}) - "
                f"es wird mit den bereits bekannten Spielern weitergearbeitet"
            )
            return
        self._roh_speichern(antwort, "global", FORMAT_OFFIZIELLE_RANGLISTE, "rankings-players")
        items = antwort.daten.get("items") if isinstance(antwort.daten, dict) else None
        if not isinstance(items, list):
            bericht.katalog.append("Rangliste enthält keine Liste 'items' - übersprungen")
            return

        # Alte Platzierungen zuruecksetzen: wer aus den Top 200 gefallen ist,
        # soll nicht mit seinem alten Platz vorne einsortiert bleiben.
        TrackedPlayer.objects.filter(origin=TrackedPlayer.Origin.RANKING).update(
            ranking_position=None
        )
        for eintrag in items:
            if not isinstance(eintrag, dict):
                continue
            try:
                tag = tag_bereinigen(eintrag.get("tag"))
            except ApiFehler:
                continue
            platz = eintrag.get("rank") if isinstance(eintrag.get("rank"), int) else None
            trophaeen = (eintrag.get("trophies")
                         if isinstance(eintrag.get("trophies"), int) else None)
            spieler, neu = TrackedPlayer.objects.get_or_create(
                tag=tag,
                defaults={
                    "origin": TrackedPlayer.Origin.RANKING, "depth": 0,
                    "ranking_position": platz, "ranking_trophies": trophaeen,
                },
            )
            if not neu:
                spieler.origin = TrackedPlayer.Origin.RANKING
                spieler.depth = 0
                spieler.ranking_position = platz
                spieler.ranking_trophies = trophaeen
                spieler.save(update_fields=[
                    "origin", "depth", "ranking_position", "ranking_trophies", "updated_at",
                ])
            bericht.rangliste_gesehen += 1
            bericht.rangliste_neu += int(neu)

    # --- Schritt 3: Battlelogs ------------------------------------------
    def _naechster(self, schon_abgefragt):
        jetzt = self._jetzt()
        grenze = jetzt - self.abruf_abstand
        return (
            TrackedPlayer.objects
            .filter(is_active=True, depth__lte=self.max_tiefe)
            .exclude(tag__in=schon_abgefragt)
            .filter(Q(last_fetched_at__isnull=True) | Q(last_fetched_at__lt=grenze))
            .filter(Q(next_fetch_after__isnull=True) | Q(next_fetch_after__lte=jetzt))
            .order_by("depth", F("ranking_position").asc(nulls_last=True), "created_at", "tag")
            .first()
        )

    def _battlelogs(self, bericht):
        abgefragt = set()
        fehler_in_folge = 0
        while bericht.spieler_abgefragt < self.max_spieler:
            spieler = self._naechster(abgefragt)
            if spieler is None:
                break
            abgefragt.add(spieler.tag)
            bericht.spieler_abgefragt += 1
            try:
                antwort = self.client.abrufen(pfad_battlelog(spieler.tag))
            except NichtGefundenFehler as fehler:
                bericht.fehler["404"] += 1
                self._markieren(spieler, "404", fehler,
                                timedelta(days=config.COLLECTOR_404_PAUSE_TAGE), gesehen=True)
                fehler_in_folge = 0    # betrifft nur diesen Tag, nicht die API
                continue
            except RatenlimitFehler as fehler:
                bericht.fehler["429"] += 1
                raise LaufAbgebrochen(
                    f"Ratenlimit auch nach {self.client.versuche} Versuchen - Lauf beendet, "
                    f"{spieler.tag} bleibt offen: {fehler}"
                ) from None
            except (UngueltigerKeyFehler, ZugriffVerweigertFehler) as fehler:
                bericht.fehler[str(fehler.status)] += 1
                raise LaufAbgebrochen(str(fehler)) from None
            except (ServerFehler, NetzwerkFehler) as fehler:
                schluessel = str(fehler.status) if fehler.status else "netzwerk"
                bericht.fehler[schluessel] += 1
                spieler.error_streak += 1
                stunden = min(2 ** (spieler.error_streak - 1),
                              config.COLLECTOR_FEHLER_PAUSE_STUNDEN_MAX)
                self._markieren(spieler, schluessel, fehler, timedelta(hours=stunden))
                fehler_in_folge += 1
                if fehler_in_folge >= config.COLLECTOR_ABBRUCH_NACH_FEHLERN:
                    raise LaufAbgebrochen(
                        f"{fehler_in_folge} Abrufe in Folge fehlgeschlagen - zuletzt: {fehler}"
                    ) from None
                continue
            except ApiFehler as fehler:
                bericht.fehler[str(fehler.status or "api")] += 1
                self._markieren(spieler, str(fehler.status or "api"), fehler,
                                timedelta(hours=config.COLLECTOR_FEHLER_PAUSE_STUNDEN_MAX))
                continue

            fehler_in_folge = 0
            self._battlelog_verarbeiten(spieler, antwort, bericht)

    def _markieren(self, spieler, status, fehler, pause, gesehen=False):
        jetzt = self._jetzt()
        spieler.last_status = status[:20]
        spieler.last_error = str(fehler)[:300]
        spieler.next_fetch_after = jetzt + pause
        felder = ["last_status", "last_error", "next_fetch_after", "error_streak", "updated_at"]
        if gesehen:
            spieler.last_fetched_at = jetzt
            felder.append("last_fetched_at")
        spieler.save(update_fields=felder)

    def _battlelog_verarbeiten(self, spieler, antwort, bericht):
        huelle = verpacke_mitschnitt(antwort, spieler.tag, FORMAT_OFFIZIELLER_BATTLELOG)
        if self.datei_verzeichnis is not None:
            speichere_mitschnitt(
                huelle, self.datei_verzeichnis,
                dateiname("battlelog", spieler.tag, antwort.abgerufen_am),
            )
        try:
            ergebnis = parse_offizieller_battlelog(huelle)
        except ParserFehler as fehler:
            # Die Antwort wird trotzdem gespeichert: ein spaeter korrigierter
            # Parser soll sie ohne neuen Abruf lesen koennen.
            bericht.uebernehmen(MatchImporter(_EineLieferung(Lieferung(
                referenz=spieler.tag, format=FORMAT_OFFIZIELLER_BATTLELOG, rohdaten=huelle,
                source=Datenquelle.API, matches=None, status="fehler", meldung=str(fehler),
            ))).ausfuehren())
            bericht.fehler["parser"] += 1
            self._markieren(spieler, "parser", fehler, timedelta(hours=1), gesehen=True)
            return

        self._unbekannte_brawler_nachladen(ergebnis, bericht)
        bericht.uebernehmen(MatchImporter(
            _EineLieferung(Lieferung(
                referenz=spieler.tag, format=FORMAT_OFFIZIELLER_BATTLELOG, rohdaten=huelle,
                source=Datenquelle.API, matches=ergebnis.matches,
                fehler=ergebnis.fehler, uebersprungen=ergebnis.uebersprungen,
            )),
            katalog_ergaenzen=True,
        ).ausfuehren())

        eintraege = antwort.daten.get("items") if isinstance(antwort.daten, dict) else []
        anzahl = len(eintraege) if isinstance(eintraege, list) else 0
        solo = sum(1 for r in ergebnis.matches
                   if r.battle_type in config.DRAFT_STATISTIK_BATTLE_TYPEN)
        bericht.battlelogs_ok += 1
        bericht.battlelog_eintraege += anzahl

        jetzt = self._jetzt()
        spieler.last_fetched_at = jetzt
        spieler.next_fetch_after = None
        spieler.last_status = "200"
        spieler.last_error = ""
        spieler.fetch_count += 1
        spieler.error_streak = 0
        spieler.last_battle_count = anzahl
        spieler.last_solo_ranked_count = solo
        spieler.save()
        self._entdecken(spieler, ergebnis, bericht)

    def _unbekannte_brawler_nachladen(self, ergebnis, bericht):
        """Neue Brawler-ID gesehen? Einmal je Lauf den Katalog nachziehen.

        Wichtig fuer die Deduplizierung: der Fingerabdruck einer Partie
        haengt daran, ob der Katalog den Brawler kennt. Wuerde ein Brawler
        erst zwischen zwei Battlelogs bekannt, bekaeme dieselbe Partie zwei
        verschiedene Fingerabdruecke.
        """
        if self._katalog_nachgeladen:
            return
        ids = {
            s.external_brawler_id
            for record in ergebnis.matches
            for team in record.teams.values()
            for s in team
            if s.external_brawler_id
        }
        if not ids:
            return
        bekannt = set(
            Brawler.objects.filter(external_id__in=ids).values_list("external_id", flat=True)
        )
        unbekannt = ids - bekannt
        if not unbekannt:
            return
        self._katalog_nachgeladen = True
        bericht.katalog.append(
            f"Unbekannte Brawler-IDs {sorted(unbekannt)} - Katalog wird neu abgerufen"
        )
        self._katalog(bericht)

    # --- Schritt 4: Entdecken -------------------------------------------
    def _entdecken(self, spieler, ergebnis, bericht):
        tiefe = spieler.depth + 1
        if tiefe > self.max_tiefe:
            return
        tags = set()
        for record in ergebnis.matches:
            if record.battle_type not in config.COLLECTOR_ENTDECKEN_AUS_TYPEN:
                continue
            for team in record.teams.values():
                for s in team:
                    try:
                        tags.add(tag_bereinigen(s.player_tag))
                    except ApiFehler:
                        continue
        tags.discard(spieler.tag)
        if not tags:
            return
        bekannt = set(
            TrackedPlayer.objects.filter(tag__in=tags).values_list("tag", flat=True)
        )
        neu = [
            TrackedPlayer(
                tag=tag, origin=TrackedPlayer.Origin.DISCOVERED, depth=tiefe,
                discovered_from=spieler.tag,
            )
            for tag in sorted(tags - bekannt)
        ]
        TrackedPlayer.objects.bulk_create(neu, ignore_conflicts=True)
        bericht.spieler_entdeckt += len(neu)
