from datetime import datetime, timezone

from django.test import SimpleTestCase

from drafter.services.evaluation import EvaluationExample
from drafter.services.v2_model import train_model
from drafter.services.v2_search import expectimax_pick, last_pick, legal_candidates


class V2SearchContractTest(SimpleTestCase):
    def setUp(self):
        rows = [
            EvaluationExample(str(i), datetime(2026, 1, i + 1, tzinfo=timezone.utc), "gem", "map",
                              (1, 2, 3), (4, 5, 6), 1)
            for i in range(4)
        ]
        self.model = train_model(rows, epochs=5)

    def test_legalitaet_entfernt_picks_und_bans(self):
        self.assertEqual(legal_candidates((1, 2, 3, 4), (1,), (2,), (3,)), [4])

    def test_last_pick_und_expectimax_empfehlen_nur_legale_kandidaten(self):
        last = last_pick(self.model, (1, 2, 3, 4), (1, 2), (3,), (4,), "gem", "map")
        self.assertEqual([item["candidate"] for item in last], [])
        result = expectimax_pick(self.model, (1, 2, 3, 4, 5), (1,), (2,), (3,), "gem", "map")
        self.assertEqual({item["candidate"] for item in result}, {4, 5})