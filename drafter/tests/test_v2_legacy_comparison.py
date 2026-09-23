"""Concrete Hideout state, synthetic seed data; equality, never target ranking."""
import json
from unittest.mock import patch
from django.urls import reverse
from drafter.models import Brawler, BrawlMap, GameMode
from drafter.tests.basis import DrafterTest


class HideoutComparisonTests(DrafterTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        mode=GameMode.objects.get(slug='bounty')
        BrawlMap.objects.get_or_create(slug='hideout',defaults={'name':'Hideout','game_mode':mode,'is_active':True})
        for name in ('Mortis','Gene','Piper','Amber','Pearl'):
            Brawler.objects.get_or_create(slug=name.lower(),defaults={'name':name,'is_active':True})

    def request_pair(self, first=False, bans=None):
        payload={'map':'hideout','mode':'bounty','own_picks':['mortis','gene'],
                 'enemy_picks':['piper','amber','pearl'],'own_team_first_pick':first,'bans':bans or [],'compare_legacy':True}
        normal=self.client.post(reverse('drafter:api_recommend'),json.dumps(payload),content_type='application/json')
        # This tests Legacy integration in isolation, without a trained V2 artifact
        # and without weakening V2's own turn-order validation.
        with patch('drafter.views.challenger.recommend',return_value={'recommendations':[]}):
            compared=self.client.post(reverse('drafter:api_challenger'),json.dumps(payload),content_type='application/json')
        self.assertEqual(normal.status_code,200)
        self.assertEqual(compared.status_code,200)
        return normal.json(),compared.json()['legacy']

    def test_exact_normal_response_order_scores_and_context_for_hideout(self):
        normal,compared=self.request_pair()
        self.assertEqual(normal['empfehlungen'],compared['recommendations'])
        self.assertEqual(normal['scores'],compared['scores'])
        self.assertEqual(normal['draft_state'],compared['receipt']['draft_state'])
        self.assertEqual(normal['datenlage'],compared['data_source'])
        self.assertEqual(compared['receipt']['entrypoint'],'DraftEngine(ctx).als_dict()')
        repeat=self.request_pair()[1]
        self.assertEqual(compared['receipt'],repeat['receipt'])

    def test_first_side_bans_and_personal_settings_preserved_and_visible(self):
        _,base=self.request_pair()
        normal,changed=self.request_pair(first=True,bans=['gale'])
        self.assertEqual(normal['empfehlungen'],changed['recommendations'])
        self.assertNotIn('gale',changed['receipt']['candidate_pool'])
        self.assertTrue(changed['receipt']['draft_state']['own_team_first_pick'])
        self.assertNotEqual(base['receipt']['context_sha256'],changed['receipt']['context_sha256'])
        session=self.client.session;session['drafter_confidence']={'belle':5};session.save()
        normal,personal=self.request_pair()
        self.assertEqual(normal['empfehlungen'],personal['recommendations'])
        self.assertEqual(personal['receipt']['personal_preferences_count'],1)
        self.assertNotEqual(base['receipt']['personal_preferences_sha256'],personal['receipt']['personal_preferences_sha256'])

    def test_catalog_change_changes_snapshot_receipt_without_scoring_override(self):
        _,before=self.request_pair()
        Brawler.objects.filter(slug='gale').update(ranked_verfuegbar=False)
        normal,after=self.request_pair()
        self.assertEqual(normal['empfehlungen'],after['recommendations'])
        self.assertNotEqual(before['receipt']['loaded_scoring_inputs_sha256'],after['receipt']['loaded_scoring_inputs_sha256'])
