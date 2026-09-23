"""Belegte, persistente Tagged-Frontier, getrennt von broad_high_rank.

Nur neue Beobachtungen nach einem expliziten Stichtag werden importiert.
Ranglisten sind Trophaeen-Saat, kein Ranked-/Skill-Nachweis. Alte MatchPlayer
werden weder gelesen, rekonstruiert noch mit Tags aufgefuellt.
"""

import re
from collections import Counter
from datetime import timedelta

from django.db import connection, transaction
from django.db.models import F, Q
from django.utils import timezone

from drafter import config
from drafter.models import CollectorRun, Datenquelle, Match, RawPayload
from drafter.models.collector import TaggedPlayer, TaggedPlayerObservation, TrackedPlayer
from drafter.services.brawl_api_client import (
    ApiFehler, BrawlApiClient, KeinKeyFehler, pfad_battlelog, pfad_rangliste_spieler,
)
from drafter.services.collector import _EineLieferung, SammelBericht
from drafter.services.ingest.importer import MatchImporter, inhalts_hash
from drafter.services.ingest.parser import (
    FORMAT_OFFIZIELLE_RANGLISTE, FORMAT_OFFIZIELLER_BATTLELOG,
    ParserFehler, parse_offizieller_battlelog,
)
from drafter.services.providers.official_api import verpacke_mitschnitt
from drafter.services.providers.records import Lieferung

SAMPLING = "tagged_frontier_v1"
COOLDOWN = timedelta(hours=6)


def beobachteter_tag(value):
    """Nur gelieferte Strings; keine Konvertierung aus Zahlen/Namen/IDs.

    Syntaxfilter, kein Beweis fuer einen existierenden Account. Normalisiert
    nur Grossschreibung/Rand-Leerraum; Original bleibt im RawPayload.
    """
    if not isinstance(value, str):
        return None
    tag = value.strip().upper()
    return tag if re.fullmatch(r"#[A-Z0-9]{1,19}", tag) else None


def eligible(match):
    if (match.source != Datenquelle.API or not match.is_ranked
            or match.battle_type != "soloRanked" or not match.ist_zaehlbar):
        return False
    players = list(match.players.all())
    return (len(players) == 6 and Counter(p.side for p in players) == {"a": 3, "b": 3}
            and all(p.brawler_id is not None for p in players))


