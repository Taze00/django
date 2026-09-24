"""One preregistered acquisition feasibility pilot, never a test-window run."""
import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from drafter.services.discovery_frontier import DiscoveryFrontierCollector


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--protocol", required=True)
        parser.add_argument("--expected-sha256", required=True)
        parser.add_argument("--code-revision", required=True)

    def handle(self, *args, **options):
        raw = Path(options["protocol"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != options["expected_sha256"]:
            raise CommandError("Pilot protocol hash mismatch")
        protocol = json.loads(raw)
        if (protocol["schema"] != "discovery-pilot-1" or protocol["purpose"] != "pre_registration_development_pilot"
                or protocol["future_test_eligible"] is not False
                or parse_datetime(protocol["preregistered_at"]) >= timezone.now()):
            raise CommandError("Invalid preregistration")
        for name, expected in protocol["implementation_sha256"].items():
            if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
                raise CommandError("Acquisition implementation differs from preregistration")
        try:
            collector = DiscoveryFrontierCollector(after=parse_datetime(protocol["after_exclusive"]),
                source_payloads=protocol["source_payloads"], pilot_id=protocol["pilot_id"],
                protocol_hash=options["expected_sha256"], max_battlelogs=protocol["max_http_attempts"],
                max_depth=protocol["max_depth"], code_revision=options["code_revision"])
            report = collector.execute()
        except ValueError as error:
            raise CommandError(str(error)) from None
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        if report["abbruch"]:
            raise CommandError(report["abbruch"])
