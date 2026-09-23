"""Bounded, preregistered development-only opponent interaction experiment."""
import json
import hashlib
from collections import Counter
from pathlib import Path
from time import perf_counter
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from drafter.services.v2_challenger_training import build_artifact, development_partitions, digest
from drafter.services.v2_model import OPPONENT_VERSION, _feature_counts, train_model, evaluate_model
from drafter.services.evaluation import metrics


class Command(BaseCommand):
    help = 'Compare the fixed D-013 candidates on Train/Validation only, never holdout'

    def add_arguments(self, parser):
        parser.add_argument('--output', required=True)
        parser.add_argument('--revision', required=True)

    def handle(self, *args, **options):
        path = Path(options['output'])
        if path.exists():
            raise CommandError('Output exists; preserve previous experiment')
        try:
            with transaction.atomic():
                if connection.vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
                train, validation = development_partitions()
                started = perf_counter()
                artifact = build_artifact(train, validation, options['revision'])
                baseline_time = perf_counter() - started
            baseline = artifact['validation']
            results = [{'version': artifact['model']['feature_version'], 'l2': 1,
                        'training_seconds': baseline_time, 'validation': baseline},
                       {'version': 'B0', 'validation': metrics(lambda row: 0.5, validation)}]
            best_loss = baseline['log_loss']
            selected = None
            for l2 in (1.0, 10.0, 100.0):
                started = perf_counter()
                model = train_model(train, regularization=l2, epochs=300, feature_version=OPPONENT_VERSION)
                training_seconds = perf_counter() - started
                started = perf_counter()
                score = evaluate_model(model, validation)
                results.append({'version': OPPONENT_VERSION, 'l2': l2, 'training_seconds': training_seconds,
                                'validation_seconds': perf_counter() - started, 'validation': score})
                if score['log_loss'] < best_loss and score['brier'] <= baseline['brier']:
                    best_loss, selected = score['log_loss'], model
            if selected is not None:
                artifact['model'] = selected.as_dict()
                support = Counter()
                for row in train:
                    support.update(set(_feature_counts(row, selected.feature_version)))
                artifact['feature_support'] = dict(support)
                artifact['validation'] = evaluate_model(selected, validation)
            artifact['experiment'] = {'protocol': 'D-013', 'candidates': results,
                                      'selected_version': artifact['model']['feature_version'],
                                      'selected_l2': artifact['model']['regularization'],
                                      'promotion': 'NOT_EVALUATED_NO_NEW_HOLDOUT'}
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x') as stream:
                json.dump(artifact, stream, indent=2, sort_keys=True)
        except (ValueError, OSError) as error:
            raise CommandError(str(error)) from error
        report = {'experiment': artifact['experiment'], 'artifact_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'canonical_content_sha256': digest(artifact),
                  'provenance': {**artifact['provenance'], **{
                      name: {k: v for k, v in artifact['provenance'][name].items() if k != 'fingerprints'}
                      for name in ('train', 'validation')}}}
        self.stdout.write(json.dumps(report, sort_keys=True, indent=2))
