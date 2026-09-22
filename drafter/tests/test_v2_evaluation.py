from datetime import datetime, timezone

from django.test import SimpleTestCase

from drafter.services.evaluation import EvaluationExample, evaluate, time_split


def beispiele():
    return [
        EvaluationExample(str(i), datetime(2026, 1, i + 1, tzinfo=timezone.utc), "gem", "map",
                          (1, 2, 3), (4, 5, 6), i % 2)
        for i in range(10)
    ]


class EvaluationContractTest(SimpleTestCase):
    def test_split_ist_zeitlich_und_fingerprint_eindeutig(self):
        train, validation, holdout = time_split(beispiele())
        self.assertLess(train[-1].played_at, validation[0].played_at)
        self.assertLess(validation[-1].played_at, holdout[0].played_at)
        self.assertEqual(len({row.fingerprint for row in train + validation + holdout}), 10)

    def test_baselines_liefern_probabilitaeten_und_metriken(self):
        train, validation, holdout = time_split(beispiele())
        report = evaluate(train, validation, holdout)
        self.assertEqual(set(report), {
            "B0_50_50", "B2_global_meta", "B3_meta_mode",
            "B4_meta_map", "B5_meta_pair_synergy",
        })
        for result in report.values():
            self.assertEqual(result["holdout"]["status"], "ok")
            self.assertGreaterEqual(result["holdout"]["log_loss"], 0.0)
            self.assertGreaterEqual(result["holdout"]["brier"], 0.0)