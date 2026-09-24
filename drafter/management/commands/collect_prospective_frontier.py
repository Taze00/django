"""One bounded prospective run; never schedules or repeats itself."""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from drafter.services.prospective_acquisition import ProspectiveCollector, verify_files, verify_catalog
from drafter.services.v2_future_window import digest, validate


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--protocol', required=True)
        parser.add_argument('--expected-protocol-sha256', required=True)

    def handle(self, *args, **options):
        try:
            protocol = json.loads(Path(options['protocol']).read_text())
            validate(protocol)
            if digest(protocol) != options['expected_protocol_sha256']:
                raise ValueError('Prospective protocol hash mismatch')
            verify_files(protocol)
            verify_catalog(protocol)
            report = ProspectiveCollector(protocol=protocol).execute()
        except (ValueError, KeyError, TypeError, OSError) as error:
            raise CommandError(str(error)) from None
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        if report['abbruch']:
            raise CommandError(report['abbruch'])
