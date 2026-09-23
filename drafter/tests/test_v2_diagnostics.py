"""Synthetic algebra and missing-evidence tests; no expected gameplay ranking."""
from dataclasses import replace
from django.test import SimpleTestCase
from drafter.services.evaluation import EvaluationExample
from drafter.services.v2_model import CompositionLogitModel, FEATURE_VERSION, OPPONENT_VERSION, feature_manifest
from drafter.services.v2_diagnostics import diagnose, compare_candidates


class DiagnosticTests(SimpleTestCase):
    def setUp(self):
        self.a = EvaluationExample('synthetic', None, 'bounty', 'Hideout', (1, 2, 3), (4, 5, 6), 0)
        self.b = replace(self.a, team_a=(1, 2, 7))
        manifest = feature_manifest([self.a, self.b])
        self.model = CompositionLogitModel(FEATURE_VERSION, manifest, tuple((i % 7 - 3) / 100 for i in range(len(manifest))), 1, 1)
        self.support = dict.fromkeys(manifest, 2)

    def item(self, row, candidate, continuation=()):
        return {'slug': str(candidate), 'name': str(candidate), 'p_win': self.model.predict(row),
                'continuation': continuation, 'diagnostic': diagnose(self.model, row, candidate, self.support, {}, continuation)}

    def test_complete_decomposition_and_candidate_comparison_reconcile(self):
        a,b = self.item(self.a,3), self.item(self.b,7)
        d=a['diagnostic'];self.assertAlmostEqual(d['candidate_logit']+d['background_logit'],d['total_logit'])
        c=compare_candidates(a,b)
        self.assertAlmostEqual(c['background_logit_difference'],0)
        self.assertAlmostEqual(sum(v for v in c['candidate_family_logit_differences'].values() if v is not None)+c['background_logit_difference'],c['total_logit_difference'])
        self.assertAlmostEqual(c['probability_difference_pp'],100*(a['p_win']-b['p_win']))
        self.assertFalse(d['families']['enemy']['active'])
        self.assertIsNone(d['families']['enemy']['modeled_logit'])
        self.assertFalse(d['search']['active'])

    def test_missing_is_not_a_learned_zero_and_support_is_unknown(self):
        row=replace(self.a, team_a=(1,2,999))
        d=self.item(row,999)['diagnostic']
        for group in (d['families'][name] for name in ('individual','mode','map','teammate')):
            self.assertEqual(group['status'],'PARTIAL')
            self.assertTrue(all(t['weight'] is None and t['logit_contribution'] is None and t['training_matches'] is None for t in group['terms']))

    def test_changing_enemies_cannot_create_counter_explanation_in_existing_model(self):
        first=compare_candidates(self.item(self.a,3), self.item(self.b,7))
        second=compare_candidates(self.item(replace(self.a,team_b=(8,9,10)),3),self.item(replace(self.b,team_b=(8,9,10)),7))
        self.assertAlmostEqual(first['total_logit_difference'],second['total_logit_difference'])
        self.assertIsNone(second['candidate_family_logit_differences']['enemy'])

    def test_search_changes_background_not_an_invented_bonus(self):
        a=self.item(self.a,3,(('enemy',6),))
        b=self.item(replace(self.b,team_b=(4,5,8)),7,(('enemy',8),))
        c=compare_candidates(a,b)
        self.assertEqual(c['background_interpretation'],'different_hypothetical_continuations')
        self.assertFalse(a['diagnostic']['search']['independent_bonus'])

    def test_opponent_family_is_exposed_only_for_that_feature_version(self):
        manifest=feature_manifest([self.a],OPPONENT_VERSION)
        model=CompositionLogitModel(OPPONENT_VERSION,manifest,tuple(.01 for _ in manifest),1,1)
        d=diagnose(model,self.a,3,dict.fromkeys(manifest,1),{},())
        self.assertTrue(d['families']['enemy']['active'])
        self.assertEqual(len(d['families']['enemy']['terms']),3)
