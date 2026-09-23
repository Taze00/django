"""Synthetic source-inventory contracts: no API, DB, mechanics or model fixtures."""
import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from drafter.services.v2_mechanics_audit import (
    RULES, TABLES, audit, graph, hits, load_inputs, present, read_csv,
    render_markdown, unique_index,
)


def fixture():
    catalog = {'observed_at': '2026-09-23T00:00:00Z', 'catalog': [
        {'external_id': '1', 'name': 'TEST', 'ranked_verfuegbar': True}]}
    tables = {t: {} for t in TABLES}
    tables['characters']['Hero'] = {'Name': 'Hero', 'Type': 'Hero', 'Hitpoints': '100', 'Speed': '', 'WeaponSkill': 'Weapon', 'UltimateSkill': ''}
    tables['skills']['Weapon'] = {'Name': 'Weapon', 'Damage': '0', 'PercentDamage': '', 'MaxCharge': '3'}
    tables['cards']['Gadget'] = {'Name': 'Gadget', 'Target': 'Hero', 'Type': 'accessory', 'Skill': 'GadgetAction', 'MetaType': '5'}
    tables['accessories']['GadgetAction'] = {'Name': 'GadgetAction', 'AreaEffect': 'Explosion', 'Cooldown': '30'}
    tables['areas']['Explosion'] = {'Name': 'Explosion', 'DestroysEnvironment': 'true'}
    public = [{'id': 1, 'name': 'Test', 'gadgets': [{'id': 3}], 'starPowers': []}]
    characters = {'Hero': {'id': 1, 'Name': 'Hero'}}
    cards = {'Gadget': {'id': 3, 'Name': 'Gadget', 'Target': 'Hero'}}
    return catalog, tables, public, characters, cards


