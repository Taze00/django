"""Synthetic selection contracts, no real validation data."""
from django.test import SimpleTestCase
from drafter.services.development_experiment import run_experiment,select_candidate


class DevelopmentExperimentTests(SimpleTestCase):
    def test_grid_cannot_win_by_regressing_brier(self):
        def score(loss,brier):return {'validation':{'log_loss':loss,'brier':brier}}
        rows={'frozen_V2':score(.7,.25),'retrained_team_l2_1':score(.6,.2),
              'retrained_team_l2_10':score(.61,.2),'opponent_l2_10':score(.59,.21)}
        self.assertEqual(select_candidate(rows),'retrained_team_l2_1')
        self.assertFalse(rows['opponent_l2_10']['eligible_development_candidate'])

    def test_no_improvement_keeps_current_control(self):
        def score(loss):return {'validation':{'log_loss':loss,'brier':.25}}
        rows={k:score(.7) for k in ('frozen_V2','retrained_team_l2_1','retrained_team_l2_10','opponent_l2_10')}
        self.assertIsNone(select_candidate(rows))

    def test_missing_volume_gate_blocks_before_file_or_database_reads(self):
        from drafter.services.v2_future_window import digest
        manifest={'original_train':{'fingerprints':['synthetic']},'new_development':[]}
        manifest['dataset_sha256']=digest(manifest)
        with self.assertRaisesRegex(ValueError,'Insufficient'):
            run_experiment(manifest,{'schema':'chronological-development-experiment-1'},'synthetic')
