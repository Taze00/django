"""Frozen prospective collection; operational counts only, no scoring or tuning."""
import hashlib
from collections import Counter
from datetime import timedelta
from pathlib import Path

from drafter.models import CollectorRun, RawPayload
from drafter.models.discovery import DiscoveryPlayer
from drafter.services.discovery_frontier import DiscoveryFrontierCollector
from drafter.services.tagged_frontier import TaggedFrontierCollector
from drafter.services.v2_future_window import ACQUISITION, digest, timestamp, validate


def verify_files(protocol):
    for name, expected in protocol['acquisition']['implementation_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen acquisition implementation changed')
    if hashlib.sha256(Path('data/brawl_reports/v2_challenger.json').read_bytes()).hexdigest() != protocol['v2_artifact_sha256']:
        raise ValueError('Frozen V2 artifact changed')
    legacy = protocol['acquisition']['legacy_artifact']
    if hashlib.sha256(Path(legacy['path']).read_bytes()).hexdigest() != legacy['file_sha256']:
        raise ValueError('Frozen D-022 bundle changed')


class ProspectiveCollector(DiscoveryFrontierCollector):
    sampling = 'prospective_discovery_v1'

    def __init__(self, *, protocol, client=None, now=None):
        validate(protocol)
        self.protocol = protocol
        self.protocol_hash = digest(protocol)
        TaggedFrontierCollector.__init__(self, after=timestamp(protocol['start_exclusive']),
            max_battlelogs=ACQUISITION['max_http_attempts_per_run'],
            max_depth=ACQUISITION['max_depth'], client=client, now=now,
            code_revision=protocol['code_revision'])
        self.raw_types, self.bootstrap_types = Counter(), Counter()
        self.seen_response_tags, self.bootstrap_tags = set(), set()

    def _execute(self):
        # Called under the same session lock as both frontier strategies.
        now = self.now()
        if not timestamp(self.protocol['start_exclusive']) < now < timestamp(self.protocol['end_inclusive']):
            raise ValueError('Outside preregistered prospective acquisition interval')
        runs = CollectorRun.objects.filter(parameters__protocol_sha256=self.protocol_hash)
        if runs.count() >= ACQUISITION['max_runs']:
            raise ValueError('Prospective run budget exhausted (crashes also consume a run)')
        if runs.filter(started_at__gt=now-timedelta(hours=6)).exists():
            raise ValueError('Six-hour prospective run cooldown still active')
        return TaggedFrontierCollector._execute(self)

    def _prepare_frontier(self):
        self.run.parameters.update(protocol_sha256=self.protocol_hash,
            purpose='prospective_test', future_test_eligible=True)
        self.run.save(update_fields=['parameters'])
        self.metrics['query_eligible_tags_available'] = DiscoveryPlayer.objects.count()
        self.metrics['query_eligible_tags_due'] = self._due().filter(discovery_frontier__isnull=False).count()

    def _claim(self, queried):
        if self.now() >= timestamp(self.protocol['end_inclusive']):
            return None
        return super()._claim(queried)

    def _extra_report(self):
        report = super()._extra_report()
        report.update(purpose='prospective_test', future_test_eligible=True,
                      protocol_sha256=self.protocol_hash)
        return report


def catalog_identity():
    """Identity/resolution fields only, no mutable runtime statistics or outcomes."""
    from drafter.models import Brawler, BrawlMap, GameMode, Patch
    rows = []
    for model, fields in (
        (Brawler, ('name','slug','external_id')),
        (GameMode, ('name','slug','external_id')),
        (BrawlMap, ('name','slug','external_id','game_mode_id')),
        (Patch, ('name','released_on','datum_bestaetigt','datum_quelle','is_current')),
    ):
        for row in model.objects.order_by('pk').values('pk', *fields):
            if 'released_on' in row:
                row['released_on'] = row['released_on'].isoformat()
            rows.append({'model':model._meta.label_lower, **row})
    return rows


def verify_catalog(protocol):
    if digest(catalog_identity()) != protocol['common_context']['catalog_identity_sha256']:
        raise ValueError('Frozen catalog/patch resolution identity changed; fail closed')
