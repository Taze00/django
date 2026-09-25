"""Forward-development temporal gate, using no real examples or quality metrics."""
from datetime import datetime, timezone
from unittest.mock import patch
from django.test import SimpleTestCase
from drafter.services.development_forward import forward_check


class ForwardDevelopmentTests(SimpleTestCase):
    def test_before_close_blocks_before_reading_candidates_or_database(self):
        protocol={'schema':'development-forward-confirmation-1',
            'start_inclusive':'2026-09-26T00:00:00Z','end_exclusive':'2026-09-28T00:00:00Z'}
        with patch('drafter.services.development_forward.timezone.now',return_value=datetime(2026,9,27,tzinfo=timezone.utc)):
            with self.assertRaisesRegex(ValueError,'has not closed'):
                forward_check(protocol,'synthetic')

    def test_invalid_interval_fails_closed(self):
        protocol={'schema':'development-forward-confirmation-1',
            'start_inclusive':'2026-09-28T00:00:00Z','end_exclusive':'2026-09-26T00:00:00Z'}
        with self.assertRaisesRegex(ValueError,'Invalid fixed'):
            forward_check(protocol,'synthetic')

    def test_candidate_hash_mismatch_blocks_database_and_scoring(self):
        protocol={'schema':'development-forward-confirmation-1',
            'start_inclusive':'2026-09-26T00:00:00Z','end_exclusive':'2026-09-28T00:00:00Z',
            'candidate_archive':'synthetic','candidate_archive_sha256':'invalid'}
        with patch('drafter.services.development_forward.timezone.now',return_value=datetime(2026,9,29,tzinfo=timezone.utc)),patch('drafter.services.development_forward.Path.read_bytes',return_value=b'changed'):
            with self.assertRaisesRegex(ValueError,'candidates changed'):
                forward_check(protocol,'synthetic')
