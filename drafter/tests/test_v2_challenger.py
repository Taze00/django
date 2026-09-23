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
        examples, _ = training.examples_from_queryset(Match.objects.filter(fingerprint__in=['fixture-1', 'fixture-2']))
        with patch.multiple(training, TRAIN_N=1, VALIDATION_N=1, TOTAL_N=3, FREEZE_DIGEST=expected,
                            TRAIN_DIGEST=training.example_digest(examples[:1]),
                            VALIDATION_DIGEST=training.example_digest(examples[1:])):
            with CaptureQueriesContext(connection) as queries:
                train, validation = training.development_partitions()
            self.assertEqual([r.fingerprint for r in train + validation], ['fixture-1', 'fixture-2'])
            for query in queries:
                sql = query['sql'].lower()
                self.assertNotIn('insert ', sql)
                if 'winner_side"' in sql.split(' from ')[0]:
                    self.assertNotIn('fixture-3', sql)
            Match.objects.filter(fingerprint='fixture-1').update(winner_side='b')
            with self.assertRaisesRegex(ValueError, 'content mismatch'):
                training.development_partitions()
            Match.objects.filter(fingerprint='fixture-1').update(winner_side='a')
            Match.objects.filter(fingerprint='fixture-3').update(fingerprint='changed')
            with self.assertRaises(ValueError):
                training.development_partitions()

    def login_user(self, name='challenger-user'):
        from django.contrib.auth.models import User
        user = User.objects.create_user(username=name)
        self.client.force_login(user)
        return user

    def test_comparison_separates_score_types_and_default_endpoint(self):
        result = self.post({**self.payload, 'compare_legacy': True}).json()
        self.assertEqual(result['legacy']['score_kind'], 'heuristic_score_not_probability')
        self.assertTrue(result['legacy']['recommendations'])
        self.assertNotIn('legacy', self.post().json())
        legacy = self.client.post(reverse('drafter:api_recommend'), json.dumps(self.payload), content_type='application/json').json()
        self.assertIn('empfehlungen', legacy)
        self.assertNotIn('engine', legacy)

    def test_signed_snapshot_is_idempotent_and_preserves_actual_response(self):
        from drafter.models import Praxisfall
        self.login_user()
        result = self.post().json()
        request = {'token': result['snapshot_token'], 'chosen': result['recommendations'][0]['slug']}
        url = reverse('drafter:api_challenger_snapshots')
        self.path.unlink()  # Saving must not re-run the model or require its current artifact.
        first = self.client.post(url, json.dumps(request), content_type='application/json')
        self.assertEqual(first.status_code, 201)
        second = self.client.post(url, json.dumps(request), content_type='application/json')
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()['id'], second.json()['id'])
        record = Praxisfall.objects.get(pk=first.json()['id'])
        self.assertEqual(record.empfehlungen, result['recommendations'])
        self.assertEqual(record.snapshot_metadata['artifact_sha256'], result['artifact_sha256'])
        self.assertIs(record.snapshot_metadata['training_eligible'], False)
        self.assertIsNone(record.gewaehlter_score)
        frozen = record.empfehlungen
        outcome_url = reverse('drafter:api_challenger_result', args=[record.id])
        response = self.client.post(outcome_url, json.dumps({'result': 'win'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.ergebnis, 'win')
        self.assertEqual(record.empfehlungen, frozen)
        self.assertEqual(self.client.get(url).json()['snapshots'][0]['id'], record.id)

    def test_snapshot_tampering_ownership_and_choice_rejected(self):
        self.login_user()
        result = self.post().json()
        url = reverse('drafter:api_challenger_snapshots')
        chosen = result['recommendations'][0]['slug']
        for payload in [{'token': result['snapshot_token'] + 'x', 'chosen': chosen},
                        {'token': result['snapshot_token'], 'chosen': 'not-recommended'}]:
            self.assertEqual(self.client.post(url, json.dumps(payload), content_type='application/json').status_code, 400)
        valid = {'token': result['snapshot_token'], 'chosen': chosen}
        saved = self.client.post(url, json.dumps(valid), content_type='application/json').json()['id']
        self.login_user('other-user')
        self.assertEqual(self.client.post(url, json.dumps(valid), content_type='application/json').status_code, 400)
        self.assertEqual(self.client.get(url).json()['snapshots'], [])
        self.assertEqual(self.client.post(reverse('drafter:api_challenger_result', args=[saved]),
                                        json.dumps({'result': 'loss'}), content_type='application/json').status_code, 404)

    def test_anonymous_logging_and_csrf_are_rejected(self):
        from django.test import Client
        self.assertNotIn('snapshot_token', self.post().json())
        self.assertEqual(self.client.post(reverse('drafter:api_challenger_snapshots'), '{}', content_type='application/json').status_code, 403)
        secure_client = Client(enforce_csrf_checks=True)
        self.assertEqual(secure_client.post(reverse('drafter:api_challenger'), json.dumps(self.payload), content_type='application/json').status_code, 403)

    def test_snapshot_expiry_conflicting_resave_and_private_detail(self):
        import time
        self.login_user()
        result = self.post().json()
        url = reverse('drafter:api_challenger_snapshots')
        payload = {'token': result['snapshot_token'], 'chosen': result['recommendations'][0]['slug']}
        with patch('django.core.signing.time.time', return_value=time.time() + 7202):
            self.assertEqual(self.client.post(url, json.dumps(payload), content_type='application/json').status_code, 400)
        saved = self.client.post(url, json.dumps(payload), content_type='application/json').json()['id']
        payload['chosen'] = result['recommendations'][1]['slug']
        self.assertEqual(self.client.post(url, json.dumps(payload), content_type='application/json').status_code, 400)
        detail_url = reverse('drafter:api_challenger_result', args=[saved])
        self.assertEqual(self.client.get(detail_url).json()['snapshot']['recommendations'], result['recommendations'])
        self.login_user('detail-other')
        self.assertEqual(self.client.get(detail_url).status_code, 404)

    def test_model_info_lists_only_supported_maps_and_explanations_use_names(self):
        info = self.client.get(reverse('drafter:api_challenger_info'))
        self.assertEqual(info.json()['supported_maps'], ['hard-rock-mine'])
        facts = self.post().json()['recommendations'][0]['contributions']
        self.assertTrue(all('label' in fact for fact in facts))
        self.assertTrue(any(b.name in fact['label'] for b in self.brawlers for fact in facts))
        self.path.unlink()
        self.assertEqual(self.client.get(reverse('drafter:api_challenger_info')).status_code, 503)
