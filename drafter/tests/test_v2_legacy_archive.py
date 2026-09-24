import gzip
import json
import tempfile
from pathlib import Path
from django.test import SimpleTestCase
from drafter.offline.legacy_bundle import encode, sha, load


class ArchiveIntegrityTests(SimpleTestCase):
    def test_pin_rejects_changed_future_data_or_constants(self):
        original={'train':['train-only'], 'priors':[{'source':'demo','weight':0.25}]}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bundle.gz';path.write_bytes(gzip.compress(encode(original),mtime=0))
            self.assertEqual(load(path,sha(original)),original)
            for altered in ({**original,'train':['train-only','future']},{**original,'priors':[]}):
                path.write_bytes(gzip.compress(encode(altered),mtime=0))
                with self.assertRaisesRegex(ValueError,'Pinned archive'): load(path,sha(original))

    def test_gzip_payload_recompression_does_not_change_content_identity(self):
        data={'frozen':True}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bundle.gz'
            for level in (1,9):
                path.write_bytes(gzip.compress(encode(data),compresslevel=level,mtime=0))
                self.assertEqual(load(path,sha(data)),data)

from django.db import connection
from django.test.utils import CaptureQueriesContext
from datetime import datetime, timezone
from drafter.tests.basis import DrafterTest
from drafter.models import Match, RawPayload
from drafter.management.commands.drafter_v2_legacy_export import source_metadata


class MetadataBoundaryTests(DrafterTest):
    def test_shared_raw_bodies_are_never_selected(self):
        row=Match.objects.create(fingerprint='train-fixture',played_at=datetime(2026,1,1,tzinfo=timezone.utc),source='fixture')
        payload=RawPayload.objects.create(content_hash='a'*64,source='fixture',format='test',payload={'never_load':'shared-body'})
        row.payloads.add(payload)
        with CaptureQueriesContext(connection) as queries:
            metadata=source_metadata(Match.objects.filter(pk=row.pk))
        self.assertEqual(metadata[str(row.pk)][0]['content_hash'],'a'*64)
        for query in queries:
            self.assertNotIn('"payload"',query['sql'])
        self.assertNotIn('never_load',json.dumps(metadata))

from drafter.offline.verify_legacy_bundle import verify


class IndependentVerifierTests(SimpleTestCase):
    def test_different_rebuild_cannot_receive_verified_receipt(self):
        with self.assertRaisesRegex(ValueError,'Independent rebuild differs'):
            verify({'first':1},{'second':2},{})

    def test_component_hash_cannot_be_replaced_by_claim(self):
        changed={'empirical':[{'changed':True}], 'empirical_sha256':'a'*64,'probes':[],'probe_sha256':sha([])}
        with self.assertRaisesRegex(ValueError,'component integrity'):
            verify(changed,changed,{})
