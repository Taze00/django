import json
from django.urls import reverse
from drafter.models import Praxisfall
from drafter.services.v2_snapshots import response_digest
from drafter.tests import test_v2_challenger


class ShadowTests(test_v2_challenger.ChallengerTests):
    def test_capture_before_choice_and_append_reports_preserves_response(self):
        self.login_user()
        response = self.post({**self.payload, 'shadow_capture': True})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        record = Praxisfall.objects.get(pk=result['snapshot_id'])
        self.assertEqual(record.gewaehlt, '')
        self.assertEqual(record.ergebnis, 'unknown')
        self.assertIn('legacy', record.snapshot_metadata['response'])
        original = record.snapshot_metadata['response']
        digest = response_digest(original)
        self.assertEqual(digest, record.snapshot_metadata['response_sha256'])
        self.assertFalse(record.snapshot_metadata['training_eligible'])
        url = reverse('drafter:api_challenger_result', args=[record.pk])
        self.assertEqual(self.client.post(url, json.dumps({'result':'win'}), content_type='application/json').status_code,400)
        choice = result['recommendations'][0]['slug']
        for data in ({'chosen':choice}, {'result':'win'}, {'result':'loss'}, {'result':'loss'}):
            self.assertEqual(self.client.post(url,json.dumps(data),content_type='application/json').status_code,200)
        record.refresh_from_db()
        self.assertEqual(record.snapshot_metadata['response'],original)
        self.assertEqual(len(record.snapshot_metadata['events']),3)
        self.assertEqual(record.ergebnis,'loss')
        self.assertEqual(record.gewaehlt,choice)

    def test_shadow_requires_explicit_authenticated_opt_in(self):
        self.assertEqual(self.post({**self.payload,'shadow_capture':True}).status_code,403)
        self.login_user()
        self.assertEqual(self.post({**self.payload,'shadow_capture':'yes'}).status_code,400)
        self.assertEqual(self.post().status_code,200)
        self.assertFalse(Praxisfall.objects.filter(snapshot_metadata__schema='drafter-shadow-1').exists())

    def test_actual_unmodeled_legal_choice_can_be_reported_without_invented_rank(self):
        self.login_user()
        result=self.post({**self.payload,'shadow_capture':True}).json()
        ranked={r['slug'] for r in result['recommendations']}
        choice=next(slug for slug in result['legacy']['receipt']['candidate_pool'] if slug not in ranked)
        url=reverse('drafter:api_challenger_result',args=[result['snapshot_id']])
        self.assertEqual(self.client.post(url,json.dumps({'chosen':choice}),content_type='application/json').status_code,200)
        record=Praxisfall.objects.get(pk=result['snapshot_id'])
        self.assertIsNone(record.gewaehlter_rang)
        self.assertEqual(record.gewaehlt,choice)
        self.assertEqual(self.client.post(url,json.dumps({'chosen':self.payload['own_picks'][0]}),content_type='application/json').status_code,400)
