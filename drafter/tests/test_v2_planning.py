"""Synthetic search contracts, not evidence of gameplay quality."""
from django.test import SimpleTestCase
from drafter.services.v2_planning import plan, PlanningError, schedule


class CompleteModel:
    def __init__(self):
        self.calls = []

    def predict(self, row):
        assert len(row.team_a) == len(row.team_b) == 3
        assert len(set(row.team_a + row.team_b)) == 6
        self.calls.append(row)
        return .5 + (sum(row.team_a) - sum(row.team_b)) / 100


class PlanningTests(SimpleTestCase):
    def call(self, own=(), enemy=(), first=True, pool=tuple(range(1, 9)), **kwargs):
        self.model = CompleteModel()
        return plan(self.model, pool, own, enemy, (), {}, mode='synthetic', map_name='fixture', own_first=first, **kwargs)

    def test_first_pick_completes_every_leaf_with_real_order(self):
        result, meta = self.call()
        self.assertEqual(len(result), 8)
        self.assertEqual(meta['remaining_order'], ('own', 'enemy', 'enemy', 'own', 'own', 'enemy'))
        self.assertTrue(meta['approximate'])
        for row in result:
            self.assertEqual(len(row['terminal_own']), 3)
            self.assertEqual(len(row['terminal_enemy']), 3)
            self.assertEqual([s for s, _ in row['continuation']], list(meta['remaining_order'][1:]))
        self.assertEqual(meta['evaluated_leaves'], len(self.model.calls))

    def test_last_pick_is_exhaustive_and_ranks_complete_values(self):
        result, meta = self.call(own=(1, 2), enemy=(3, 4, 5), first=False)
        self.assertEqual([r['candidate'] for r in result], [8, 7, 6])
        self.assertFalse(meta['approximate'])
        self.assertEqual(meta['evaluated_leaves'], 3)

    def test_mid_pick_uses_minimax_reply(self):
        result, meta = self.call(own=(1, 2), enemy=(3, 4), first=True, pool=(1, 2, 3, 4, 5, 6, 7), width=4)
        for item in result:
            remaining = set((5, 6, 7)) - {item['candidate']}
            self.assertEqual(item['continuation'], (('enemy', max(remaining)),))
        self.assertFalse(meta['approximate'])

    def test_invalid_turn_counts_duplicates_and_budget_fail(self):
        for own, enemy, first in [((1,), (), True), ((), (), False), ((1, 2), (), True)]:
            with self.subTest(own=own, enemy=enemy), self.assertRaises(PlanningError):
                self.call(own, enemy, first)
        with self.assertRaises(PlanningError):
            self.call(own=(1, 1), enemy=(3, 4, 5), first=False)
        with self.assertRaises(PlanningError):
            self.call(max_leaves=1)
        with self.assertRaises(PlanningError):
            self.call(pool=(1, 2, 3))

    def test_deterministic_with_permuted_pool_and_legal_continuations(self):
        first, _ = self.call()
        second, _ = self.call(pool=tuple(reversed(range(1, 9))))
        self.assertEqual(first, second)
        for item in first:
            self.assertEqual(len(set(item['terminal_own'] + item['terminal_enemy'])), 6)

    def test_bans_excluded_through_all_future_moves(self):
        model = CompleteModel()
        rows, _ = plan(model, tuple(range(1, 9)), (1, 2), (3, 4), (8,), {},
                       mode='test', map_name='test', own_first=True)
        self.assertTrue(rows)
        for row in rows:
            self.assertNotIn(8, row['terminal_own'] + row['terminal_enemy'])
