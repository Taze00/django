from datetime import datetime, timezone

from django.test import SimpleTestCase

from drafter.services.evaluation import EvaluationExample
from drafter.services.v2_model import train_model


class V2ModelContractTest(SimpleTestCase):
    def test_team_swap_ist_exakt_symmetrisch(self):
        row = EvaluationExample("x", datetime.now(timezone.utc), "gem", "map",
                                (1, 2, 3), (4, 5, 6), 1)
        swapped = EvaluationExample("y", row.played_at, row.mode, row.map_name,
                                    row.team_b, row.team_a, 0)
        model = train_model([row, swapped], epochs=20)
        self.assertAlmostEqual(model.predict(row), 1 - model.predict(swapped), places=12)

    def test_model_hat_keinen_intercept_und_ist_deterministisch(self):
        rows = [
            EvaluationExample(str(index), datetime(2026, 1, index + 1, tzinfo=timezone.utc),
                              "gem", "map", (1, 2, 3), (4, 5, 6), index % 2)
            for index in range(6)
        ]
        first = train_model(rows, epochs=10)
        second = train_model(rows, epochs=10)
        self.assertEqual(first.as_dict(), second.as_dict())

class OpponentModelTests(SimpleTestCase):
    def test_opponent_terms_swap_sign_and_are_jointly_explained(self):
        from dataclasses import replace
        from drafter.services.v2_model import OPPONENT_VERSION, _feature_counts
        from drafter.services.v2_explanation import contributions
        row = EvaluationExample('synthetic', datetime(2026, 1, 1, tzinfo=timezone.utc),
                                'gem', 'map', (1, 2, 3), (4, 5, 6), 1)
        swapped = replace(row, team_a=row.team_b, team_b=row.team_a, label=0)
        features = _feature_counts(row, OPPONENT_VERSION)
        reverse = _feature_counts(swapped, OPPONENT_VERSION)
        self.assertEqual(features, {k: -v for k, v in reverse.items()})
        self.assertEqual(len([k for k in features if k.startswith('opponent:')]), 9)
        model = train_model([row, swapped], epochs=10, feature_version=OPPONENT_VERSION)
        self.assertAlmostEqual(model.predict(row) + model.predict(swapped), 1, places=12)
        self.assertTrue(any(f['feature'].startswith('opponent:') for f in contributions(model, row, limit=100)))
        self.assertEqual(model.as_dict()['model_version'], OPPONENT_VERSION)

    def test_validation_only_brawlers_never_enter_vocabulary(self):
        from drafter.services.v2_model import OPPONENT_VERSION
        from dataclasses import replace
        row = EvaluationExample('synthetic', datetime(2026, 1, 1, tzinfo=timezone.utc),
                                'gem', 'map', (1, 2, 3), (4, 5, 6), 1)
        model = train_model([row], epochs=10, feature_version=OPPONENT_VERSION)
        manifest = dict(model.manifest)
        prediction = model.predict(replace(row, team_a=(1, 2, 999)))
        self.assertTrue(0 < prediction < 1)
        self.assertEqual(manifest, model.manifest)
        self.assertNotIn('brawler:999', manifest)
