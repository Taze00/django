import io
import json

from django.core.management import call_command

from drafter.tests.basis import DrafterTest


class DrafterV2AuditTest(DrafterTest):
    def test_audit_ist_read_onlyes_json(self):
        vorher = {
            "brawler": self.brawler("gale").pk,
            "praxisfaelle": 0,
        }
        ausgabe = io.StringIO()
        call_command("drafter_v2_audit", format="json", stdout=ausgabe)
        bericht = json.loads(ausgabe.getvalue())

        self.assertTrue(bericht["audit"]["read_only"])
        self.assertEqual(bericht["counts"]["raw_payloads"], 0)
        self.assertEqual(bericht["counts"]["matches"], 0)
        self.assertEqual(bericht["counts"]["praxisfaelle"], vorher["praxisfaelle"])
        self.assertEqual(self.brawler("gale").pk, vorher["brawler"])