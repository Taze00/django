"""Train the opt-in Challenger from verified development partitions only."""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from drafter.services.v2_challenger_training import build_artifact, development_partitions, digest


class Command(BaseCommand):
    help = 'Train experimental V2 on verified historical Train/Validation only; no holdout evaluation'

    def add_arguments(self, parser):
        parser.add_argument('--output', required=True)
        parser.add_argument('--revision', required=True)

    def handle(self, *args, **options):
        path = Path(options['output'])
        if path.exists():
            raise CommandError('Output already exists; preserve the previous artifact')
        try:
            with transaction.atomic():
                if connection.vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
                train, validation = development_partitions()
                artifact = build_artifact(train, validation, options['revision'])
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x') as stream:
                json.dump(artifact, stream, sort_keys=True, indent=2)
        except (ValueError, OSError) as error:
            raise CommandError(str(error)) from error
        report = {key: artifact[key] for key in ('schema', 'status', 'validation', 'limitations')}
        report['artifact_sha256'] = digest(artifact)
        report['provenance'] = {**artifact['provenance'], **{
            name: {k: v for k, v in artifact['provenance'][name].items() if k != 'fingerprints'}
            for name in ('train', 'validation')}}
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
