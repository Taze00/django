"""Read-only export of pinned Train and frozen constants, never runtime aggregates."""
import gzip
import hashlib
import json
from pathlib import Path
from django.conf import settings
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Prefetch
from django.utils import timezone
from drafter import config, models
from drafter.services.v2_legacy_bundle import verified_train, CATALOG_MODELS, STAT_MODELS
from drafter.management.commands.drafter_v2_legacy_bundle_audit import PINNED_ARTIFACT
from drafter.services.v2_legacy_comparison import _digest


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def fixture(query):
    return json.loads(serializers.serialize('json',query.order_by('pk')))


def source_code():
    root=Path(__file__).resolve().parents[3]
    paths=list((root/'drafter').glob('*.py'))+list((root/'drafter/models').glob('*.py'))
    paths += [p for p in (root/'drafter/services').rglob('*.py') if not p.name.startswith('v2_')]
    return {str(p.relative_to(root)):p.read_text() for p in sorted(set(paths))}


def source_metadata(query):
    return {str(m.pk):sorted([{k:getattr(p,k) for k in ('id','source','content_hash','format','sampling','collector_run_id')} for p in m.payloads.all()],key=lambda p:p['id']) for m in query.prefetch_related(Prefetch('payloads',queryset=models.RawPayload.objects.only('id','source','content_hash','format','sampling','collector_run_id')))}


class Command(BaseCommand):
    help='Export pinned Train plus frozen B constants to a new gzip archive (no writes to DB)'
    def add_arguments(self,parser):
        parser.add_argument('--output',required=True)
        parser.add_argument('--revision',required=True)
    def handle(self,*args,**options):
        artifact_path=Path(getattr(settings,'DRAFTER_V2_MODEL_PATH',Path(settings.BASE_DIR)/'data/brawl_reports/v2_challenger.json'))
        body=artifact_path.read_bytes()
        if hashlib.sha256(body).hexdigest()!=PINNED_ARTIFACT: raise CommandError('V2 artifact changed')
        with transaction.atomic():
            with connection.cursor() as c: c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            query,examples=verified_train(json.loads(body))
            keys=[r.fingerprint for r in examples]
            catalog=[row for model in CATALOG_MODELS for row in fixture(model.objects.all())]
            prior_objects={m._meta.label_lower:list(m.objects.filter(source__in=('demo','manual')).order_by('pk')) for m in STAT_MODELS}
            if [len(v) for v in prior_objects.values()] != [20,90,27,0]: raise CommandError('Authorized prior membership changed')
            prior_hash=_digest({k:serializers.serialize('python',v) for k,v in prior_objects.items()})
            if prior_hash!='8f0560ee751038bfdbb14595bc8bf2534f105bbd68ae5c3bdfe33192610b81b1':
                raise CommandError('Authorized prior contents changed since D-021')
            priors=[r for m in STAT_MODELS for r in fixture(m.objects.filter(source__in=('demo','manual')))]
            matches=fixture(query)
            source_membership=source_metadata(query)
            for row in matches: row['fields']['payloads']=[]  # Raw bodies may span partitions; do not export them.
            players=fixture(models.MatchPlayer.objects.filter(match__in=query))
            bans=fixture(models.MatchBan.objects.filter(match__in=query))
            constants={k:v for k,v in vars(config).items() if k.isupper() and type(v) in (dict,list,tuple,str,int,float,bool,type(None))}
            value={'schema':'legacy-evaluation-input-1','revision':options['revision'],'captured_at':timezone.now().isoformat(),
                   'policy':'train_empirical_frozen_manual_constants_v1','artifact_sha256':PINNED_ARTIFACT,
                   'train':json.loads(body)['provenance']['train'],'catalog':catalog,'priors':priors,
                   'prior_d021_sha256':prior_hash,'configuration':constants,'code':source_code(),
                   'matches':matches,'players':players,'bans':bans,'source_membership':source_membership,
                   'reference_date':examples[-1].played_at.date().isoformat(),
                   'classification':{'A':['matches','players','bans','empirical_aggregates','empirical_hierarchical_priors'],
                     'B':['catalog','configuration','code','priors','reference_date'],
                     'C':[], 'B_meaning':'pre-existing frozen algorithmic/catalog constants, not measured mechanics or Train-derived',
                     'unknown_values':'preserved; required unresolved identities fail replay; optional UNKNOWN keeps Legacy semantics'}}
        data=canonical(value)
        with Path(options['output']).open('xb') as stream: stream.write(gzip.compress(data,mtime=0))
        self.stdout.write(json.dumps({'input_sha256':hashlib.sha256(data).hexdigest(),'train_n':len(keys),'prior_n':len(priors),'output':options['output']}))
