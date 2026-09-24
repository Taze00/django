"""Synthetic prospective collection boundaries; never real evaluation data."""
from datetime import datetime, timedelta, timezone
from drafter.models import CollectorRun
from drafter.services.prospective_acquisition import ProspectiveCollector
from drafter.services.v2_future_window import register, digest
from drafter.tests.basis import DrafterTest
from drafter.tests.test_v2_future_window import fixture_receipt, fixture_acquisition, fixture_context
from drafter.tests.test_collector import ErsatzClient


class ProspectiveAcquisitionTests(DrafterTest):
    def setUp(self):
        super().setUp()
        self.protocol = register(now=datetime(2026,9,24,tzinfo=timezone.utc),
            development_end='2026-09-23T23:00:00Z', start='2026-09-25T00:00:00Z',
            end='2026-10-09T00:00:00Z', v2_hash='a'*64, legacy_hash='b'*64,
            development_hash='c'*64, revision='synthetic', legacy_verification=fixture_receipt(),
            acquisition=fixture_acquisition(), common_context=fixture_context())
        self.client = ErsatzClient({}, standard={'items':[]})
        self.now = datetime(2026,9,26,tzinfo=timezone.utc)

    def collect(self, now=None):
        return ProspectiveCollector(protocol=self.protocol, client=self.client,
                                    now=lambda: now or self.now).execute()

    def test_cannot_collect_before_start_or_after_end(self):
        for at in (datetime(2026,9,25,tzinfo=timezone.utc), datetime(2026,10,9,tzinfo=timezone.utc)):
            with self.assertRaisesRegex(ValueError,'Outside'):
                self.collect(at)
        self.assertEqual(CollectorRun.objects.count(),0)
        self.assertEqual(self.client.aufrufe,[])

    def test_cooldown_purpose_and_global_budget_include_failed_runs(self):
        report = self.collect()
        run = CollectorRun.objects.get()
        self.assertEqual(run.parameters['protocol_sha256'],digest(self.protocol))
        self.assertEqual(report['purpose'],'prospective_test')
        self.assertTrue(report['future_test_eligible'])
        with self.assertRaisesRegex(ValueError,'cooldown'):
            self.collect(self.now+timedelta(hours=5))
        self.collect(self.now+timedelta(hours=6))
        CollectorRun.objects.bulk_create([CollectorRun(parameters={'protocol_sha256':digest(self.protocol)},
                                                       status='aborted') for _ in range(54)])
        with self.assertRaisesRegex(ValueError,'budget'):
            self.collect(self.now+timedelta(days=1))
        self.assertEqual(self.client.aufrufe,[])

    def test_missing_or_post_registration_feasibility_is_rejected(self):
        for change in ({'pilot_new_eligible':0}, {'pilot_finished_at':'2026-09-26T00:00:00Z'}):
            protocol = {**self.protocol,'acquisition':{**self.protocol['acquisition'],**change}}
            with self.assertRaises(ValueError):
                ProspectiveCollector(protocol=protocol,client=self.client)

    def test_new_window_payload_retains_prospective_provenance_and_cutoff(self):
        from drafter.models import TrackedPlayer, RawPayload
        from drafter.models.discovery import DiscoveryPlayer
        from drafter.tests import test_tagged_frontier as fixtures
        from drafter.services.brawl_api_client import pfad_battlelog
        self.battle = lambda *args, **kwargs: fixtures.TaggedFrontierTest.battle(self, *args, **kwargs)
        root_run = CollectorRun.objects.create(parameters={'strategie':'observed_discovery_pilot_v1'})
        root = TrackedPlayer.objects.create(tag=fixtures.SEED,origin='official_observed')
        DiscoveryPlayer.objects.create(player=root,first_source='trophy_battlelog',
            first_seen=self.now-timedelta(days=1),last_seen=self.now-timedelta(days=1),first_run=root_run)
        old = self.battle(time='20260924T230000.000Z')
        new = self.battle(time='20260925T230000.000Z')
        self.client = fixtures.ClockClient({pfad_battlelog(fixtures.SEED):{'items':[old,new]}},
                                           standard={'items':[]},moment=self.now)
        report = self.collect()
        self.assertEqual(report['new_eligible_solo_ranked_matches'],1)
        self.assertEqual(report['historical_records_retained_raw_only'],1)
        raw = RawPayload.objects.filter(reference=fixtures.SEED).get()
        self.assertEqual(raw.sampling,'prospective_discovery_v1')
        self.assertEqual(raw.collector_run.parameters['protocol_sha256'],digest(self.protocol))
