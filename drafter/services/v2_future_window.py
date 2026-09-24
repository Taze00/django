"""Future-only preregistration and membership, never model fitting or evaluation.

Pure contracts accept an admission inventory from the read-only DB adapter.
A digest detects changes; operational access controls still protect sealed data.
"""
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 'drafter-future-window-3'
OLD_END = datetime(2026, 9, 18, 15, 4, 42, tzinfo=timezone.utc)
POLICY = {
    'source': 'api', 'battle_type': 'soloRanked', 'sampling': 'prospective_discovery_v1',
    'shadow_eligible': False, 'training_eligible': False, 'tuning_on_test': False,
    'metrics': ['log_loss', 'brier', 'calibration_10_equal_width_bins'],
    'ranking': 'descriptive_only_when_actual_order_bans_and_choice_observed',
    'minimum_matches': 1000, 'minimum_interpretation': 'operational_floor_not_power_guarantee',
    'legacy_prediction': 'frozen_DraftEngine.siegchance_complete_3v3',
    'v2_prediction': 'frozen_complete_3v3_not_hypothetical_search',
    'comparison': 'paired_common_eligible_matches_report_all_exclusions',
    'late_arrivals': 'exclude_after_seal_no_replacement',
    'acquisition_pilot_eligible': False,
}


