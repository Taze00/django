"""Synthetic fixtures only: trophy identities may be queried, never scored as Ranked."""
import hashlib
import io
import json
import tempfile
from pathlib import Path
from django.core.management import call_command, CommandError
from datetime import timedelta

from drafter.models import CollectorRun, Match, RawPayload, TaggedPlayer, TrackedPlayer
from drafter.models.discovery import DiscoveryPlayer, DiscoveryObservation
from drafter.services.brawl_api_client import BrawlApiClient, pfad_battlelog
from drafter.services.discovery_frontier import DiscoveryFrontierCollector
from drafter.tests.test_api_client import _http_fehler
from drafter.tests import test_tagged_frontier as fixtures
from drafter.tests.basis import DrafterTest
NOW, CUTOFF = fixtures.NOW, fixtures.CUTOFF


class DiscoveryFrontierTest(DrafterTest):
    battle = fixtures.TaggedFrontierTest.battle
    api = fixtures.TaggedFrontierTest.api
    collect = fixtures.TaggedFrontierTest.collect

    def setup_source(self, entries=None):
        self.collect(self.api(entries=entries if entries is not None else [self.battle("ranked")]))
        raw = RawPayload.objects.get(format="brawlstars.battlelog.raw")
        return [{"id": raw.pk, "content_hash": raw.content_hash}]

    def pilot(self, sources, client=None, **kwargs):
        kwargs.setdefault("max_battlelogs", 1)
        return DiscoveryFrontierCollector(source_payloads=sources, pilot_id="synthetic-pilot",
            protocol_hash="a" * 64, after=CUTOFF, client=client or self.api(),
            now=lambda: NOW, **kwargs).execute()

    def test_trophy_discovery_is_separate_and_preserves_exact_provenance(self):
        sources = self.setup_source()
        report = self.pilot(sources, max_battlelogs=0)
        self.assertEqual(report["query_eligible_tags_available"], 6)
        self.assertEqual(report["ranked_evidence_frontier_size"], 0)
        self.assertEqual(TaggedPlayer.objects.count(), 1)
        observation = DiscoveryObservation.objects.get(player__player__tag="#P1")
        self.assertEqual(observation.source, "trophy_battlelog")
        self.assertEqual(observation.relationship, "teammate")
        self.assertEqual(observation.battle_type, "ranked")
        self.assertEqual(observation.json_pointer, "/antwort/items/0/battle/teams/0/1/tag")
        self.assertIsNone(observation.match_id)
        self.assertNotEqual(observation.run_id, observation.payload.collector_run_id)
        self.assertEqual(observation.observed_at, observation.payload.fetched_at)
        self.assertEqual(DiscoveryObservation.objects.get(player__player__tag="#P4").relationship, "opponent")
        self.assertFalse(report["future_test_eligible"])

    def test_trophy_neighbor_queries_can_produce_real_ranked_evidence(self):
        sources = self.setup_source()
        client = self.api()
        client.antworten[pfad_battlelog("#P1")] = {"items": [self.battle(time="20260923T120000.000Z")]}
        report = self.pilot(sources, client)
        self.assertEqual(client.aufrufe, [pfad_battlelog("#P1")])
        self.assertEqual(report["new_eligible_solo_ranked_matches"], 1)
        self.assertEqual(report["ranked_evidence_frontier_size"], 6)
        self.assertEqual(report["raw_battle_types"], {"soloRanked": 1})
        self.assertEqual(TaggedPlayer.objects.count(), 1, "Do not silently broaden the old frontier")

    def test_raw_soloranked_without_result_is_identity_not_evidence(self):
        battle = self.battle()
        battle["battle"].pop("result")
        sources = self.setup_source([battle])
        report = self.pilot(sources, max_battlelogs=0)
        self.assertEqual(report["discovery_frontier_size"], 6)
        self.assertEqual(report["ranked_evidence_frontier_size"], 0)
        self.assertEqual(DiscoveryPlayer.objects.get(player__tag="#P1").first_source, "soloRanked_battlelog")

    def test_no_tags_inferred_and_unknown_relationship_retained(self):
        sources = self.setup_source([self.battle("friendly", tags=["#REAL", None, "", 123, {}, "#OTHER"])])
        report = self.pilot(sources, max_battlelogs=0)
        self.assertEqual(report["discovery_frontier_size"], 2)
        self.assertEqual(set(DiscoveryObservation.objects.values_list("relationship", flat=True)), {"UNKNOWN"})
        self.assertEqual(report["ranked_evidence_frontier_size"], 0)

    def test_source_content_tampering_fails_before_http_and_repeat_is_blocked(self):
        sources = self.setup_source()
        raw = RawPayload.objects.get(pk=sources[0]["id"])
        raw.payload["antwort"]["items"][0]["battle"]["teams"][0][0]["tag"] = "#FAKE"
        raw.save(update_fields=["payload"])
        client = self.api()
        with self.assertRaises(ValueError):
            self.pilot(sources, client)
        self.assertEqual(client.aufrufe, [])
        self.assertEqual(DiscoveryPlayer.objects.count(), 0)
        with self.assertRaisesRegex(ValueError, "already attempted"):
            self.pilot(sources, client)

    def test_shared_cooldown_and_old_queue_are_preserved(self):
        sources = self.setup_source()
        existing = TrackedPlayer.objects.get(tag="#SEED")
        before = (existing.last_fetched_at, existing.next_fetch_after)
        TrackedPlayer.objects.create(tag="#UNPROVEN", origin="manual")
        report = self.pilot(sources, max_battlelogs=0)
        existing.refresh_from_db()
        self.assertEqual((existing.last_fetched_at, existing.next_fetch_after), before)
        self.assertFalse(DiscoveryPlayer.objects.filter(player__tag="#UNPROVEN").exists())
        self.assertEqual(report["query_eligible_tags_due"], 5)

    def test_ten_attempt_budget_includes_retries_and_backoff(self):
        sources = self.setup_source()
        calls = []
        def fail(request, timeout=None):
            calls.append(request.full_url)
            raise _http_fehler(503, {})
        client = BrawlApiClient(api_key="synthetic", oeffner=fail, schlafen=lambda _: None, mindestabstand=0)
        report = self.pilot(sources, client, max_battlelogs=10)
        self.assertEqual(len(calls), 10)
        self.assertEqual(report["battlelog_attempts"], 10)
        self.assertEqual(report["ranking_attempts"], 0)
        self.assertTrue(all(p.next_fetch_after >= NOW + timedelta(hours=6)
                            for p in TrackedPlayer.objects.filter(next_fetch_after__isnull=False)))

    def test_discovery_depth_one_never_queries_depth_two(self):
        sources = self.setup_source()
        client = self.api()
        client.antworten[pfad_battlelog("#P1")] = {"items": [self.battle("ranked", tags=["#P1", "#X1", "#X2", "#X3", "#X4", "#X5"])]}
        client.antworten[pfad_battlelog("#X1")] = {"items": [self.battle("ranked", tags=["#X1", "#Y1", "#Y2", "#Y3", "#Y4", "#Y5"])]}
        report = self.pilot(sources, client, max_battlelogs=10, max_depth=1)
        self.assertEqual(report["battlelog_attempts"], 10)
        self.assertFalse(any("Y" in url for url in client.aufrufe))
        self.assertTrue(DiscoveryPlayer.objects.filter(player__tag="#Y1").exists())

    def test_boundary_rejected_and_repeat_success_refused(self):
        sources = self.setup_source()
        for kwargs in ({"max_battlelogs": 11}, {"ranking_seeds": 1}, {"max_depth": 2}):
            with self.assertRaises(ValueError):
                self.pilot(sources, **kwargs)
        self.pilot(sources, max_battlelogs=0)
        with self.assertRaisesRegex(ValueError, "already attempted"):
            self.pilot(sources)

    def test_cutoff_cannot_reopen_old_evidence(self):
        with self.assertRaisesRegex(ValueError, "historical"):
            DiscoveryFrontierCollector(source_payloads=[{"id": 1}], pilot_id="test",
                protocol_hash="a"*64, after=CUTOFF-timedelta(seconds=1))

    def test_command_rejects_changed_protocol_or_implementation_before_run(self):
        protocol = {"schema":"discovery-pilot-1", "purpose":"pre_registration_development_pilot",
                    "future_test_eligible":False, "preregistered_at":"2026-09-01T00:00:00Z",
                    "implementation_sha256":{"drafter/services/discovery_frontier.py":"0"*64}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"protocol.json"
            raw = json.dumps(protocol).encode(); path.write_bytes(raw)
            for expected in ("0"*64, hashlib.sha256(raw).hexdigest()):
                with self.assertRaises(CommandError):
                    call_command("collect_discovery_pilot", protocol=str(path),
                                 expected_sha256=expected, code_revision="synthetic", stdout=io.StringIO())
        self.assertEqual(CollectorRun.objects.count(), 0)
