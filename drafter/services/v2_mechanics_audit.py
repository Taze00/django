"""Offline Phase-5A source inventory, NOT a mechanics engine or importer.

Only nonempty CSV cells and explicit references are counted. No units, engine
opcodes, patch dates, loadouts or negative capability claims are inferred.
CLI reads hash-pinned local probe files and writes its report to stdout only.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import deque
from pathlib import Path

TABLES = ('characters', 'skills', 'projectiles', 'areas', 'cards', 'accessories')
BUILD = '69.230'
REVISION = 'cc307ffd36678ac463cc2ca9373a08b0a2d2b0b7'
MAX_DEPTH = 4

# Candidate field slots, not complete definitions of the named mechanics.
# An empty rule deliberately leaves the field UNKNOWN.
RULES = {
    'base.hp': {'characters': 'Hitpoints'},
    'base.movement_speed': {'characters': 'Speed'},
    'attack.damage': {'skills': 'Damage'},
    'attack.projectile_count': {'skills': 'NumBulletsInOneAttack'},
    'attack.damage_instances': {'skills': 'MsBetweenAttacks ActiveTime MultiShot', 'projectiles': 'DamagesConstantlyTickDelay'},
    'attack.reload': {'skills': 'RechargeTime'},
    'attack.ammo': {'skills': 'MaxCharge'},
    'attack.range': {'skills': 'CastingRange MaxCastingRange'},
    'attack.projectile_speed': {'projectiles': 'Speed'},
    'attack.pierce': {'projectiles': 'PiercesCharacters'},
    'attack.splash_aoe': {'skills': 'AreaEffectObject AreaEffectObject2', 'projectiles': 'SpawnAreaEffectObject SpawnAreaEffectObject2'},
    'attack.bounce': {'projectiles': 'IsBouncing BouncePercent'},
    'attack.percentage_hp_damage': {'skills': 'PercentDamage'},
    'attack.scaling': {'skills': 'PercentDamage DamageModifier', 'projectiles': 'DamagePercentStart DamagePercentEnd DamageChangeStartPromille DamageChangeEndPromille'},
    'attack.shoots_over_walls': {'projectiles': 'Indirect'},
    'attack.wall_penetration': {'skills': 'MeleeAttackPiercesEnvironment', 'projectiles': 'PassesEnvironment PiercesEnvironment PiercesEnvironmentLikeButter'},
    'ability.damage': {'skills': 'Damage', 'areas': 'Damage'},
    'ability.healing': {'skills': 'HealSelfOnActivationPower', 'projectiles': 'LifeStealPercent HealOwnPercent', 'areas': 'LifeStealPercent MaxOverHeal'},
    'ability.shield': {'skills': 'ConsumableShieldValue', 'projectiles': 'ConsumableShield', 'accessories': 'ShieldPercent'},
    'ability.damage_reduction': {'characters': 'OverchargeShieldPercent', 'projectiles': 'DamageReduction'},
    'ability.slow': {},
    'ability.stun': {'projectiles': 'StunLengthMS', 'areas': 'StunTicks'},
    'ability.knockback': {'skills': 'ChargePushback', 'projectiles': 'PushbackStrength', 'areas': 'PushbackStrength'},
    'ability.pull': {'projectiles': 'GrapplesEnemy'},
    'ability.silence': {'projectiles': 'SilenceDurationMS'},
    'ability.root': {},
    'ability.dash': {},
    'ability.jump': {},
    'ability.teleport': {},
    'ability.wallbreak': {'areas': 'DestroysEnvironment'},
    'ability.wall_creation': {},
    'ability.bush_destruction': {'areas': 'DestroysOnlyBushes DestroysDecorations'},
    'ability.summons': {},
    'ability.transformations': {},
    'kit.gadgets': {},
    'kit.star_powers': {},
    'kit.hypercharge': {},
    'kit.nanopower': {},
    'kit.buffy': {},
    'kit.other': {},
    'condition.limited_uses': {},
    'condition.cooldown': {'skills': 'Cooldown BonusSkillCooldown', 'accessories': 'Cooldown'},
    'condition.activation': {'skills': 'RestrictCastOnSkillActive', 'accessories': 'RequirePetDistance RequireEnemyInRange ConsumesAmmo SkipTypeCondition'},
    'condition.duration': {'skills': 'ActiveTime ConsumableShieldTicks', 'areas': 'TimeMs MinTimeMs', 'accessories': 'ActiveTicks ShieldTicks'},
    'condition.radius_area': {'projectiles': 'Radius', 'areas': 'Radius InnerRadius', 'accessories': 'Range'},
    'condition.charges': {'skills': 'MaxCharge ChargedShotCount', 'characters': 'UltiUses'},
    'condition.repeatability': {},
}
# Text labels actually present in the bounded sources. Numeric opcodes are NOT decoded.
LABELS = {
    'ability.healing': {'skills': ('BehaviorType', {'Heal'}), 'areas': ('Type', {'Heal', 'HealAbsolute', 'HealAndDamage', 'HealRegen', 'Hot', 'HotAndDot', 'HotAndOverheals'}), 'accessories': ('Type', {'heal', 'heal_attached_and_self', 'heal_damage_taken'})},
    'ability.slow': {'accessories': ('Type', {'bush_slow'})},
    'ability.silence': {'areas': ('Type', {'Silence'})},
    'ability.dash': {'skills': ('BehaviorType', {'Charge'}), 'accessories': ('Type', {'dash'})},
    'ability.jump': {'skills': ('BehaviorType', {'FlyJump'}), 'accessories': ('Type', {'jump'})},
    'ability.teleport': {'skills': ('BehaviorType', {'Portals', 'Blink', 'BlinkReturn', 'BlinkToPlaceholder', 'BlinkToProjectile'}), 'accessories': ('Type', {'teleport_to_pet', 'teleport_forward'})},
    'ability.wall_creation': {'areas': ('Type', {'WallSpawn', 'MeepleWallSpawn', 'GladiatorWallSpawn'})},
    'ability.transformations': {'skills': ('BehaviorType', {'ChangeCharacter'}), 'accessories': ('Type', {'change_character'})},
}
LINKS = {
    'characters': {'WeaponSkill': 'skills', 'UltimateSkill': 'skills', 'OverchargedUltimateSkill': 'skills'},
    'skills': {**{k: 'skills' for k in ('SecondarySkill', 'SecondarySkill2', 'SecondarySkill3', 'SecondarySkill4', 'OverchargedVersion')}, **{k: 'projectiles' for k in ('Projectiles', 'OverchargedProjectiles', 'OverchargedChainProjectile')}, **{k: 'areas' for k in ('AreaEffectObject', 'AreaEffectObject2', 'OverchargedAreaEffectObject', 'OverchargedAreaEffectObject2')}, 'SummonedCharacters': 'characters', 'OverchargedSummonedCharacters': 'characters'},
    'projectiles': {**{k: 'areas' for k in ('SpawnAreaEffectObject', 'SpawnAreaEffectObject2', 'SpawnAreaEffectTrail', 'OnCreateAreaEffect')}, 'ChainBullet': 'projectiles', 'SpawnCharacter': 'characters'},
    'areas': {k: 'areas' for k in ('ChainAreaEffect', 'ChainAreaEffect2', 'ChainAreaEffect3', 'ChildAreaEffect', 'OverchargedChainAreaEffect', 'OverchargedChainAreaEffect2', 'OverchargedChainAreaEffect3')},
    'cards': {'AreaEffect': 'areas', 'Projectiles': 'projectiles'},
    'accessories': {'Skill': 'skills', 'AreaEffect': 'areas', 'PetAreaEffect': 'areas'},
}


def read_csv(body):
    rows = list(csv.reader(io.StringIO(body.decode('utf-8-sig'))))
    if len(rows) < 2 or len(set(rows[0])) != len(rows[0]):
        raise ValueError('Invalid CSV header/types')
    header, result = rows[0], {}
    for row in rows[2:]:  # second row contains types, never data
        if len(row) != len(header):
            raise ValueError('CSV width mismatch')
        record = dict(zip(header, row))
        name = record.get('Name')
        if not name or name in result:
            raise ValueError('Missing or duplicate CSV identity')
        result[name] = record  # preserve blanks, literal zero and FALSE distinctly
    return result


def present(value):
    return value is not None and value != ''


def normalize(value):
    return ''.join(c for c in value.casefold() if c.isalnum())


def unique_index(records, field):
    result = {}
    for record in records:
        key = str(record[field])
        if key in result:
            raise ValueError('Duplicate source identity')
        result[key] = record
    return result


def load_inputs(directory, manifest_path, catalog_path):
    manifest = json.loads(Path(manifest_path).read_text())
    sources = unique_index(manifest['requests'], 'name')
    names = ['archive-' + table + '.csv' for table in TABLES]
    bodies = {}
    for name in names:
        body = (Path(directory) / name).read_bytes()
        if hashlib.sha256(body).hexdigest() != sources[name]['sha256']:
            raise ValueError('Source hash mismatch: ' + name)
        bodies[name] = body
    catalog_body = Path(catalog_path).read_bytes()
    if hashlib.sha256(catalog_body).hexdigest() != manifest['catalog_sha256']:
        raise ValueError('Catalog hash mismatch')
    identity_body = (Path(manifest_path).parent / 'MECHANICS_IDENTITIES_2026-09-23.json').read_bytes()
    if hashlib.sha256(identity_body).hexdigest() != manifest['identities_sha256']:
        raise ValueError('Identity projection hash mismatch')
    identities = json.loads(identity_body)
    return (json.loads(catalog_body),
            {t: read_csv(bodies['archive-' + t + '.csv']) for t in TABLES},
            identities['public'], identities['characters'], identities['cards'])


def graph(tables, roots):
    """Bounded explicit-reference inventory; preserves conditional path at each edge."""
    queue = deque((t, n, s, 0, ()) for t, n, s in roots)
    seen, nodes, unresolved = set(), [], set()
    while queue:
        table, name, scope, depth, path = queue.popleft()
        key = (table, name, scope)
        if key in seen:
            continue
        seen.add(key)
        row = tables[table].get(name)
        if row is None:
            unresolved.add((table, name, scope, 'missing_reference'))
            continue
        nodes.append((table, row, scope, path))
        links = dict(LINKS.get(table, {}))
        # Base attack/Super roots are separate; never traverse from base into a kit.
        if table == 'characters' and scope in ('base', 'hypercharge'):
            links = {}
        if table == 'cards' and row.get('Type') == 'accessory':
            links['Skill'] = 'accessories'
        for field, target in links.items():
            for ref in filter(None, row.get(field, '').split(';')):
                next_scope = scope
                if field.startswith('Overcharged') and 'hypercharge' not in scope:
                    next_scope += '/hypercharge'
                if target == 'characters':
                    next_scope += '/transformation' if row.get('BehaviorType') == 'ChangeCharacter' else '/summon'
                if table == 'characters':
                    next_scope += '/base_attack' if field == 'WeaponSkill' else '/super'
                edge = (table, row['Name'], field)
                if depth >= MAX_DEPTH:
                    unresolved.add((target, ref, next_scope, 'depth_limit'))
                elif edge not in path:
                    queue.append((target, ref, next_scope, depth + 1, path + (edge,)))
    return nodes, sorted(unresolved)


def hits(mechanic, nodes):
    result = []
    for table, row, scope, path in nodes:
        if mechanic.startswith('base.') and scope != 'base':
            continue
        if mechanic.startswith('attack.') and 'base_attack' not in scope.split('/'):
            continue
        if mechanic == 'ability.damage' and scope in ('base', 'base_attack'):
            continue
        for field in RULES[mechanic].get(table, '').split():
            if mechanic == 'ability.damage_reduction' and table == 'characters' and scope != 'hypercharge':
                continue
            if present(row.get(field)):
                result.append((scope + '/hypercharge' if field.startswith('Overcharged') and 'hypercharge' not in scope else scope, table, row['Name'], field))
        label = LABELS.get(mechanic, {}).get(table)
        if label and row.get(label[0]) in label[1]:
            result.append((scope, table, row['Name'], label[0]))
        if mechanic == 'ability.summons' and row.get('BehaviorType') != 'ChangeCharacter':
            for field in ('SummonedCharacters', 'OverchargedSummonedCharacters', 'SpawnCharacter'):
                if present(row.get(field)):
                    result.append((scope + '/hypercharge' if field.startswith('Overcharged') and 'hypercharge' not in scope else scope, table, row['Name'], field))
    return sorted(set(result))


def audit(catalog, tables, public, json_characters, json_cards):
    entries = catalog['catalog']
    unique_index(entries, 'external_id')
    by_public = unique_index(public, 'id')
    by_character = unique_index(json_characters.values(), 'id')
    by_card = unique_index(json_cards.values(), 'id')
    brawlers = []
    for entry in sorted(entries, key=lambda e: int(e['external_id'])):
        ext = str(entry['external_id'])
        meta, candidate = by_public.get(ext), by_character.get(ext)
        errors, kit = [], {'gadget': [], 'star_power': []}
        if not meta or normalize(meta['name']) != normalize(entry['name']):
            errors.append('public_catalog_identity_mismatch')
        raw = tables['characters'].get(candidate['Name']) if candidate else None
        if not raw or raw['Type'] != 'Hero':
            errors.append('missing_hero_row')
        if meta and raw:
            for source_key, scope in (('gadgets', 'gadget'), ('starPowers', 'star_power')):
                for ability in meta.get(source_key, []):
                    card = by_card.get(str(ability['id']))
                    csv_card = tables['cards'].get(card['Name']) if card else None
                    if not card or not csv_card or card.get('Target') != raw['Name'] or csv_card.get('Target') != raw['Name']:
                        errors.append('ability_target_mismatch:' + str(ability['id']))
                    else:
                        kit[scope].append(csv_card['Name'])
            if not any(kit.values()):
                errors.append('no_independent_ability_link')
        roots, kit_hits = [], {}
        if not errors:
            roots = [('characters', raw['Name'], 'base'), ('characters', raw['Name'], 'hypercharge')]
            for field, scope in (('WeaponSkill', 'base_attack'), ('UltimateSkill', 'super'), ('OverchargedUltimateSkill', 'super/hypercharge')):
                if raw.get(field):
                    roots.append(('skills', raw[field], scope))
            for scope, names in kit.items():
                roots.extend(('cards', n, scope) for n in sorted(set(names)))
                kit_hits['kit.' + ('gadgets' if scope == 'gadget' else 'star_powers')] = [(scope, 'cards', n, 'Target') for n in sorted(set(names))]
            for card in tables['cards'].values():
                if card['Target'] != raw['Name'] or card.get('Disabled', '').lower() == 'true':
                    continue
                scope = {'6': 'hypercharge', '13': 'buffy/gadget', '15': 'buffy/star_power', '16': 'buffy/hypercharge', '19': 'nanopower', '9': 'other/trait', '12': 'other/event_deck'}.get(card['MetaType'])
                if scope:
                    roots.append(('cards', card['Name'], scope))
                    mechanic = 'kit.' + ('buffy' if scope.startswith('buffy') else 'other' if scope.startswith('other/') else scope)
                    kit_hits.setdefault(mechanic, []).append((scope, 'cards', card['Name'], 'MetaType'))
        nodes, unresolved = graph(tables, roots)
        evidence = {}
        for mechanic in RULES:
            found = sorted(set(kit_hits.get(mechanic, []) + hits(mechanic, nodes)))
            if found:
                # One exact witness per scope suffices to reproduce coverage, not all values.
                per_scope = {}
                for hit in found:
                    per_scope.setdefault(hit[0], '|'.join(hit))
                evidence[mechanic] = list(per_scope.values())
        brawlers.append({'external_id': ext, 'name': entry['name'],
                        'ranked_available': entry['ranked_verfuegbar'], 'source_row': raw['Name'] if raw else None,
                        'identity_status': 'CONFLICT' if errors else 'CORROBORATED_SOURCE_CLAIM',
                        'identity_errors': errors, 'raw_field_evidence': evidence,
                        'no_fragment_observed': sorted(set(RULES) - set(evidence)),
                        'current_patch': None, 'historical_validity': None,
                        'unresolved_reference_count': len(unresolved)})
    count = len(brawlers)
    mechanics = {}
    for mechanic in RULES:
        covered = [b for b in brawlers if mechanic in b['raw_field_evidence']]
        conditional = [b for b in covered if any(h.split('|')[0] not in ('base', 'base_attack') for h in b['raw_field_evidence'][mechanic])]
        mechanics[mechanic] = {'raw_fragment_brawlers': len(covered), 'raw_fragment_percent': round(100 * len(covered) / count, 2) if count else None,
                              'no_fragment_observed': count - len(covered),
                              'conditional_fragment_brawlers': len(conditional),
                              'source_distribution': {'archive_69.230': len(covered)},
                              'patch_quality': 'BUILD_ONLY_NO_VALIDITY_INTERVAL',
                              'qualified_current_brawlers': 0, 'current_unknown': count,
                              'classification': ('CONDITIONAL' if mechanic.startswith(('kit.', 'condition.')) else 'PARTIAL') if covered else 'UNAVAILABLE'}
    return {'schema': 'drafter-mechanics-inventory-1', 'source_build_claim': BUILD, 'archive_revision': REVISION,
            'catalog_observed_at': catalog['observed_at'], 'denominator': count,
            'ranked_denominator': sum(b['ranked_available'] for b in brawlers),
            'source_rows': {t: len(tables[t]) for t in TABLES}, 'graph_max_depth': MAX_DEPTH,
            'gate_5b': 'NOT_PASSED', 'mechanics': mechanics, 'brawlers': brawlers}


def render_markdown(report):
    lines = ['# Drafter V2 mechanics coverage', '',
             'Generated offline by `python3 -m drafter.services.v2_mechanics_audit --format markdown`.', '',
             '**Scope:** frozen local catalog, ' + str(report['denominator']) + ' Brawlers (' + str(report['ranked_denominator']) + ' Ranked-available).',
             'See [MECHANICS_SOURCES.md](MECHANICS_SOURCES.md) for source classifications, probe reproduction, verification sample and the Phase 5B gate.', '',
             '**Counts are nonempty raw field/reference fragments, NOT complete or current mechanics.**',
             'UNKNOWN does not mean absent. Conditional counts retain Super/equipment/form/summon paths.',
             f"Every field has 0 qualified current-patch Brawlers and {report['denominator']} current UNKNOWNs in this audit.",
             'Source distribution for every observed fragment: pinned archive 69.230, with BrawlAPI identity corroboration.',
             'Patch quality for every row: build label only; no verified match-time validity interval.', '',
             f"| Mechanic | Raw fragment / {report['denominator']} | % | No fragment | Conditional / {report['denominator']} | Classification |",
             '|---|---:|---:|---:|---:|---|']
    for key, m in report['mechanics'].items():
        lines.append(f"| {key} | {m['raw_fragment_brawlers']} | {m['raw_fragment_percent']} | {m['no_fragment_observed']} | {m['conditional_fragment_brawlers']} | {m['classification']} |")
    lines += ['', '## Per-Brawler inventory', '',
              'Available below means raw fragments only; all omitted mechanics in the table above are UNKNOWN.',
              'Exact field/row/scope witnesses and explicit missing lists are in [MECHANICS_INVENTORY_2026-09-23.json](MECHANICS_INVENTORY_2026-09-23.json).',
              'Source for every accepted row: archive 69.230 + BrawlAPI; current patch and historical validity UNKNOWN.',
              'Conditional scopes below are observed candidates, never equipped-loadout claims. Reference traversal is bounded at four edges;',
              'unresolved counts include missing/depth-limited edges, so zero observed fragments never proves absence.', '',
              '| Brawler | Raw fragments | Conditional scopes | Identity / unresolved references |',
              '|---|---|---|---|']
    for b in report['brawlers']:
        scopes = sorted({h.split('|')[0] for v in b['raw_field_evidence'].values() for h in v if h.split('|')[0] not in ('base', 'base_attack')})
        lines.append('| ' + b['name'] + ' | ' + ', '.join(b['raw_field_evidence']) + ' | ' + ', '.join(scopes) + ' | ' + b['identity_status'] + ' / ' + str(b['unresolved_reference_count']) + ' |')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--catalog', required=True)
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    args = parser.parse_args()
    report = audit(*load_inputs(args.input_dir, args.manifest, args.catalog))
    print(render_markdown(report) if args.format == 'markdown' else json.dumps(report, indent=2), end='' if args.format == 'markdown' else '\n')


if __name__ == '__main__':
    main()
