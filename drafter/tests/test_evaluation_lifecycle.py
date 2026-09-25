import json
from django.test import SimpleTestCase
from drafter.services.evaluation_lifecycle import ABORT_FILE, development_origin
from drafter.services.v2_future_window import validate


class EvaluationLifecycleTests(SimpleTestCase):
    def test_actual_aborted_registration_fails_closed(self):
        protocol=json.loads((ABORT_FILE.parent/'PROSPECTIVE_WINDOW.json').read_text())
        with self.assertRaisesRegex(ValueError,'ABORTED_FOR_DEVELOPMENT'):
            validate(protocol)

    def test_development_origins_never_become_final_test(self):
        aborted=json.loads(ABORT_FILE.read_text())['protocol_sha256']
        for row in ({'sampling':'observed_discovery_pilot_v1'},
                    {'sampling':'ranked_development_v1'},
                    {'sampling':'prospective_discovery_v1','protocol_sha256':aborted}):
            self.assertTrue(development_origin(row))
        self.assertFalse(development_origin({'sampling':'prospective_discovery_v1','protocol_sha256':'future-other'}))
