import hashlib
import json
import tempfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from drafter.models import Brawler
from drafter.models.matches import Match, MatchPlayer
from drafter.services import v2_challenger_training as training
from drafter.services.evaluation import EvaluationExample
from drafter.services.v2_challenger import load_artifact, ChallengerUnavailable
from drafter.services.v2_model import train_model, _feature_counts
from drafter.tests.basis import DrafterTest
from datetime import datetime, timezone


class ChallengerTests(DrafterTest):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'model.json'
        self.settings_override = self.settings(DRAFTER_V2_MODEL_PATH=str(self.path))
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.brawlers = list(Brawler.objects.order_by('id')[:8])
        ids = [b.id for b in self.brawlers]
        row = EvaluationExample('synthetic', datetime(2026, 1, 1, tzinfo=timezone.utc),
                                'test-mode', 'test-map', tuple(ids[:3]), tuple(ids[3:6]), 1)
        rows = [row, replace(row, team_a=(ids[0], ids[1], ids[6]))]
        model = train_model(rows, epochs=5)
        self.artifact = {
            'schema': 'drafter-v2-challenger-1', 'status': 'EXPERIMENTAL_NOT_PROMOTED',
            'model': model.as_dict(), 'feature_support': {key: 1 for key in model.manifest},
            'catalog': {b.slug: b.id for b in Brawler.objects.all()},
            'contexts': {'hard-rock-mine': {'mode': 'test-mode', 'map_name': 'test-map'}},
            'provenance': {'train': {'n': 2, 'last': row.played_at.isoformat()}, 'validation': {'n': 1}},
            'limitations': ['Synthetic test artifact only'],
        }
        self.save()
        self.payload = {'map': 'hard-rock-mine', 'own_picks': [b.slug for b in self.brawlers[:2]],
                        'enemy_picks': [b.slug for b in self.brawlers[3:6]],
                        'own_team_first_pick': False, 'bans': []}

    def save(self):
        self.path.write_text(json.dumps(self.artifact))

    def post(self, data=None):
        return self.client.post(reverse('drafter:api_challenger'), json.dumps(
            self.payload if data is None else data), content_type='application/json')

    def test_last_pick_is_complete_sorted_and_explained(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        result = response.json()
        recommendations = result['recommendations']
        self.assertEqual(len(recommendations), 2)
        self.assertEqual([r['p_win'] for r in recommendations], sorted(
            [r['p_win'] for r in recommendations], reverse=True))
        self.assertEqual(result['engine'], 'v2_challenger')
        for row in recommendations:
            self.assertTrue(0 < row['p_win'] < 1)
            self.assertTrue(row['contributions'])
            self.assertIsNone(row['uncertainty']['interval'])
        self.assertNotIn('fingerprints', result['provenance']['train'])

    def test_banned_and_unavailable_candidates_excluded(self):
        self.payload['bans'] = [self.brawlers[2].slug]
        self.brawlers[6].ranked_verfuegbar = False
        self.brawlers[6].save()
        self.assertEqual(self.post().json()['recommendations'], [])

    def test_invalid_shapes_duplicates_and_types(self):
        for data in ([], {'map': []}, {**self.payload, 'own_picks': []},
                     {**self.payload, 'enemy_picks': self.payload['own_picks'] + [self.brawlers[3].slug]},
                     {**self.payload, 'bans': self.payload['own_picks']}):
            with self.subTest(data=data):
                self.assertEqual(self.post(data).status_code, 400)

    def test_missing_model_and_mismatched_identity_fail_without_fallback(self):
        self.path.unlink()
        self.assertEqual(self.post().status_code, 503)
        self.artifact['catalog'][self.brawlers[0].slug] += 999
        self.save()
        self.assertEqual(self.post().status_code, 503)

    def test_nonfinite_and_unknown_model_versions_are_rejected(self):
        for value in (float('nan'), float('inf')):
            self.artifact['model']['weights'][0] = value
            self.save()
            with self.assertRaises(ChallengerUnavailable):
                load_artifact()
        self.artifact['model']['weights'][0] = 0
        self.artifact['model']['feature_version'] = 'unknown'
        self.save()
        with self.assertRaises(ChallengerUnavailable):
            load_artifact()

    def test_page_and_post_only_contract(self):
        page = self.client.get(reverse('drafter:challenger'))
        self.assertContains(page, 'V2 Challenger')
        self.assertContains(page, 'csrfmiddlewaretoken')
        self.assertEqual(self.client.get(reverse('drafter:api_challenger')).status_code, 405)

    def test_recovered_partitions_never_load_holdout_examples(self):
        Match.objects.all().delete()  # Disposable test DB only.
        for day in (1, 2, 3):
            match = Match.objects.create(fingerprint=f'fixture-{day}', played_at=datetime(2026, 1, day, tzinfo=timezone.utc),
                                         is_ranked=True, battle_type='soloRanked', winner_side='a', source='fixture')
            for side, team in [('a', self.brawlers[:3]), ('b', self.brawlers[3:6])]:
                for b in team:
                    MatchPlayer.objects.create(match=match, side=side, brawler=b)
        expected = hashlib.sha256('fixture-1\nfixture-2\nfixture-3'.encode()).hexdigest()
        with patch.multiple(training, TRAIN_N=1, VALIDATION_N=1, TOTAL_N=3, FREEZE_DIGEST=expected):
            with CaptureQueriesContext(connection) as queries:
                train, validation = training.development_partitions()
            self.assertEqual([r.fingerprint for r in train + validation], ['fixture-1', 'fixture-2'])
            for query in queries:
                sql = query['sql'].lower()
                self.assertNotIn('insert ', sql)
                if 'winner_side"' in sql.split(' from ')[0]:
                    self.assertNotIn('fixture-3', sql)
            Match.objects.filter(fingerprint='fixture-3').update(fingerprint='changed')
            with self.assertRaises(ValueError):
                training.development_partitions()
