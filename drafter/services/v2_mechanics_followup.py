"""Offline bounded source-structure audit; no effect execution or patch application."""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, deque
from pathlib import Path

NEW_TABLES = ('status_effects_logic', 'components_logic', 'buddies', 'roguelite_cards',
              'roguelite_decks', 'traits', 'gear_boosts', 'globals', 'actions', 'conditions')
OLD_TABLES = ('characters', 'skills', 'cards', 'accessories', 'projectiles', 'areas')
# Column-name links only. No numeric engine codes, expression evaluation or formulas.
LINKS = {
    'characters': {'Traits': 'traits', 'Components': 'components_logic', 'WeaponSkill': 'skills', 'UltimateSkill': 'skills'},
    'cards': {'Traits': 'traits', 'Components': 'components_logic', 'StatusEffect': 'status_effects_logic', 'Buddies': 'buddies', 'RogueliteDeck': 'roguelite_decks'},
    'skills': {'SummonedCharacters': 'characters', 'Projectiles': 'projectiles', 'ActivationSelfStatusEffects': 'status_effects_logic', 'AreaEffectObject': 'areas'},
    'accessories': {'Skill': 'skills', 'StatusEffectAlly': 'status_effects_logic', 'StatusEffectEnemy': 'status_effects_logic', 'StatusEffectSelf': 'status_effects_logic', 'AreaEffect': 'areas'},
    'projectiles': {'StatusEffectEnemy': 'status_effects_logic', 'StatusEffectAlly': 'status_effects_logic', 'OnEnemyHitActions': 'actions'},
    'areas': {'StatusEffectEnemy': 'status_effects_logic', 'ActionsEnemy': 'actions'},
    'buddies': {'Accessory': 'accessories', 'Traits': 'traits', 'Components': 'components_logic'},
    'roguelite_decks': {'RogueliteCard' + str(n): 'roguelite_cards' for n in range(1, 26)},
    'roguelite_cards': {'Traits': 'traits'},
    'traits': {'StatusEffect': 'status_effects_logic', 'Components': 'components_logic', 'Actions': 'actions', 'AreaEffect': 'areas', 'Skill': 'skills', 'Character': 'characters', 'Projectile': 'projectiles'},
    'gear_boosts': {'StatusEffect': 'status_effects_logic'},
    'components_logic': {'StatusEffects': 'status_effects_logic', 'StatusEffectsOvercharged': 'status_effects_logic', 'Traits': 'traits', 'TraitsOvercharged': 'traits', 'AreaEffects': 'areas', 'Skills': 'skills', 'Characters': 'characters', 'Projectiles': 'projectiles'},
    'status_effects_logic': {'ChainStatusEffect': 'status_effects_logic', 'ChainStatusEffect2': 'status_effects_logic', 'StatusToApplyOnEnd': 'status_effects_logic', 'Traits': 'traits', 'Components': 'components_logic', 'ActionsOnTrigger': 'actions', 'ActionsOnCancelOnDamage': 'actions'},
    'actions': {'Conditions': 'conditions', 'StatusEffects': 'status_effects_logic', 'AreaEffects': 'areas', 'Projectiles': 'projectiles', 'Characters': 'characters', 'Skills': 'skills'},
    'conditions': {},
}
ROOTS = (
    ('cards', 'ShotgunGirl_Dash', 'gadget'),
    ('cards', 'ShotgunGirl_unique', 'star_power'),
    ('cards', 'ShotgunGirl_overcharge', 'hypercharge'),
    ('cards', 'ShotgunGirl_Buddy_Gadgets', 'buffy/gadget'),
    ('cards', 'ShotgunGirl_Buddy_Starpowers', 'buffy/star_power'),
    ('cards', 'ShotgunGirl_Buddy_Overcharge', 'buffy/hypercharge'),
    ('cards', 'nano_shelly_deck', 'mode/nanopower'),
    ('skills', 'MechanicUlti', 'super/summon'),
    ('skills', 'MechaDudeUlti', 'super/transformation'),
    ('actions', 'MenderUltiFearAction', 'super/target_condition'),
    ('characters', 'Rock', 'quarantined_identity_probe'),
    ('gear_boosts', 'ForestSpeed', 'equipped_gear/activation_unknown'),
)