ACQUISITION = {
    'strategy': 'prospective_discovery_v1', 'ranking_requests': 0,
    'max_http_attempts_per_run': 10, 'max_depth': 1, 'cooldown_hours': 6,
    'max_runs': 56, 'max_window_http_attempts': 560, 'recurring_collector': False,
    'selection': 'due_active; last_fetched ASC NULLS FIRST; discovery_first_seen ASC; tag ASC',
    'sampling_bias': 'graph_discovered_not_independent_no_sampling_weights',
    'raw_retention': 'retain_all_no_deletion', 'automatic_training': False,
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.utcoffset() is None:
        raise ValueError('Timestamp needs explicit timezone')
    return parsed.astimezone(timezone.utc)


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def validate(protocol):
    if protocol.get('schema') != SCHEMA or protocol.get('policy') != POLICY:
        raise ValueError('Unsupported future protocol/policy')
    if not all(_sha(protocol.get(key)) for key in ('v2_artifact_sha256', 'legacy_bundle_sha256', 'development_membership_sha256')):
        raise ValueError('Frozen model, Legacy input bundle and development membership hashes required')
    if not isinstance(protocol.get('code_revision'), str) or not protocol['code_revision'].strip() or protocol['code_revision'] == 'UNKNOWN':
        raise ValueError('Code revision required')
    receipt=protocol.get('legacy_verification', {})
    if (receipt.get('schema')!='legacy-bundle-verification-1' or receipt.get('status')!='VERIFIED'
            or receipt.get('bundle_sha256')!=protocol['legacy_bundle_sha256']
            or receipt.get('policy')!='train_empirical_frozen_manual_constants_v1'
            or receipt.get('required_unknown_inputs')!=[]
            or any(receipt.get('checks',{}).get(key) is not True for key in
                   ('independent_rebuild','independent_raw_counts','prior_identity','train_membership','scoring_replay'))):
        raise ValueError('Verified Legacy bundle receipt required')
    registered, development, start, end = (timestamp(protocol[k]) for k in ('registered_at','development_end','start_exclusive','end_inclusive'))
    if timestamp(receipt['frozen_at'])>registered:
        raise ValueError('Legacy inputs must be frozen before registration')
    if not (development <= registered < start < end and start > OLD_END):
        raise ValueError('Future window must follow registration and all development data')
    acquisition = protocol.get('acquisition', {})
    if acquisition.get('policy') != ACQUISITION:
        raise ValueError('Frozen bounded acquisition policy required')
    if (not _sha(acquisition.get('pilot_result_sha256'))
            or acquisition.get('pilot_new_eligible', 0) <= 0
            or not timestamp(acquisition['pilot_finished_at']) <= registered
            or not acquisition.get('implementation_sha256')
            or not all(_sha(v) for v in acquisition['implementation_sha256'].values())):
        raise ValueError('Verified completed acquisition feasibility and implementation required')
    common = protocol.get('common_context', {})
    if (common.get('patch_policy') != 'frozen_algorithmic_context_not_observed_game_patch'
            or common.get('legacy_patch_id') != 1 or common.get('allowed_import_patch_ids') != [1]
            or not common.get('map_mode_pairs') or not common.get('brawler_ids')
            or not _sha(common.get('catalog_identity_sha256'))):
        raise ValueError('Exact common context and explicit frozen patch convention required')
    if protocol.get('legacy_input_policy') != 'train_empirical_frozen_manual_constants_v1':
        raise ValueError('Legacy bundle requires Train-only empirical inputs and frozen manual constants')


def register(*, now, development_end, start, end, v2_hash, legacy_hash, development_hash, revision, legacy_verification, acquisition, common_context):
    value = {'acquisition': acquisition, 'common_context': common_context, 'schema': SCHEMA, 'policy': POLICY.copy(), 'legacy_verification': legacy_verification, 'registered_at': now.isoformat(),
             'development_end': development_end, 'start_exclusive': start, 'end_inclusive': end,
             'v2_artifact_sha256': v2_hash, 'legacy_bundle_sha256': legacy_hash,
             'development_membership_sha256': development_hash, 'code_revision': revision,
             'legacy_input_policy': 'train_empirical_frozen_manual_constants_v1'}
    validate(value)
    return value


def seal(protocol, inventory, now):
    validate(protocol)
    start, end = timestamp(protocol['start_exclusive']), timestamp(protocol['end_inclusive'])
    if now <= end:
        raise ValueError('Window still open; cannot seal or peek at metrics')
    seen, reconstructed, members, excluded = set(), set(), [], {}
    def reject(reason):
        excluded[reason] = excluded.get(reason, 0) + 1
    for row in sorted(inventory, key=lambda r: (r['played_at'], r['fingerprint'])):
        at = timestamp(row['played_at'])
        if not start < at <= end:
            raise ValueError('Inventory outside preregistered window')
        if row.get('source') != 'api' or row.get('battle_type') != 'soloRanked' or not row.get('is_ranked'):
            reject('not_official_soloRanked'); continue
        if row.get('has_conflict') or not row.get('result_known'):
            reject('unknown_or_conflicting_result'); continue
        if not row.get('complete_unique_3v3') or not row.get('known_context'):
            reject('incomplete_duplicate_or_unknown_context'); continue
        common = protocol['common_context']
        if ([row.get('map_id'), row.get('mode_id')] not in common['map_mode_pairs']
                or any(b not in common['brawler_ids'] for b in row.get('brawler_ids', []))
                or len(row.get('brawler_ids', [])) != 6
                or row.get('patch_id') not in common['allowed_import_patch_ids']):
            reject('outside_frozen_common_context'); continue
        origins = row.get('origins', [])
        if any(o['sampling'] == 'observed_discovery_pilot_v1' for o in origins):
            reject('pre_registration_acquisition_pilot'); continue
        if not any(o['sampling'] == POLICY['sampling'] and o['source'] == 'api'
                   and o['format'] == 'brawlstars.battlelog.raw' and o['run_id'] is not None
                   and o.get('protocol_sha256') == digest(protocol)
                   and o.get('purpose') == 'prospective_test'
                   and o.get('code_revision') == protocol['code_revision']
                   and at <= timestamp(o['fetched_at']) <= now and _sha(o['content_hash']) for o in origins):
            reject('unverified_provenance'); continue
        fp, reconstructed_fp = row['fingerprint'], row.get('reconstructed_fingerprint')
        if not _sha(fp) or not _sha(reconstructed_fp) or not _sha(row.get('content_sha256')):
            reject('missing_fingerprint'); continue
        if fp in seen or reconstructed_fp in reconstructed:
            raise ValueError('Duplicate membership/fingerprint collision: resolve before sealing')
        seen.add(fp); reconstructed.add(reconstructed_fp)
        members.append(row)
    if len(members) < POLICY['minimum_matches']:
        raise ValueError(f"Insufficient independent observations: {len(members)}; no seal")
    return {'schema': 'drafter-future-membership-1', 'protocol_sha256': digest(protocol),
            'sealed_at': now.isoformat(), 'members': members, 'membership_sha256': digest(members),
            'excluded': excluded, 'n': len(members), 'status': 'SEALED_NOT_EVALUATED',
            'training_eligible': False}


def publish(path, value):
    """Complete atomic create, never replace an existing registration or seal."""
    path = Path(path)
    body = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    fd, temp = tempfile.mkstemp(prefix='.future-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(body); stream.flush(); os.fsync(stream.fileno())
        os.link(temp, path)
    finally:
        os.unlink(temp)


def verify_membership(protocol, membership, inventory):
    validate(protocol)
    if (membership.get('schema') != 'drafter-future-membership-1'
            or membership.get('status') != 'SEALED_NOT_EVALUATED'
            or membership.get('n') != len(membership.get('members', []))):
        raise ValueError('Invalid sealed membership contract')
    if membership.get('protocol_sha256') != digest(protocol) or membership.get('membership_sha256') != digest(membership['members']):
        raise ValueError('Sealed manifest integrity mismatch')
    current = {r['fingerprint']: r for r in inventory}
    for row in membership['members']:
        # Additional provenance sightings after seal do not revise membership.
        observed = current.get(row['fingerprint'])
        if observed is None or any(observed.get(k) != v for k,v in row.items() if k != 'origins'):
            raise ValueError('Sealed match content/eligibility changed')
        if any(o['sampling'] == 'observed_discovery_pilot_v1' for o in observed['origins']):
            raise ValueError('Acquisition pilot observation cannot enter prospective membership')
        if not all(origin in observed['origins'] for origin in row['origins']):
            raise ValueError('Sealed source provenance changed')
    return {'status': 'VERIFIED_NOT_EVALUATED', 'n': len(membership['members']),
            'late_arrivals_ignored': len(set(current) - {r['fingerprint'] for r in membership['members']})}
