from datetime import datetime, timezone
from unittest.mock import patch
from django.db import connection
from django.test import SimpleTestCase
from django.test.utils import CaptureQueriesContext
from drafter.models import Match, MatchPlayer, Brawler
from drafter.services import v2_legacy_bundle as bundle
from drafter.services.evaluation import examples_from_queryset
from drafter.services.v2_challenger_training import example_digest
from drafter.tests.basis import DrafterTest


class PriorLineageTests(SimpleTestCase):
    def test_demo_and_manual_cannot_be_promoted_by_hashing(self):
        for source in ('demo','manual'):
            report=bundle.prior_gate({'CounterStat':{source:1,'api':100}})
            self.assertEqual(report['status'],'BLOCKED_PRIOR_LINEAGE')
            self.assertFalse(report['verified'])
            self.assertEqual(report['non_train_priors']['CounterStat'][source],1)

    def test_measured_only_is_not_automatic_train_lineage(self):
        report=bundle.prior_gate({'BrawlerStat':{'api':100}})
        self.assertFalse(report['verified'])
        self.assertEqual(report['status'],'REQUIRES_TRAIN_REBUILD_AND_REPLAY')


class TrainMembershipTests(DrafterTest):
    def test_only_pinned_train_is_selected_and_tampering_fails(self):
        train=Match.objects.create(fingerprint='train-only-fixture',played_at=datetime(2026,1,1,tzinfo=timezone.utc),
                                   source='fixture',battle_type='soloRanked',winner_side='a')
        other=Match.objects.create(fingerprint='never-read-fixture',played_at=datetime(2026,1,2,tzinfo=timezone.utc),source='fixture')
        for i,b in enumerate(Brawler.objects.order_by('pk')[:6]):
            MatchPlayer.objects.create(match=train,side='a' if i<3 else 'b',brawler=b)
        rows,_=examples_from_queryset(Match.objects.filter(pk=train.pk))
        expected=example_digest(rows)
        artifact={'provenance':{'train':{'fingerprints':[train.fingerprint],'examples_sha256':expected}}}
        with patch.multiple(bundle,TRAIN_N=1,TRAIN_DIGEST=expected):
            with CaptureQueriesContext(connection) as captured:
                queryset,selected=bundle.verified_train(artifact)
            self.assertEqual([r.fingerprint for r in selected],[train.fingerprint])
            self.assertIn('train-only-fixture',captured[0]['sql'])
            self.assertNotIn('never-read-fixture',str(list(captured)))
            Match.objects.filter(pk=train.pk).update(winner_side='b')
            with self.assertRaisesRegex(ValueError,'Train content mismatch'):
                bundle.verified_train(artifact)
            artifact['provenance']['train']['fingerprints']=[train.fingerprint,train.fingerprint]
            with self.assertRaises(ValueError): bundle.verified_train(artifact)
