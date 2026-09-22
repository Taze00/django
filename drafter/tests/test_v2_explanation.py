from datetime import datetime, timezone

from django.test import SimpleTestCase

from drafter.services.evaluation import EvaluationExample
from drafter.services.v2_explanation import explain
from drafter.services.v2_model import train_model


class V2ExplanationContractTest(SimpleTestCase):
    def test_explanation_kommt_aus_modellfakten(self):
        row = EvaluationExample("x", datetime.now(timezone.utc), "gem", "map",
                                (1, 2, 3), (4, 5, 6), 1)
        model = train_model([row], epochs=4)
        result = explain(model, row, {"candidate": 1, "responses": 2, "p_win": 0.5})
        self.assertEqual(result["model_version"], "v2-composition-logit-1")
        self.assertEqual(result["search"]["population_assumption"], "uniform_legal_responses")
        self.assertTrue(all(item["provenance"] == "trained_model_feature"
                            for item in result["contributions"]))