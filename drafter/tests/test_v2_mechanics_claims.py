"""Archive safety and explanation contracts; no DB, network or game simulation."""
import json
import tempfile
import unittest
from pathlib import Path

from drafter.services.v2_mechanics_claims import archive, explanations, read_reviewed

CLAIMS = Path(__file__).resolve().parents[2] / 'docs/drafter-v2/MECHANICS_CURRENT_CLAIMS_2026-09-23.json'


class MechanicsClaimTests(unittest.TestCase):
    def test_exact_reviewed_annotations_survive_storage_and_repeat_import(self):
        with tempfile.TemporaryDirectory() as directory:
            target = archive(CLAIMS, directory)
            before = target.stat()
            self.assertEqual(archive(CLAIMS, directory), target)
            self.assertEqual(target.stat().st_ino, before.st_ino)
            self.assertEqual(target.read_bytes(), CLAIMS.read_bytes())
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_corrupt_existing_record_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = archive(CLAIMS, directory)
            target.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                archive(CLAIMS, directory)
            self.assertEqual(target.read_bytes(), b'corrupt')
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_changed_values_permissions_and_conditions_require_review(self):
        for field, value in [('value', 0), ('value', False), ('value', None),
                             ('requirements', []), ('historical_training_allowed', True),
                             ('observed_at', '2099-01-01T00:00:00Z')]:
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                document = json.loads(CLAIMS.read_bytes())
                document['claims'][0][field] = value
                path = Path(directory) / 'changed.json'
                path.write_text(json.dumps(document))
                with self.assertRaises(ValueError):
                    explanations(path)
                with self.assertRaises(ValueError):
                    archive(path, Path(directory) / 'archive')
                self.assertFalse((Path(directory) / 'archive').exists())

    def test_conditions_attribution_unknowns_and_usage_flags_are_preserved(self):
        originals = json.loads(CLAIMS.read_bytes())['claims']
        rendered = explanations(CLAIMS)
        self.assertEqual([item['claim'] for item in rendered], originals)
        for item in rendered:
            claim, text = item['claim'], item['text']
            for required in claim['requirements'] + claim['limitations']:
                self.assertIn(required, text)
            for key in ('source_url', 'source_section', 'source_sha256', 'observed_at'):
                self.assertIn(claim[key], text)
            self.assertIsNone(claim['valid_from'])
            self.assertIsNone(claim['valid_to'])
            self.assertIs(claim['numeric_inference_allowed'], False)
            self.assertIs(claim['historical_training_allowed'], False)
            self.assertEqual(item['current_validity'], 'UNKNOWN')
            self.assertIn('Equipped loadout and active effect: UNKNOWN', text)
            self.assertEqual(item['source_body_availability'], 'NOT_CHECKED')

    def test_current_numeric_and_historical_requests_fail_closed(self):
        for purpose in ('current', 'numeric', 'historical', '', None):
            with self.subTest(purpose=purpose), self.assertRaises(ValueError):
                explanations(CLAIMS, purpose=purpose)

    def test_missing_oversized_and_unreviewed_artifacts_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'claims.json'
            with self.assertRaises(FileNotFoundError):
                read_reviewed(path)
            for body in (b'{}', b'x' * 65537):
                path.write_bytes(body)
                with self.assertRaises(ValueError):
                    read_reviewed(path)

    def test_returned_annotations_cannot_mutate_future_reads(self):
        result = explanations(CLAIMS)
        result[0]['claim']['requirements'].clear()
        self.assertTrue(explanations(CLAIMS)[0]['claim']['requirements'])
