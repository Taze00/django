import copy
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from django.test import SimpleTestCase
from drafter.services.v2_future_window import register, seal, publish, digest, verify_membership, validate

UTC = timezone.utc


def fixture_receipt():
    return {'schema':'legacy-bundle-verification-1','status':'VERIFIED','bundle_sha256':'b'*64,
            'policy':'train_empirical_frozen_manual_constants_v1','frozen_at':'2026-09-23T00:00:00Z',
            'required_unknown_inputs':[], 'checks':dict.fromkeys(
                ('independent_rebuild','independent_raw_counts','prior_identity','train_membership','scoring_replay'),True)}


class FutureWindowTests(SimpleTestCase):
    def setUp(self):
        self.protocol = register(now=datetime(2026,9,24,tzinfo=UTC), development_end='2026-09-23T00:00:00Z',
                                 start='2026-09-25T00:00:00Z', end='2026-10-09T00:00:00Z',
                                 v2_hash='a'*64, legacy_hash='b'*64, development_hash='c'*64, revision='fixture-only',legacy_verification=fixture_receipt())
        self.now = datetime(2026,10,10,tzinfo=UTC)
        self.rows = [{'fingerprint':digest(i), 'reconstructed_fingerprint':digest(['reconstructed',i]),
                      'content_sha256':digest(['content',i]), 'played_at':'2026-09-26T00:00:00Z',
                      'source':'api','battle_type':'soloRanked','is_ranked':True,'has_conflict':False,
                      'result_known':True,'complete_unique_3v3':True,'known_context':True,
                      'origins':[{'sampling':'tagged_frontier_v1','source':'api','format':'brawlstars.battlelog.raw',
                                  'run_id':1,'fetched_at':'2026-09-27T00:00:00Z','content_hash':digest(['raw',i])}]}
                     for i in range(1000)]

    def test_preregistration_rejects_old_or_overlapping_window_and_unknown_inputs(self):
        for field,value in [('start_exclusive','2026-09-18T15:04:42Z'),('development_end','2026-09-26T00:00:00Z'),
                            ('legacy_bundle_sha256','UNKNOWN'),('legacy_input_policy','live_provider')]:
            p={**self.protocol,field:value}
            with self.subTest(field=field),self.assertRaises(ValueError): validate(p)

    def test_unverified_or_changed_bundle_receipt_cannot_register(self):
        for changes in ({'status':'BUILT'}, {'bundle_sha256':'d'*64}, {'required_unknown_inputs':['unknown']},
                        {'frozen_at':'2026-09-26T00:00:00Z'}, {'checks':{}}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                validate({**self.protocol,'legacy_verification':{**fixture_receipt(),**changes}})

    def test_old_development_end_is_allowed_without_relaxing_future_boundary(self):
        validate({**self.protocol, 'development_end':'2026-09-10T00:00:00Z'})

    def test_seal_requires_closed_window_and_minimum_evidence(self):
        with self.assertRaises(ValueError): seal(self.protocol,self.rows,datetime(2026,10,1,tzinfo=UTC))
        with self.assertRaises(ValueError): seal(self.protocol,[],self.now)
        result=seal(self.protocol,self.rows,self.now)
        self.assertEqual(result['n'],1000)
        self.assertEqual(result['status'],'SEALED_NOT_EVALUATED')
        self.assertFalse(result['training_eligible'])

    def test_trophy_shadow_unknown_conflict_and_unprovenanced_rows_excluded(self):
        for changes in ({'battle_type':'ranked'}, {'source':'user_report'}, {'result_known':False},
                        {'has_conflict':True},{'origins':[]},{'complete_unique_3v3':False}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                seal(self.protocol,[{**r,**changes} for r in self.rows],self.now)

    def test_temporal_escape_and_duplicate_membership_fail_closed(self):
        with self.assertRaises(ValueError): seal(self.protocol,[{**self.rows[0],'played_at':'2026-09-18T00:00:00Z'}],self.now)
        with self.assertRaises(ValueError): seal(self.protocol,self.rows+[self.rows[0]],self.now)

    def test_changes_detected_late_arrivals_do_not_change_membership(self):
        sealed=seal(self.protocol,self.rows,self.now)
        before=digest(sealed)
        late={**self.rows[0],'fingerprint':digest('late')}
        report=verify_membership(self.protocol,sealed,self.rows+[late])
        self.assertEqual(report['late_arrivals_ignored'],1)
        self.assertEqual(before,digest(sealed))
        changed=copy.deepcopy(self.rows);changed[0]['content_sha256']=digest('changed')
        with self.assertRaises(ValueError): verify_membership(self.protocol,sealed,changed)
        sealed['members'][0]['has_conflict']=True
        with self.assertRaises(ValueError): verify_membership(self.protocol,sealed,self.rows)

    def test_pilot_origin_is_excluded_even_with_later_acceptable_provenance(self):
        changed = copy.deepcopy(self.rows)
        changed[0]['origins'].append({**changed[0]['origins'][0], 'sampling':'observed_discovery_pilot_v1'})
        with self.assertRaisesRegex(ValueError, 'Insufficient'):
            seal(self.protocol, changed, self.now)
        sealed = seal(self.protocol, self.rows, self.now)
        with self.assertRaisesRegex(ValueError, 'pilot'):
            verify_membership(self.protocol, sealed, changed)

    def test_atomic_publication_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'protocol.json';publish(path,self.protocol)
            before=path.read_bytes()
            with self.assertRaises(FileExistsError): publish(path,{'different':True})
            self.assertEqual(before,path.read_bytes())


from django.db import connection
from django.test.utils import CaptureQueriesContext
from drafter.tests.basis import DrafterTest
from drafter.models import Brawler, Match, MatchPlayer
from drafter.management.commands.drafter_v2_future_window import inventory


class FutureInventoryTests(DrafterTest):
    def test_database_predicate_excludes_old_rows_before_content_loading(self):
        protocol = register(now=datetime(2026,9,24,tzinfo=UTC), development_end='2026-09-23T00:00:00Z',
                            start='2026-09-25T00:00:00Z',end='2026-10-09T00:00:00Z',
                            v2_hash='a'*64,legacy_hash='b'*64,development_hash='c'*64,revision='fixture',legacy_verification=fixture_receipt())
        old=Match.objects.create(fingerprint=digest('old-sealed'),played_at=datetime(2026,9,18,tzinfo=UTC),source='api',battle_type='soloRanked')
        new=Match.objects.create(fingerprint=digest('new'),played_at=datetime(2026,9,26,tzinfo=UTC),source='api',battle_type='soloRanked',winner_side='a')
        brawlers=list(Brawler.objects.order_by('id')[:5])
        for i in range(6):
            MatchPlayer.objects.create(match=new,side='a' if i<3 else 'b',brawler=brawlers[i] if i<5 else None)
        with CaptureQueriesContext(connection) as captured:
            rows=list(inventory(protocol))
        self.assertEqual([r['fingerprint'] for r in rows],[new.fingerprint])
        self.assertFalse(rows[0]['complete_unique_3v3'])
        self.assertTrue(all('winner_side' not in row for row in rows))
        self.assertIn('2026-09-25',captured[0]['sql'])
        self.assertIn('2026-10-09',captured[0]['sql'])
        self.assertNotIn(old.fingerprint,str(rows))
        before=rows[0]['content_sha256']
        Match.objects.filter(pk=new.pk).update(winner_side='b')
        self.assertNotEqual(before,list(inventory(protocol))[0]['content_sha256'])
