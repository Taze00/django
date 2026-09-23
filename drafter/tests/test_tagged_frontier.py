"""Synthetic API contract data only; never imported as production evidence."""

import io
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.core.management import CommandError, call_command

from drafter.models import CollectorRun, Match, RawPayload, TaggedPlayer, TaggedPlayerObservation, TrackedPlayer
from drafter.services.brawl_api_client import BrawlApiClient, pfad_battlelog, pfad_rangliste_spieler
from drafter.services.tagged_frontier import TaggedFrontierCollector, SAMPLING
from drafter.tests.basis import DrafterTest
from drafter.tests.test_api_client import _Antwort, _http_fehler
from drafter.tests.test_collector import ErsatzClient

NOW = datetime(2026, 9, 23, 13, tzinfo=timezone.utc)
CUTOFF = datetime(2026, 9, 18, 15, 4, 42, tzinfo=timezone.utc)
SEED = "#SEED"


class ClockClient(ErsatzClient):
    def __init__(self, *args, moment=NOW, **kwargs):
        super().__init__(*args, **kwargs)
        self.moment = moment

    def abrufen(self, *args, **kwargs):
        return replace(super().abrufen(*args, **kwargs), abgerufen_am=self.moment)


class TaggedFrontierTest(DrafterTest):
    def battle(self, battle_type="soloRanked", *, tags=None, time="20260923T110000.000Z"):
        tags = tags if tags is not None else [SEED, "#P1", "#P2", "#P3", "#P4", "#P5"]
        players = []
        for tag, slug in zip(tags, ("gale", "belle", "max", "buster", "gene", "tick")):
            players.append({"tag": tag, "brawler": {"name": self.brawler(slug).name}})
        return {"battleTime": time, "event": {"map": self.karte().name, "mode": "gemGrab"},
                "battle": {"type": battle_type, "mode": "gemGrab", "result": "victory",
                           "teams": [players[:3], players[3:]]}}

    def api(self, *, entries=None, ranking=None, moment=NOW):
        if ranking is None:
            ranking = [{"tag": SEED, "rank": 1, "trophies": 100000}]
        return ClockClient({pfad_rangliste_spieler(): {"items": ranking},
                            pfad_battlelog(SEED): {"items": entries if entries is not None else [self.battle()]}},
                           standard={"items": []}, moment=moment)

    def collect(self, client=None, **options):
        options.setdefault("ranking_seeds", 1)
        options.setdefault("max_battlelogs", 1)
        options.setdefault("now", lambda: NOW)
        return TaggedFrontierCollector(client=client or self.api(), after=CUTOFF, **options).execute()

    def test_seed_has_exact_raw_pointer_run_and_no_skill_claim(self):
        report = self.collect(max_battlelogs=0)
        frontier = TaggedPlayer.objects.get()
        observation = frontier.observations.get()
        self.assertEqual(frontier.player.tag, SEED)
        self.assertEqual(frontier.first_source, "ranking")
        self.assertEqual(frontier.first_seen, NOW)
        self.assertEqual(frontier.last_seen, NOW)
        self.assertEqual(frontier.first_run_id, report["run_id"])
        self.assertEqual(observation.json_pointer, "/antwort/items/0/tag")
        self.assertEqual(observation.payload.payload["antwort"]["items"][0]["tag"], SEED)
        self.assertEqual(observation.payload.payload["endpoint"], "/rankings/global/players")
        self.assertEqual(observation.payload.collector_run_id, report["run_id"])
        self.assertEqual(observation.payload.sampling, SAMPLING)
        self.assertIsNone(observation.match_id)
        self.assertEqual(report["skill_labels"], "UNKNOWN")
        self.assertEqual(report["ranking_seeds_due"], 1)

    def test_discovery_persists_and_next_run_queries_without_rankings(self):
        first = self.collect()
        self.assertEqual(first["new_discovered_tags"], 5)
        self.assertEqual(first["frontier_size"], 6)
        discovered = TaggedPlayer.objects.get(player__tag="#P1")
        observation = discovered.observations.get()
        self.assertEqual(discovered.first_source, "solo_ranked")
        self.assertEqual(observation.queried_player.tag, SEED)
        self.assertEqual(observation.match.battle_type, "soloRanked")
        self.assertEqual(observation.json_pointer, "/antwort/items/0/battle/teams/0/1/tag")
        self.assertEqual(observation.payload.reference, SEED)
        self.assertEqual(first["new_eligible_solo_ranked_matches"], 1)
        client = self.api()
        second = self.collect(client, ranking_seeds=0)
        self.assertEqual(second["battlelog_attempts"], 1)
        self.assertEqual(client.aufrufe, [pfad_battlelog("#P1")])
        self.assertEqual(TaggedPlayer.objects.get(player__tag=SEED).first_source, "ranking")
        self.assertTrue(TaggedPlayerObservation.objects.filter(source="query", json_pointer="/referenz").exists())

    def test_player_duplicates_and_missing_fields_are_not_invented(self):
        client = self.api(ranking=[{"tag": " #seed "}, {"tag": SEED}, {},
                                   {"tag": 123}, {"tag": "bad/tag"}, {"tag": "#NEXT"}])
        report = self.collect(client, ranking_seeds=5, max_battlelogs=0)
        self.assertEqual(report["ranking_duplicate_tags"], 1)
        self.assertEqual(report["ranking_invalid_tags"], 3)
        self.assertEqual(report["frontier_size"], 2)
        seed = TrackedPlayer.objects.get(tag=SEED)
        self.assertIsNone(seed.ranking_position)
        self.assertIsNone(seed.ranking_trophies)

    def test_missing_tags_never_come_from_names_ids_or_historical_players(self):
        battle = self.battle(tags=[SEED, None, "", 1234, {}, "#P5"])
        battle["battle"]["teams"][0][1]["name"] = "#INVENTED"
        self.collect(self.api(entries=[battle]))
        self.assertEqual(set(TaggedPlayer.objects.values_list("player__tag", flat=True)), {SEED, "#P5"})
        self.assertEqual(Match.objects.get().players.filter(player_tag="").count(), 4)

    def test_only_complete_known_result_new_soloranked_discovers(self):
        entries = [self.battle("ranked"), self.battle("friendly", time="20260923T110100.000Z"),
                   self.battle(time="20260918T150442.000Z")]
        unknown = self.battle(time="20260923T110200.000Z")
        unknown["battle"].pop("result")
        incomplete = self.battle(time="20260923T110300.000Z")
        incomplete["battle"]["teams"][0].pop()
        unknown_brawler = self.battle(time="20260923T110400.000Z")
        unknown_brawler["battle"]["teams"][0][0]["brawler"] = {"id": 999999999, "name": "UNKNOWN"}
        report = self.collect(self.api(entries=entries + [unknown, incomplete, unknown_brawler]))
        self.assertEqual(report["new_discovered_tags"], 0)
        self.assertEqual(report["new_eligible_solo_ranked_matches"], 0)
        self.assertEqual(report["historical_records_retained_raw_only"], 1)
        self.assertEqual(Match.objects.filter(played_at__lte=CUTOFF).count(), 0)
        self.assertEqual(report["api"]["anfragen"], 2, "No hidden catalog refresh")

    def test_duplicate_matches_keep_payloads_and_never_backfill_player_tags(self):
        self.collect()
        match = Match.objects.get()
        match.players.update(player_tag="")  # Simulate anonymized imported identities, test DB only.
        TrackedPlayer.objects.exclude(tag=SEED).update(is_active=False)
        later = NOW + timedelta(hours=6)
        report = self.collect(self.api(moment=later), ranking_seeds=0, now=lambda: later)
        self.assertEqual(Match.objects.count(), 1)
        self.assertEqual(match.payloads.count(), 2)
        self.assertEqual(match.players.filter(player_tag="").count(), 6)
        self.assertEqual(report["neu"], 0)
        self.assertEqual(report["duplikate"], 1)
        self.assertEqual(report["new_discovered_tags"], 0)
        self.assertEqual(TaggedPlayer.objects.count(), 6)

    def test_cooldown_survives_discovery_and_exact_six_hour_revisit(self):
        self.collect(self.api(entries=[]))
        tracked = TrackedPlayer.objects.get(tag=SEED)
        before = (tracked.last_fetched_at, tracked.next_fetch_after, tracked.fetch_count)
        later = NOW + timedelta(hours=5)
        report = self.collect(self.api(entries=[], moment=later), now=lambda: later)
        tracked.refresh_from_db()
        self.assertEqual(report["api"]["anfragen"], 0)
        self.assertTrue(report["ranking_cooldown_skipped"])
        self.assertEqual((tracked.last_fetched_at, tracked.next_fetch_after, tracked.fetch_count), before)
        later = NOW + timedelta(hours=6)
        report = self.collect(self.api(entries=[], moment=later), now=lambda: later)
        tracked.refresh_from_db()
        self.assertEqual(report["api"]["anfragen"], 2)
        self.assertEqual(tracked.fetch_count, 2)
        frontier = TaggedPlayer.objects.get()
        self.assertEqual(frontier.first_seen, NOW)
        self.assertEqual(frontier.last_seen, later)

    def test_existing_queue_cooldown_is_not_reset_by_new_frontier_membership(self):
        tracked = TrackedPlayer.objects.create(tag=SEED, origin="manual", last_fetched_at=NOW,
                                              next_fetch_after=NOW + timedelta(hours=10))
        self.collect()
        tracked.refresh_from_db()
        self.assertEqual(tracked.last_fetched_at, NOW)
        self.assertEqual(tracked.next_fetch_after, NOW + timedelta(hours=10))
        self.assertEqual(tracked.origin, "manual")
        self.assertEqual(TaggedPlayer.objects.get().first_source, "ranking")
        self.assertEqual(Match.objects.count(), 0)

    def test_empty_frontier_does_not_adopt_old_queue_or_make_requests(self):
        TrackedPlayer.objects.create(tag="#OLD", origin="ranking")
        client = self.api()
        report = self.collect(client, ranking_seeds=0)
        self.assertEqual(client.aufrufe, [])
        self.assertEqual(report["frontier_size"], 0)
        self.assertEqual(report["data_status"], "DATA_UNAVAILABLE")

    def test_rankings_without_tags_are_saved_then_stop_without_battlelogs(self):
        client = self.api(ranking=[{"name": "Cannot infer tag"}, {"tag": None}])
        report = self.collect(client)
        self.assertEqual(client.battlelog_aufrufe, [])
        self.assertIn("RANKING_TAGS_UNAVAILABLE", report["abbruch"])
        self.assertEqual(RawPayload.objects.count(), 1)
        self.assertEqual(TaggedPlayer.objects.count(), 0)
        self.assertEqual(CollectorRun.objects.get().status, "aborted")

    def test_one_ranking_request_and_at_most_five_battlelogs(self):
        client = self.api(ranking=[{"tag": f"#S{i}"} for i in range(200)])
        report = self.collect(client, ranking_seeds=3, max_battlelogs=5)
        self.assertEqual(report["ranking_entries"], 200)
        self.assertEqual(report["ranking_seeds_admitted"], 3)
        self.assertEqual(report["frontier_size"], 3)
        self.assertEqual(report["battlelog_attempts"], 3)
        self.assertEqual(report["ranking_attempts"], 1)
        self.assertEqual(len(client.aufrufe), 4)

    def test_depth_zero_defers_discovered_players_until_next_run(self):
        client = self.api()
        report = self.collect(client, max_battlelogs=5, max_depth=0)
        self.assertEqual(len(client.battlelog_aufrufe), 1)
        self.assertEqual(report["frontier_size"], 6)
        second = self.collect(self.api(), ranking_seeds=0, max_battlelogs=5, max_depth=0)
        self.assertEqual(second["battlelog_attempts"], 5)

    def test_depth_one_persists_boundary_tags_without_querying_them(self):
        client = self.api()
        child = self.battle(tags=["#P1", "#X1", "#X2", "#X3", "#X4", "#X5"],
                            time="20260923T110100.000Z")
        client.antworten[pfad_battlelog("#P1")] = {"items": [child]}
        report = self.collect(client, max_battlelogs=5)
        self.assertEqual(report["battlelog_attempts"], 5)
        self.assertEqual(report["frontier_size"], 11)
        self.assertFalse(any("X" in path for path in client.battlelog_aufrufe))
        self.assertEqual(TaggedPlayer.objects.get(player__tag="#X1").discovery_depth, 2)

    def test_retry_attempts_consume_budget_with_existing_backoff(self):
        calls, sleeps = [], []
        def open_response(request, timeout=None):
            calls.append(request.full_url)
            if "rankings" in request.full_url:
                return _Antwort({"items": [{"tag": SEED}, {"tag": "#NEXT"}]})
            raise _http_fehler(503, {"reason": "maintenance"})
        client = BrawlApiClient(api_key="synthetic-test-key", oeffner=open_response,
                                schlafen=sleeps.append, mindestabstand=0)
        report = self.collect(client, ranking_seeds=2, max_battlelogs=5)
        self.assertEqual(len(calls), 6)
        self.assertEqual(report["ranking_attempts"], 1)
        self.assertEqual(report["battlelog_attempts"], 5)
        self.assertEqual(report["api"]["wiederholungen"], 3)
        self.assertEqual(sleeps, [1.0, 2.0, 4.0])
        self.assertEqual(client.versuche, 4)
        self.assertTrue(all(p.next_fetch_after >= NOW + timedelta(hours=6) for p in TrackedPlayer.objects.all()))
        self.assertNotIn("synthetic-test-key", json.dumps(report))

    def test_429_aborts_within_budget_and_honors_retry_after(self):
        calls, sleeps = [], []
        def open_response(request, timeout=None):
            calls.append(request.full_url)
            if "rankings" in request.full_url:
                return _Antwort({"items": [{"tag": SEED}, {"tag": "#NEXT"}]})
            error = _http_fehler(429, {})
            error.headers["Retry-After"] = "9"
            raise error
        client = BrawlApiClient(api_key="synthetic-test-key", oeffner=open_response,
                                schlafen=sleeps.append, mindestabstand=0)
        report = self.collect(client, ranking_seeds=2, max_battlelogs=5)
        self.assertEqual(report["abbruch"], "API_429")
        self.assertEqual(len(calls), 5)
        self.assertEqual(sleeps, [9.0, 9.0, 9.0])
        self.assertEqual(report["spieler_abgefragt"], 1)

    def test_credential_failure_and_malformed_payload_stop_safely(self):
        for status in (401, 403):
            with self.subTest(status=status):
                def open_response(request, timeout=None):
                    raise _http_fehler(status, {})
                client = BrawlApiClient(api_key="synthetic-test-key", oeffner=open_response)
                # Distinct run time avoids the explicit ranking cooldown.
                report = self.collect(client, now=lambda: NOW + timedelta(days=status - 400))
                self.assertEqual(report["api"]["anfragen"], 1)
                self.assertEqual(report["battlelog_attempts"], 0)
                self.assertEqual(report["abbruch"], f"API_{status}")

    def test_parser_failure_keeps_raw_query_provenance_and_cooldown(self):
        client = self.api()
        client.antworten[pfad_battlelog(SEED)] = {"not_items": []}
        report = self.collect(client)
        self.assertEqual(report["fehler"], {"parser": 1})
        self.assertEqual(RawPayload.objects.filter(parse_status="error").count(), 1)
        self.assertEqual(TaggedPlayerObservation.objects.filter(source="query").count(), 1)
        self.assertEqual(TrackedPlayer.objects.get().last_fetched_at, NOW)
        self.assertEqual(Match.objects.count(), 0)

    def test_crash_retains_raw_response_and_durable_claim(self):
        with patch("drafter.services.tagged_frontier.parse_offizieller_battlelog", side_effect=RuntimeError("test")):
            with self.assertRaises(RuntimeError):
                self.collect()
        self.assertEqual(RawPayload.objects.count(), 2)
        self.assertEqual(CollectorRun.objects.get().status, "aborted")
        self.assertGreater(TrackedPlayer.objects.get().next_fetch_after, NOW)

    def test_no_key_no_request_and_command_rejects_invalid_boundaries(self):
        client = BrawlApiClient(api_key="")
        report = self.collect(client)
        self.assertEqual(report["api"]["anfragen"], 0)
        self.assertEqual(report["battlelog_attempts"], 0)
        for cutoff in ("invalid", "2026-09-18", "2026-09-18T15:04:42"):
            with self.assertRaises(CommandError):
                call_command("collect_tagged_frontier", after=cutoff, stdout=io.StringIO())
        for args in ({"max_battlelogs": 6}, {"ranking_seeds": 6}, {"max_depth": 2}):
            with self.assertRaises(ValueError):
                TaggedFrontierCollector(after=CUTOFF, **args)

    def test_other_player_perspective_deduplicates_and_preserves_both_queries(self):
        client = self.api()
        other_view = self.battle()
        other_view["battle"]["result"] = "defeat"  # #P3 is on the opposing team.
        client.antworten[pfad_battlelog("#P3")] = {"items": [other_view]}
        report = self.collect(client, max_battlelogs=5)
        self.assertEqual(report["neu"], 1)
        self.assertEqual(report["duplikate"], 1)
        self.assertEqual(report["konflikte"], 0)
        self.assertEqual(Match.objects.get().payloads.count(), 2)
        self.assertEqual(set(TaggedPlayerObservation.objects.filter(
            source="solo_ranked", player__player__tag="#P2"
        ).values_list("queried_player__tag", flat=True)), {SEED, "#P3"})

    def test_conflicting_match_cannot_seed_new_tags(self):
        self.collect()
        match = Match.objects.get()
        match.has_conflict = True
        match.save(update_fields=["has_conflict"])
        TrackedPlayer.objects.exclude(tag=SEED).update(is_active=False)
        changed = self.battle(tags=[SEED, "#NEW1", "#NEW2", "#NEW3", "#NEW4", "#NEW5"])
        later = NOW + timedelta(hours=6)
        report = self.collect(self.api(entries=[changed], moment=later),
                              ranking_seeds=0, now=lambda: later)
        self.assertEqual(report["duplikate"], 1)
        self.assertEqual(report["new_discovered_tags"], 0)
        self.assertEqual(TaggedPlayer.objects.count(), 6)

    def test_no_key_does_not_claim_existing_due_frontier(self):
        self.collect(max_battlelogs=0)
        report = self.collect(BrawlApiClient(api_key=""), ranking_seeds=0)
        self.assertEqual(report["spieler_abgefragt"], 0)
        self.assertIsNone(TrackedPlayer.objects.get().next_fetch_after)
        self.assertEqual(report["api"]["anfragen"], 0)

    def test_404_keeps_seven_day_pause_and_continues_within_budget(self):
        client = self.api(ranking=[{"tag": "#A404"}, {"tag": SEED}])
        client.antworten[pfad_battlelog("#A404")] = None
        report = self.collect(client, ranking_seeds=2, max_battlelogs=2)
        missing = TrackedPlayer.objects.get(tag="#A404")
        self.assertEqual(report["fehler"], {"404": 1})
        self.assertEqual(report["battlelog_attempts"], 2)
        self.assertEqual(missing.next_fetch_after, NOW + timedelta(days=7))
        self.assertEqual(missing.last_fetched_at, NOW)
        self.assertEqual(report["battlelogs_ok"], 1)

    def test_newer_sighting_cannot_update_sealed_row_via_fingerprint_tolerance(self):
        old = self.battle(time="20260918T150442.000Z")
        TaggedFrontierCollector(client=self.api(entries=[old]), after=CUTOFF - timedelta(seconds=1),
                               ranking_seeds=1, max_battlelogs=1, now=lambda: NOW).execute()
        match = Match.objects.get()
        match.winner_side = ""
        match.save(update_fields=["winner_side"])
        match.players.update(player_tag="")
        old_payload_ids = set(match.payloads.values_list("pk", flat=True))
        TrackedPlayer.objects.exclude(tag=SEED).update(is_active=False)
        new_sighting = self.battle(time="20260918T150442.500Z")
        later = NOW + timedelta(hours=6)
        report = self.collect(self.api(entries=[new_sighting], moment=later),
                              ranking_seeds=0, now=lambda: later)
        match.refresh_from_db()
        self.assertEqual(report["protected_historical_duplicates_raw_only"], 1)
        self.assertEqual(match.winner_side, "")
        self.assertEqual(match.players.filter(player_tag="").count(), 6)
        self.assertEqual(set(match.payloads.values_list("pk", flat=True)), old_payload_ids)
        self.assertEqual(report["new_discovered_tags"], 0)
