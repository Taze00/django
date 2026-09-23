"""Recover the known development partitions without loading holdout examples."""
import hashlib
import json
from collections import Counter

from django.db.models import Count, Q

from drafter.models import Brawler
from drafter.models.matches import Match
from drafter.services.evaluation import examples_from_queryset
from drafter.services.v2_model import _feature_counts, evaluate_model, train_model

FREEZE_DIGEST = '2bb8222b9025a5da7daadea8b9a252c39b16bcda8b07b9bc2df69315ea4dcf9e'
CUTOFF = '2026-09-18T15:04:42Z'
TRAIN_N, VALIDATION_N, TOTAL_N = 6094, 2031, 10158
TRAIN_DIGEST = '5e8ff094ad9f93ed565bcaed9f725ffd7d78dd67c22e31c7b6aaed6cd2cec447'
VALIDATION_DIGEST = '4b2806db07d35e20dd8a0e6e76bef74dd928706b90e6615a3b2f64776c3df797'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def example_digest(rows):
    return digest([{'fingerprint': r.fingerprint, 'played_at': r.played_at.isoformat(),
                    'mode': r.mode, 'map_name': r.map_name, 'team_a': r.team_a,
                    'team_b': r.team_b, 'label': r.label} for r in rows])


def development_partitions():
    # Reproduce the original structural eligibility, including duplicate Brawlers.
    # No winner value, team identity or model feature is selected for holdout rows.
    eligible = Match.objects.filter(
        is_ranked=True, battle_type='soloRanked', has_conflict=False,
        winner_side__in=('a', 'b'), played_at__lte=CUTOFF,
    ).annotate(
        count_a=Count('players', filter=Q(players__side='a', players__brawler_id__isnull=False)),
        count_b=Count('players', filter=Q(players__side='b', players__brawler_id__isnull=False)),
    ).filter(count_a=3, count_b=3)
    membership = list(eligible.order_by('played_at', 'fingerprint').values_list('fingerprint', flat=True))
    actual = hashlib.sha256('\n'.join(membership).encode()).hexdigest()
    if len(membership) != TOTAL_N or actual != FREEZE_DIGEST:
        raise ValueError('Frozen membership mismatch; development recovery blocked')
    train_keys = membership[:TRAIN_N]
    validation_keys = membership[TRAIN_N:TRAIN_N + VALIDATION_N]
    train, skipped_train = examples_from_queryset(Match.objects.filter(fingerprint__in=train_keys))
    validation, skipped_validation = examples_from_queryset(Match.objects.filter(fingerprint__in=validation_keys))
    if skipped_train or skipped_validation or len(train) != TRAIN_N or len(validation) != VALIDATION_N:
        raise ValueError('Development partition changed after membership verification')
    if train[-1].played_at > validation[0].played_at:
        raise ValueError('Development time ordering violated')
    if example_digest(train) != TRAIN_DIGEST or example_digest(validation) != VALIDATION_DIGEST:
        raise ValueError('Frozen development content mismatch; training blocked')
    return train, validation


def build_artifact(train, validation, revision):
    model = train_model(train, regularization=1.0, epochs=300)
    if model is None or not validation:
        raise ValueError('Train/Validation data unavailable')
    support = Counter()
    for row in train:
        support.update(set(_feature_counts(row)))
    keys = [row.fingerprint for row in train]
    contexts = {}
    for slug, mode, map_name in Match.objects.filter(fingerprint__in=keys).exclude(
        brawl_map__isnull=True,
    ).values_list('brawl_map__slug', 'mode_name', 'map_name').distinct():
        value = {'mode': mode, 'map_name': map_name}
        if not mode or not map_name or (slug in contexts and contexts[slug] != value):
            raise ValueError('Ambiguous training map context')
        contexts[slug] = value
    def partition(rows):
        return {'n': len(rows), 'fingerprints': [r.fingerprint for r in rows],
                'examples_sha256': example_digest(rows), 'first': rows[0].played_at.isoformat(),
                'last': rows[-1].played_at.isoformat()}
    return {
        'schema': 'drafter-v2-challenger-1', 'status': 'EXPERIMENTAL_NOT_PROMOTED',
        'model': model.as_dict(), 'feature_support': dict(support),
        'catalog': dict(Brawler.objects.values_list('slug', 'id')),
        'contexts': contexts,
        'provenance': {'revision': revision, 'freeze_sha256': FREEZE_DIGEST,
                       'train': partition(train), 'validation': partition(validation),
                       'holdout_access': 'membership_digest_only_no_examples_or_predictions'},
        'validation': evaluate_model(model, validation),
        'limitations': ['Current patch applicability UNKNOWN', 'Skill/builds UNKNOWN',
                        'No calibrated uncertainty interval', 'No independent promotion evidence'],
    }
