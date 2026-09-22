import io
import json

from django.core.management import call_command

from drafter.tests.basis import DrafterTest


class V2FreezeContractTest(DrafterTest):
    def test_freeze_manifest_ist_deterministisch_und_read_only(self):
        first = io.StringIO()
        second = io.StringIO()
        call_command("drafter_v2_freeze", format="json", git_commit="test", stdout=first)
        call_command("drafter_v2_freeze", format="json", git_commit="test", stdout=second)
        one = json.loads(first.getvalue())
        two = json.loads(second.getvalue())
        self.assertEqual(one["fingerprint_sha256"], two["fingerprint_sha256"])
        self.assertEqual(one["counts"], two["counts"])
        self.assertEqual(one["git_commit"], "test")