class MechanicsAuditTests(unittest.TestCase):
    def test_csv_preserves_blank_zero_false_and_skips_type_row(self):
        rows = read_csv(b'Name,Value,Flag\nstring,int,boolean\nOne,,\nTwo,0,false\n')
        self.assertEqual(set(rows), {'One', 'Two'})
        self.assertFalse(present(rows['One']['Value']))
        self.assertTrue(present(rows['Two']['Value']))
        self.assertTrue(present(rows['Two']['Flag']))
        self.assertEqual(rows['Two']['Flag'], 'false')

    def test_malformed_or_duplicate_sources_fail_closed(self):
        for body in (b'Name,Name\nstring,string\na,b\n', b'Name,X\nstring,int\na\n', b'Name\nstring\na\na\n'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                read_csv(body)
        with self.assertRaises(ValueError):
            unique_index([{'id': 1}, {'id': '1'}], 'id')

    def test_gadget_wallbreak_never_becomes_base(self):
        report = audit(*fixture())
        evidence = report['brawlers'][0]['raw_field_evidence']['ability.wallbreak']
        self.assertEqual(evidence, ['gadget|areas|Explosion|DestroysEnvironment'])
        self.assertEqual(report['mechanics']['ability.wallbreak']['conditional_fragment_brawlers'], 1)

    def test_blanks_are_unknown_but_literal_zero_is_only_a_raw_fragment(self):
        r = audit(*fixture())
        self.assertEqual(r['mechanics']['attack.damage']['raw_fragment_brawlers'], 1)
        self.assertEqual(r['mechanics']['base.movement_speed']['raw_fragment_brawlers'], 0)
        self.assertEqual(r['mechanics']['attack.percentage_hp_damage']['raw_fragment_brawlers'], 0)
        self.assertTrue(all(m['current_unknown'] == 1 for m in r['mechanics'].values()))
        self.assertTrue(all(m['qualified_current_brawlers'] == 0 for m in r['mechanics'].values()))

    def test_conflicting_ability_target_quarantines_entire_brawler(self):
        args = fixture()
        args[-1]['Gadget']['Target'] = 'AnotherHero'
        r = audit(*args)
        self.assertEqual(r['brawlers'][0]['identity_status'], 'CONFLICT')
        self.assertEqual(r['brawlers'][0]['raw_field_evidence'], {})
        self.assertEqual(r['denominator'], 1)  # conflict never shrinks denominator

    def test_csv_target_must_also_match(self):
        args = fixture()
        args[1]['cards']['Gadget']['Target'] = 'AnotherHero'
        self.assertEqual(audit(*args)['brawlers'][0]['identity_status'], 'CONFLICT')

    def test_missing_ability_link_is_not_inferred_from_character_id(self):
        args = fixture()
        args[2][0]['gadgets'] = []
        self.assertEqual(audit(*args)['brawlers'][0]['raw_field_evidence'], {})

    def test_duplicate_catalog_is_rejected_not_double_counted(self):
        args = fixture()
        args[0]['catalog'].append(args[0]['catalog'][0].copy())
        with self.assertRaises(ValueError):
            audit(*args)

    def test_transformation_is_not_summon_and_retains_scope(self):
        tables = fixture()[1]
        tables['skills']['Transform'] = {'Name': 'Transform', 'BehaviorType': 'ChangeCharacter', 'SummonedCharacters': 'Form'}
        tables['characters']['Form'] = {'Name': 'Form', 'WeaponSkill': 'Weapon'}
        nodes, missing = graph(tables, [('skills', 'Transform', 'super')])
        self.assertFalse(missing)
        self.assertEqual(hits('ability.summons', nodes), [])
        self.assertTrue(hits('ability.transformations', nodes))
        self.assertIn('super/transformation/base_attack', {x[0] for x in hits('attack.damage', nodes)})

    def test_overcharged_reference_requires_hypercharge_even_on_super_row(self):
        tables = fixture()[1]
        tables['skills']['Super'] = {'Name': 'Super', 'OverchargedSummonedCharacters': 'Pet'}
        nodes, _ = graph(tables, [('skills', 'Super', 'super')])
        self.assertEqual(hits('ability.summons', nodes)[0][0], 'super/hypercharge')

    def test_unknown_opcodes_sentinels_do_not_become_repeatability_or_jump(self):
        nodes = [('skills', {'Name': 'X', 'ChargeType': '11', 'Value': '-1'}, 'super', ())]
        for mechanic in ('ability.jump', 'condition.limited_uses', 'condition.repeatability'):
            self.assertEqual(hits(mechanic, nodes), [])

    def test_reference_traversal_is_bounded_and_missing_nodes_are_reported(self):
        tables = fixture()[1]
        for i in range(8):
            tables['skills'][str(i)] = {'Name': str(i), 'SecondarySkill': str(i + 1)}
        nodes, unresolved = graph(tables, [('skills', '0', 'super')])
        self.assertEqual(len(nodes), 5)
        self.assertEqual(unresolved[0][-1], 'depth_limit')
        _, unresolved = graph(tables, [('skills', 'absent', 'super')])
        self.assertEqual(unresolved[0][-1], 'missing_reference')

    def test_all_mechanics_reported_without_patch_or_feature_promotion(self):
        report = audit(*fixture())
        self.assertEqual(set(report['mechanics']), set(RULES))
        self.assertEqual(report['gate_5b'], 'NOT_PASSED')
        self.assertIsNone(report['brawlers'][0]['current_patch'])
        self.assertIsNone(report['brawlers'][0]['historical_validity'])
        self.assertIn('Raw fragment / 1', render_markdown(report))
        self.assertEqual(report, audit(*fixture()))

    def test_hash_mismatch_stops_before_parsing(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / 'archive-characters.csv').write_text('changed')
            manifest = {'requests': [{'name': 'archive-characters.csv', 'sha256': '0' * 64}]}
            (p / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'Source hash mismatch'), patch('drafter.services.v2_mechanics_audit.read_csv') as parser:
                load_inputs(p, p / 'manifest.json', p / 'catalog.json')
            parser.assert_not_called()

    def test_minimized_replay_is_exact_and_rejects_changed_catalog_or_identities(self):
        args = fixture()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            records = []
            for name, rows in args[1].items():
                buffer = io.StringIO()
                columns = list(next(iter(rows.values()))) if rows else ['Name']
                writer = csv.DictWriter(buffer, fieldnames=columns)
                writer.writeheader()
                writer.writerow({key: 'string' for key in columns})
                writer.writerows(rows.values())
                body = buffer.getvalue().encode()
                filename = 'archive-' + name + '.csv'
                (root / filename).write_bytes(body)
                records.append({'name': filename, 'sha256': hashlib.sha256(body).hexdigest()})
            catalog_body = json.dumps(args[0]).encode()
            identity_body = json.dumps({'public': args[2], 'characters': args[3], 'cards': args[4]}).encode()
            cat = root / 'catalog.json'
            ident = root / 'MECHANICS_IDENTITIES_2026-09-23.json'
            cat.write_bytes(catalog_body)
            ident.write_bytes(identity_body)
            manifest = {'requests': records, 'catalog_sha256': hashlib.sha256(catalog_body).hexdigest(),
                        'identities_sha256': hashlib.sha256(identity_body).hexdigest()}
            manifest_path = root / 'manifest.json'
            manifest_path.write_text(json.dumps(manifest))
            self.assertEqual(load_inputs(root, manifest_path, cat), args)
            cat.write_bytes(catalog_body + b' ')
            with self.assertRaisesRegex(ValueError, 'Catalog hash mismatch'):
                load_inputs(root, manifest_path, cat)
            cat.write_bytes(catalog_body)
            ident.write_bytes(identity_body + b' ')
            with self.assertRaisesRegex(ValueError, 'Identity projection hash mismatch'):
                load_inputs(root, manifest_path, cat)
