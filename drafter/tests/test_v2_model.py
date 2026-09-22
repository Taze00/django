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