def read_records(body):
    """Preserve physical continuation rows; do not collapse arrays or fill blanks."""
    rows = list(csv.reader(io.StringIO(body.decode('utf-8-sig'))))
    if len(rows) < 2 or rows[0][0] != 'Name' or len(set(rows[0])) != len(rows[0]) or len(rows[1]) != len(rows[0]):
        raise ValueError('Invalid header/type rows')
    header, records, current = rows[0], {}, None
    for ordinal, row in enumerate(rows[2:], 3):
        if len(row) != len(header):
            raise ValueError('CSV width mismatch')
        if row[0]:
            if row[0] in records:
                raise ValueError('Duplicate named record')
            current = {'fields': {}, 'physical_records': []}
            records[row[0]] = current
        if current is None:
            raise ValueError('Orphan continuation row')
        current['physical_records'].append(ordinal)
        for key, value in zip(header, row):
            if value != '':
                current['fields'].setdefault(key, []).append({'record': ordinal, 'value': value})
    return {'physical_rows': len(rows) - 2, 'named_records': len(records),
            'continuation_rows': len(rows) - 2 - len(records), 'records': records}


def values(record, field):
    return [cell['value'] for cell in record['fields'].get(field, [])]


def walk(tables, root, max_depth=6, max_nodes=400):
    queue = deque([(root[0], root[1], 0)])
    seen, nodes, edges, missing = set(), [], [], []
    while queue:
        table, name, depth = queue.popleft()
        if (table, name) in seen:
            continue
        if len(seen) >= max_nodes:
            missing.append({'reason': 'node_limit', 'target': [table, name]})
            break
        seen.add((table, name))
        record = tables.get(table, {}).get('records', {}).get(name)
        if record is None:
            missing.append({'reason': 'missing_reference', 'target': [table, name]})
            continue
        nodes.append({'table': table, 'name': name, **record})
        links = dict(LINKS.get(table, {}))
        if table == 'cards' and values(record, 'Type') == ['accessory']:
            links['Skill'] = 'accessories'
        for field, target in links.items():
            for cell in record['fields'].get(field, []):
                for ref in filter(None, cell['value'].split(';')):
                    edge = {'from': [table, name, field, cell['record']], 'to': [target, ref],
                            'explicit_overcharged_column': 'Overcharged' in field}
                    edges.append(edge)
                    if depth == max_depth:
                        missing.append({'reason': 'depth_limit', 'target': [target, ref]})
                    else:
                        queue.append((target, ref, depth + 1))
    return {'root': list(root), 'max_depth': max_depth, 'max_nodes': max_nodes,
            'nodes': nodes, 'edges': edges, 'unresolved': missing,
            'effect_semantics': 'UNKNOWN', 'scope_inheritance': 'ROOT_AND_EDGE_PATH_REQUIRED'}


def checked(directory, record):
    body = (Path(directory) / record['name']).read_bytes()
    if hashlib.sha256(body).hexdigest() != record['sha256']:
        raise ValueError('Hash mismatch: ' + record['name'])
    return body


def kit_conflicts(metadata, cards, expected_target):
    by_id = {23000000 + i: r for i, r in enumerate(cards['records'].values())}
    conflicts = []
    for gadget in metadata['gadgets']:
        record = by_id.get(gadget['id'])
        observed = values(record, 'Target') if record else []
        if observed != [expected_target]:
            conflicts.append({'id': gadget['id'], 'observed_targets': observed,
                              'expected_target': expected_target})
    return conflicts


