"""Synthetic contract fixtures, only in Django's isolated test database.

Some rows mimic source=api to exercise the filter, never real observations.
"""

import io
import json
from datetime import datetime, timedelta, timezone

from django.core.management import call_command, CommandError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from drafter.models.matches import Match, MatchPlayer, RawPayload
from drafter.models.collector import CollectorRun
from drafter.tests.basis import DrafterTest


class V2GrowthTest(DrafterTest):
    cutoff = datetime(2026, 9, 18, 15, 4, 42, tzinfo=timezone.utc)

    def match(self, name, **overrides):
        fields = dict(fingerprint=name, source="api", battle_type="soloRanked",
                      is_ranked=True, winner_side="a", played_at=self.cutoff + timedelta(seconds=1))
        fields.update(overrides)
        match = Match.objects.create(**fields)
        for index, slug in enumerate(("gale", "belle", "max", "buster", "gene", "tick")):
            MatchPlayer.objects.create(match=match, side="a" if index < 3 else "b",
                                       brawler=self.brawler(slug), brawler_name=slug)
        return match

    def report(self, **kwargs):
        out = io.StringIO()
        call_command("drafter_v2_growth", after=self.cutoff.isoformat(), format="json", stdout=out, **kwargs)
        return json.loads(out.getvalue())

    def test_excludes_old_and_boundary_even_if_imported_later(self):
        self.match("old", played_at=self.cutoff - timedelta(days=1))
        self.match("boundary", played_at=self.cutoff)
        self.match("new")
        report = self.report()
        self.assertEqual(report["eligible_new_ranked_matches"], 1)
        self.assertEqual(report["new_api_matches"], 1)
        self.assertFalse(report["holdout_evaluated"])
        self.assertEqual(report["promotion"], "NOT_ASSESSED")

    def test_trophies_and_synthetic_or_unverified_sources_are_not_ranked_evidence(self):
        self.match("trophies", battle_type="ranked")
        self.match("synthetic", source="synthetic")
        self.match("fixture", source="fixture")
        self.match("not-ranked", is_ranked=False)
        report = self.report()
        self.assertEqual(report["new_api_matches"], 2)
        self.assertEqual(report["eligible_new_ranked_matches"], 0)
        self.assertEqual(report["status"], "DATA_UNAVAILABLE")

    def test_incomplete_unknown_extra_players_and_conflicts_are_excluded(self):
        self.match("conflict", has_conflict=True)
        self.match("unknown-result", winner_side="")
        incomplete = self.match("incomplete")
        incomplete.players.first().delete()
        unknown = self.match("unknown-brawler")
        unknown.players.filter(side="a").update(brawler=None)
        extra = self.match("extra")
        MatchPlayer.objects.create(match=extra, side="a", brawler_name="unknown")
        report = self.report()
        self.assertEqual(report["eligible_new_ranked_matches"], 0)
        self.assertEqual(report["excluded"], {"not_complete_known_3v3": 3, "unknown_or_conflict_result": 2})

    def test_duplicate_sightings_do_not_multiply_samples_and_unknown_stays_unknown(self):
        match = self.match("observed")
        for index in range(2):
            payload = RawPayload.objects.create(source="api", format="test-only",
                content_hash=str(index), payload={}, sampling="broad_high_rank")
            match.payloads.add(payload)
        self.match("without-provenance")
        report = self.report()
        self.assertEqual(report["eligible_new_ranked_matches"], 2)
        self.assertEqual(report["sampling_match_counts"], {"UNKNOWN": 1, "broad_high_rank": 1})

    def test_command_only_reads_and_does_not_expose_collector_payload_or_error(self):
        self.match("test")
        CollectorRun.objects.create(abort_reason="private-error-marker",
            parameters={"spieler_tags": ["private-tag-marker"]},
            report={"neu": 1, "private_payload": "private-payload-marker"})
        with CaptureQueriesContext(connection) as queries:
            report = self.report()
        for query in queries:
            sql = query["sql"].lstrip().upper()
            # PostgreSQL iterator() uses a named cursor around a SELECT.
            self.assertTrue(sql.startswith("SELECT") or (
                sql.startswith("DECLARE") and " FOR SELECT " in sql
            ), sql)
        serialized = json.dumps(report)
        for marker in ("private-error-marker", "private-tag-marker", "private-payload-marker"):
            self.assertNotIn(marker, serialized)
        self.assertIsNone(report["recent_collector_runs"][0]["counts"]["duplikate"])

    def test_requires_explicit_timezone(self):
        for value in ("bad", "2026-09-18", "2026-09-18T15:04:42", "2026-15-18T15:04:42Z"):
            with self.subTest(value=value), self.assertRaises(CommandError):
                call_command("drafter_v2_growth", after=value, stdout=io.StringIO())

    def test_empty_inventory_has_no_invented_latest_time(self):
        report = self.report()
        self.assertIsNone(report["latest_api_ranked_at"])
        self.assertEqual(report["eligible_range"], {"first": None, "last": None})
        self.assertEqual(report["sampling_match_counts"], {})
