"""Synthetic source-structure fixtures only; no game facts, network or database."""
import tempfile
import unittest
from pathlib import Path

from drafter.services.v2_mechanics_followup import checked, kit_conflicts, read_records, values, walk


class MechanicsFollowupTests(unittest.TestCase):
    def test_continuations_preserve_order_provenance_zero_false_and_missing(self):
        table = read_records(b'Name,Values,Flag\nstring,int,boolean\nA,270,false\n,90,\n,0,\nB,,\n')
        self.assertEqual((table['physical_rows'], table['named_records'], table['continuation_rows']), (4, 2, 2))
        a = table['records']['A']
        self.assertEqual(values(a, 'Values'), ['270', '90', '0'])
        self.assertEqual(values(a, 'Flag'), ['false'])
        self.assertEqual([v['record'] for v in a['fields']['Values']], [3, 4, 5])
        self.assertEqual(values(table['records']['B'], 'Values'), [])

    def test_no_orphan_or_duplicate_identity_or_malformed_types(self):
        for body in (b'Name,Value\nstring,int\n,1\n', b'Name\nstring\nA\nA\n',
                     b'Name,Value\nstring\nA,1\n', b'Name,Value\nstring,int\nA\n'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                read_records(body)

    def test_and_conditions_are_edges_not_executed_predicates(self):
        tables = {
            'actions': read_records(b'Name,Conditions,ConditionCompareAndOr\nstring,string,string\nAction,C1;C2,And\n'),
            'conditions': read_records(b'Name,Type,Values\nstring,string,int\nC1,FacingDirection,270\n,,90\nC2,UnknownOpcode,17\n')}
        r = walk(tables, ('actions', 'Action', 'gadget/conditional'))
        self.assertEqual(len(r['edges']), 2)
        self.assertEqual(r['root'][2], 'gadget/conditional')
        self.assertEqual(r['effect_semantics'], 'UNKNOWN')
        self.assertEqual(values(r['nodes'][0], 'ConditionCompareAndOr'), ['And'])
        self.assertNotIn('condition_result', r)

    def test_hypercharge_requirement_and_multivalue_references_remain_explicit(self):
        tables = {'components_logic': read_records(b'Name,StatusEffectsOvercharged\nstring,string\nX,A\n,B\n'),
                  'status_effects_logic': read_records(b'Name,DurationTicks\nstring,int\nA,20\nB,40\n')}
        r = walk(tables, ('components_logic', 'X', 'gadget'))
        self.assertEqual(len(r['edges']), 2)
        self.assertTrue(all(e['explicit_overcharged_column'] for e in r['edges']))
        self.assertEqual([e['from'][-1] for e in r['edges']], [3, 4])

    def test_no_numeric_opcode_mapping_or_tick_conversion(self):
        tables = {'gear_boosts': read_records(b'Name,LogicType,ModifierValue\nstring,int,int\nX,0,15\n')}
        r = walk(tables, ('gear_boosts', 'X', 'equipped_gear'))
        self.assertEqual(values(r['nodes'][0], 'LogicType'), ['0'])
        self.assertEqual(r['edges'], [])
        self.assertEqual(r['effect_semantics'], 'UNKNOWN')

    def test_bounds_and_missing_references_are_reported(self):
        tables = {'traits': read_records(b'Name,StatusEffect\nstring,string\nX,Missing\n')}
        r = walk(tables, ('traits', 'X', 'test'), max_depth=0)
        self.assertEqual(r['unresolved'][0]['reason'], 'depth_limit')
        r = walk(tables, ('traits', 'X', 'test'), max_nodes=1)
        self.assertEqual(r['unresolved'][0]['reason'], 'node_limit')
        r = walk(tables, ('traits', 'X', 'test'))
        self.assertEqual(r['unresolved'][0]['reason'], 'missing_reference')

    def test_cycles_terminate_without_erasing_edges(self):
        tables = {'status_effects_logic': read_records(b'Name,ChainStatusEffect\nstring,string\nX,Y\nY,X\n')}
        r = walk(tables, ('status_effects_logic', 'X', 'test'))
        self.assertEqual(len(r['nodes']), 2)
        self.assertEqual(len(r['edges']), 2)

    def test_identity_conflicts_are_derived_and_unknown_ids_not_repaired(self):
        cards = read_records(b'Name,Target\nstring,string\nA,Right\nB,Wrong\n')
        r = kit_conflicts({'gadgets': [{'id': 23000000}, {'id': 23000001}, {'id': 23000009}]}, cards, 'Right')
        self.assertEqual([c['id'] for c in r], [23000001, 23000009])
        self.assertEqual(r[-1]['observed_targets'], [])

    def test_modified_source_fails_digest_check(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'x').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
                checked(folder, {'name': 'x', 'sha256': '0' * 64})