def report(new_dir, old_dir, manifest_path, baseline_path):
    manifest = json.loads(Path(manifest_path).read_text())
    metadata = json.loads(checked(Path(manifest_path).parent, {
        'name': 'MECHANICS_FOLLOWUP_METADATA_2026-09-23.json', 'sha256': manifest['metadata_sha256']}))
    old = {r['name']: r for r in json.loads(Path(baseline_path).read_text())['requests']}
    new = {r['name']: r for r in manifest['requests']}
    tables = {t: read_records(checked(new_dir, new[t + '.csv'])) for t in NEW_TABLES}
    tables.update({t: read_records(checked(old_dir, old['archive-' + t + '.csv'])) for t in OLD_TABLES})
    previous_cards = read_records(checked(new_dir, new['previous-cards.csv']))
    previous_characters = read_records(checked(old_dir, old['archive-previous-characters.csv']))
    identity_history = {}
    for build, chars, cards in (('68.250', previous_characters, previous_cards),
                                ('69.230', tables['characters'], tables['cards'])):
        # This is the provider's claimed row-ID convention, not a newly assigned official ID.
        identity_history[build] = {
            'characters': [{'source_row_id_claim': 16000000 + i, 'name': n,
                            'tid': values(r, 'TID')} for i, (n, r) in enumerate(chars['records'].items()) if n in ('Rock', 'RocketGirl')],
            'cards': [{'source_row_id_claim': 23000000 + i, 'name': n,
                       'target': values(r, 'Target')} for i, (n, r) in enumerate(cards['records'].items()) if n in ('RocketGirl_Jump', 'RocketGirl_MegaRocket', 'Rock_gadget', 'Rock_gadget_1')]}
    text_rows = list(csv.reader(io.StringIO(checked(new_dir, new['texts.csv']).decode())))
    translations = {r[0]: r[1] for r in text_rows[2:] if r[0] in ('TID_ROCK', 'TID_ROCKET_GIRL')}
    bolt = metadata['bolt']
    fingerprint = json.loads(checked(new_dir, new['fingerprint.json']))
    conflicts = kit_conflicts(bolt, tables['cards'], 'Rock')
    return {'schema': 'drafter-mechanics-followup-1', 'baseline_commit': '33c570c',
            'fetch_status_counts': dict(Counter(str(r.get('status')) for r in manifest['requests'])),
            'wire_http_exchange_count': None, 'observed_redirected_fetches': manifest['observed_redirected_fetches'],
            'response_bytes': sum(r.get('bytes', 0) for r in manifest['requests']),
            'new_table_shapes': {t: {k: v for k, v in tables[t].items() if k != 'records'} for t in NEW_TABLES},
            'archive_head': metadata['archive_head'],
            'archive_folder': '69.230', 'fingerprint_version': fingerprint['version'],
            'fingerprint_sha_claim': fingerprint['sha'],
            'public_conditions_metadata': metadata['conditions_response']['metadata'],
            'identity_history': identity_history, 'identity_translations': translations,
            'bolt_public_gadget_ids': [g['id'] for g in bolt['gadgets']],
            'bolt_status': 'CONFLICT' if conflicts else 'PARTIAL', 'bolt_conflicts': conflicts,
            'named_component_parameter_records': sum(bool(values(r, 'ValueNames')) for r in tables['components_logic']['records'].values()),
            'graphs': [walk(tables, r) for r in ROOTS],
            'current_explanation_gate': 'CONDITIONAL_ALLOWLIST_ONLY',
            'computed_current_mechanics_gate': 'NOT_PASSED', 'historical_training_gate': 'NOT_PASSED',
            'patch_applied': False, 'historical_join_enabled': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('new-dir', 'old-dir', 'manifest', 'baseline'):
        parser.add_argument('--' + arg, required=True)
    args = parser.parse_args()
    print(json.dumps(report(args.new_dir, args.old_dir, args.manifest, args.baseline), indent=2))


if __name__ == '__main__':
    main()