class TaggedFrontierCollector:
    """Maximal ein Ranglistenversuch und fuenf Battlelog-HTTP-Versuche.

    Depth begrenzt neue Abruf-Hops INNERHALB eines Laufs. Schon persistierte
    Frontier-Spieler sind Wurzeln des naechsten Laufs. Tags an der Grenze
    bleiben mit ihrer Graphkante gespeichert, werden aber erst spaeter
    abgefragt. So ist Wachstum ueber mehrere Laeufe ohne offene Rekursion
    moeglich. TrackedPlayer liefert den strategieuebergreifenden Cooldown.
    """

    def __init__(self, *, after, ranking_seeds=0, max_battlelogs=5, max_depth=1,
                 client=None, now=None, code_revision="UNKNOWN"):
        if after is None or after.utcoffset() is None:
            raise ValueError("after requires an explicit timezone")
        if not 0 <= ranking_seeds <= 5 or not 0 <= max_battlelogs <= 5:
            raise ValueError("seed and battlelog budgets must be between 0 and 5")
        if max_depth not in (0, 1):
            raise ValueError("max_depth must be 0 or 1 for this bounded experiment")
        self.after = after
        self.ranking_seeds = ranking_seeds
        self.max_battlelogs = max_battlelogs
        self.max_depth = max_depth
        self.client = client if client is not None else BrawlApiClient()
        self.now = now or timezone.now
        self.code_revision = code_revision
        self.summary = SammelBericht()
        self.run = None
        self.depths = {}
        self.new_match_ids = set()
        self.metrics = {
            "report_version": SAMPLING, "ranking_attempts": 0, "battlelog_attempts": 0,
            "ranking_entries": 0, "ranking_valid_unique_tags": 0,
            "ranking_seeds_admitted": 0, "ranking_seeds_due": 0,
            "ranking_duplicate_tags": 0, "ranking_invalid_tags": 0,
            "ranking_cooldown_skipped": False, "new_discovered_tags": 0,
            "new_frontier_seeds": 0, "duplicate_player_observations": 0,
            "invalid_discovered_tags": 0, "historical_records_retained_raw_only": 0,
            "protected_historical_duplicates_raw_only": 0,
            "new_eligible_solo_ranked_matches": 0,
            "holdout_evaluated": False, "skill_labels": "UNKNOWN",
        }

    def execute(self):
        # Session-Lock: parallele Bootstrap-Prozesse duerfen weder Saat noch
        # Budget verdoppeln. Bei Prozessabbruch gibt PostgreSQL ihn frei.
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s, %s)", [20260923, 1201])
            locked = cursor.fetchone()[0]
        if not locked:
            raise ApiFehler("A tagged frontier collector is already running")
        try:
            return self._execute()
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s, %s)", [20260923, 1201])

    def _execute(self):
        self.run = CollectorRun.objects.create(started_at=self.now(), parameters={
            "strategie": SAMPLING, "ranking_seeds": self.ranking_seeds,
            "ranking_http_budget": int(bool(self.ranking_seeds)),
            "battlelog_http_budget": self.max_battlelogs, "max_tiefe": self.max_depth,
            "depth_semantics": "new_request_hops_per_run",
            "abruf_abstand_stunden": 6, "after_exclusive": self.after.isoformat(),
            "code_revision": self.code_revision, "catalog_requests": 0,
        })
        self.depths = dict.fromkeys(TaggedPlayer.objects.values_list("player_id", flat=True), 0)
        self.metrics["frontier_before"] = len(self.depths)
        try:
            if self.ranking_seeds:
                self._ranking()
            self._battlelogs()
        except ApiFehler as error:
            # Keine Antwortkoerper/Headers/Fehlertexte im Bericht. Der Client
            # bereinigt ebenfalls; hier reichen Status und Ausnahmeklasse.
            self.summary.abbruch = ("RANKING_TAGS_UNAVAILABLE: raw response retained"
                if error.grund == "unusable_ranking" else f"API_{error.status or type(error).__name__}")
        except BaseException:
            self.summary.abbruch = "PROCESSING_ERROR: inspect stored payloads before resuming"
            raise
        finally:
            self.summary.api = self.client.statistik.als_dict()
            self.metrics["frontier_size"] = TaggedPlayer.objects.count()
            self.metrics["new_eligible_solo_ranked_matches"] = sum(
                eligible(match) for match in Match.objects.filter(
                    pk__in=self.new_match_ids).prefetch_related("players")
            )
            report = {**self.summary.als_dict(), **self.metrics, "run_id": self.run.pk}
            report["data_status"] = ("OBSERVATIONS_AVAILABLE" if
                report["new_eligible_solo_ranked_matches"] else "DATA_UNAVAILABLE")
            self.run.finished_at = self.now()
            self.run.status = (CollectorRun.Status.ABORTED if self.summary.abbruch
                               else CollectorRun.Status.FINISHED)
            self.run.abort_reason = self.summary.abbruch
            self.run.report = report
            self.run.save()
        return report

    def _request(self, path, kind, remaining):
        # Der vorhandene Client behaelt Spacing, Backoff und Retry-After.
        # Wiederholungen verbrauchen dasselbe harte HTTP-Budget wie Erstversuche.
        before = self.client.statistik.anfragen
        original = self.client.versuche
        self.client.versuche = min(original, remaining)
        try:
            return self.client.abrufen(path)
        finally:
            self.metrics[kind + "_attempts"] += self.client.statistik.anfragen - before
            self.client.versuche = original

    def _raw(self, answer, reference, format_name):
        envelope = verpacke_mitschnitt(answer, reference, format_name)
        payload, _ = RawPayload.objects.get_or_create(content_hash=inhalts_hash(envelope), defaults={
            "source": Datenquelle.API, "format": format_name, "reference": reference,
            "payload": envelope, "fetched_at": answer.abgerufen_am,
            "sampling": SAMPLING, "collector_run": self.run,
            "parse_status": RawPayload.ParseStatus.UNSUPPORTED,
            "parse_message": "Persisted before parsing by tagged frontier",
        })
        return payload

    def _observe(self, tag, source, payload, pointer, *, parent=None, match=None,
                 ranking=None):
        seen = payload.fetched_at
        with transaction.atomic():
            defaults = {"origin": (TrackedPlayer.Origin.RANKING if source == "ranking"
                                    else TrackedPlayer.Origin.DISCOVERED),
                        "discovered_from": parent.player.tag if parent else ""}
            if ranking:
                for key, field in (("rank", "ranking_position"), ("trophies", "ranking_trophies")):
                    value = ranking.get(key)
                    defaults[field] = value if type(value) is int and value >= 0 else None
            tracked, _ = TrackedPlayer.objects.get_or_create(tag=tag, defaults=defaults)
            depth = parent.discovery_depth + 1 if parent else 0
            frontier, new = TaggedPlayer.objects.get_or_create(player=tracked, defaults={
                "first_source": source, "first_seen": seen, "last_seen": seen,
                "discovery_depth": depth, "first_run": self.run,
            })
            if not new:
                frontier = TaggedPlayer.objects.select_for_update().get(pk=frontier.pk)
                frontier.last_seen = max(frontier.last_seen, seen)
                if source != "query":
                    frontier.discovery_depth = min(frontier.discovery_depth, depth)
                frontier.save(update_fields=["last_seen", "discovery_depth"])
                self.metrics["duplicate_player_observations"] += 1
            TaggedPlayerObservation.objects.get_or_create(
                player=frontier, source=source, payload=payload, run=self.run,
                json_pointer=pointer, defaults={"observed_at": seen, "match": match,
                    "queried_player": parent.player if parent else None},
            )
        if source != "query":
            hop = self.depths[parent.player_id] + 1 if parent else 0
            self.depths[tracked.pk] = min(self.depths.get(tracked.pk, hop), hop)
        return frontier, new

    def _due(self):
        now = self.now()
        return TrackedPlayer.objects.filter(is_active=True).filter(
            Q(last_fetched_at__isnull=True) | Q(last_fetched_at__lte=now - COOLDOWN)
        ).filter(Q(next_fetch_after__isnull=True) | Q(next_fetch_after__lte=now))

    def _ranking(self):
        # Auch unveraenderte oder fehlgeschlagene Ranglisten nicht hektisch
        # wiederholen. Ein neuer Lauf setzt weder diesen noch Spieler-Timer zurueck.
        previous = CollectorRun.objects.filter(
            parameters__strategie=SAMPLING, started_at__gt=self.now() - COOLDOWN,
            report__ranking_attempts__gt=0,
        ).exclude(pk=self.run.pk).exists()
        if previous:
            self.metrics["ranking_cooldown_skipped"] = True
            return
        answer = self._request(pfad_rangliste_spieler("global"), "ranking", 1)
        payload = self._raw(answer, "global", FORMAT_OFFIZIELLE_RANGLISTE)
        items = answer.daten.get("items") if isinstance(answer.daten, dict) else None
        if not isinstance(items, list):
            raise ApiFehler("No ranking items", grund="unusable_ranking")
        self.metrics["ranking_entries"] = len(items)
        seen, admitted = set(), []
        for index, item in enumerate(items):
            tag = beobachteter_tag(item.get("tag")) if isinstance(item, dict) else None
            if tag is None:
                self.metrics["ranking_invalid_tags"] += 1
                continue
            if tag in seen:
                self.metrics["ranking_duplicate_tags"] += 1
                continue
            seen.add(tag)
            if len(admitted) >= self.ranking_seeds:
                continue
            frontier, new = self._observe(tag, "ranking", payload,
                f"/antwort/items/{index}/tag", ranking=item)
            admitted.append(frontier.player_id)
            self.metrics["new_frontier_seeds"] += int(new)
        self.metrics["ranking_valid_unique_tags"] = len(seen)
        self.metrics["ranking_seeds_admitted"] = len(admitted)
        self.metrics["ranking_seeds_due"] = self._due().filter(pk__in=admitted).count()
        if not seen:
            # Explizit stoppen, auch wenn andere Frontier-Spieler vorhanden sind.
            # Kein stiller Ersatz der vom Nutzer angeforderten Saatquelle.
            self.summary.abbruch = "RANKING_TAGS_UNAVAILABLE: raw response retained"
            raise ApiFehler("No usable ranking tags", grund="unusable_ranking")

    def _claim(self, queried):
        allowed = [pk for pk, depth in self.depths.items() if depth <= self.max_depth]
        with transaction.atomic():
            player = self._due().filter(pk__in=allowed).exclude(pk__in=queried).order_by(
                F("last_fetched_at").asc(nulls_first=True), "tagged_frontier__first_seen", "tag"
            ).select_for_update(of=("self",), skip_locked=True).first()
            if player is None:
                return None
            # Dauerhafte Lease vor HTTP: Prozessabbruch fuehrt zu einer Pause,
            # nicht zu einem unprotokollierten unmittelbaren Wiederholungsabruf.
            player.next_fetch_after = self.now() + COOLDOWN
            player.save(update_fields=["next_fetch_after", "updated_at"])
            return player

    def _battlelogs(self):
        if self.max_battlelogs and self._due().filter(pk__in=self.depths).exists() \
                and not self.client.einsatzbereit:
            raise KeinKeyFehler("Isolated API credential is unavailable; no player was claimed")
        queried = set()
        failures = 0
        while self.metrics["battlelog_attempts"] < self.max_battlelogs:
            player = self._claim(queried)
            if player is None:
                return
            queried.add(player.pk)
            self.summary.spieler_abgefragt += 1
            try:
                answer = self._request(pfad_battlelog(player.tag), "battlelog",
                    self.max_battlelogs - self.metrics["battlelog_attempts"])
            except ApiFehler as error:
                status = str(error.status or "network")
                self.summary.fehler[status] += 1
                player.error_streak += 1
                player.last_status = status
                player.last_error = type(error).__name__
                if error.status == 404:
                    player.last_fetched_at = self.now()
                    player.next_fetch_after = self.now() + timedelta(days=config.COLLECTOR_404_PAUSE_TAGE)
                else:
                    hours = min(2 ** min(player.error_streak - 1, 6),
                                config.COLLECTOR_FEHLER_PAUSE_STUNDEN_MAX)
                    player.next_fetch_after = self.now() + max(COOLDOWN, timedelta(hours=hours))
                player.save()
                failures = 0 if error.status == 404 else failures + 1
                if error.status in (401, 403, 429) or failures >= config.COLLECTOR_ABBRUCH_NACH_FEHLERN:
                    raise
                continue
            failures = 0
            self._battlelog(player, answer)

    def _battlelog(self, player, answer):
        payload = self._raw(answer, player.tag, FORMAT_OFFIZIELLER_BATTLELOG)
        parent = TaggedPlayer.objects.select_related("player").get(player=player)
        self._observe(player.tag, "query", payload, "/referenz", parent=parent)
        # Der erfolgreiche HTTP-Abruf bleibt auch bei Parserfehlern dokumentiert.
        player.last_fetched_at = self.now()
        player.next_fetch_after = self.now() + COOLDOWN
        player.fetch_count += 1
        player.last_status = "200"
        player.last_error = ""
        player.error_streak = 0
        player.save()
        try:
            parsed = parse_offizieller_battlelog(payload.payload)
        except ParserFehler:
            payload.parse_status = RawPayload.ParseStatus.ERROR
            payload.parse_message = "Unsupported battlelog structure; raw response retained"
            payload.save(update_fields=["parse_status", "parse_message"])
            self.summary.fehler["parser"] += 1
            return
        recent = [r for r in parsed.matches if r.played_at > self.after]
        self.metrics["historical_records_retained_raw_only"] += len(parsed.matches) - len(recent)
        delivery = Lieferung(
            referenz=player.tag, format=FORMAT_OFFIZIELLER_BATTLELOG,
            rohdaten=payload.payload, source=Datenquelle.API, matches=recent,
            fehler=parsed.fehler, uebersprungen=parsed.uebersprungen,
            sampling=SAMPLING, collector_run_id=self.run.pk,
        )
        importer = MatchImporter(_EineLieferung(delivery))
        # Selbst eine neu datierte Sichtung darf durch Fingerprint-Toleranz
        # keine historische Zeile anreichern. Im Zweifel raw-only erhalten.
        safe = []
        for record in recent:
            existing = importer.finde_importierte_partie(record)
            if existing is not None and existing.played_at <= self.after:
                self.metrics["protected_historical_duplicates_raw_only"] += 1
            else:
                safe.append(record)
        delivery.matches = safe
        imported = importer.ausfuehren()
        self.summary.uebernehmen(imported)
        self.new_match_ids.update(imported.new_match_ids)
        payload.refresh_from_db()
        payload.parse_status = RawPayload.ParseStatus.ERROR if imported.fehlerhaft else RawPayload.ParseStatus.PARSED
        payload.parse_message = ("Import errors; raw response retained" if imported.fehlerhaft
                                 else "Parsed; only records after the explicit cutoff imported")
        payload.save(update_fields=["parse_status", "parse_message"])
        items = answer.daten["items"]
        self.summary.battlelogs_ok += 1
        self.summary.battlelog_eintraege += len(items)
        player.last_battle_count = len(items)
        player.last_solo_ranked_count = sum(r.battle_type == "soloRanked" for r in recent)
        player.save(update_fields=["last_battle_count", "last_solo_ranked_count", "updated_at"])
        # Parser je Roh-Eintrag: exakte JSON-Pointer trotz uebersprungener Items.
        for index, item in enumerate(items):
            single = {**payload.payload, "antwort": {"items": [item]}}
            for record in parse_offizieller_battlelog(single).matches:
                if (record.played_at <= self.after or record.battle_type != "soloRanked"
                        or not record.ranked or record.winner not in ("a", "b")):
                    continue
                match = importer.finde_importierte_partie(record)
                if (match is None or match.played_at <= self.after
                        or not match.payloads.filter(pk=payload.pk).exists() or not eligible(match)):
                    continue
                for team_index, team in enumerate(item["battle"]["teams"]):
                    for player_index, observed in enumerate(team):
                        tag = beobachteter_tag(observed.get("tag"))
                        if tag is None:
                            self.metrics["invalid_discovered_tags"] += 1
                            continue
                        _, new = self._observe(tag, "solo_ranked", payload,
                            f"/antwort/items/{index}/battle/teams/{team_index}/{player_index}/tag",
                            parent=parent, match=match)
                        self.metrics["new_discovered_tags"] += int(new)
                        self.summary.spieler_entdeckt += int(new)
