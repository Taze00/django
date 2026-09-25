"""One frozen forward DEVELOPMENT check, never a final test or Legacy comparison."""
import hashlib
import json
from pathlib import Path
from time import perf_counter
from django.db import connection, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drafter.models import Match
from drafter.services.development_dataset import new_development_inventory, V2_HASH
from drafter.services.development_experiment import feature_coverage
from drafter.services.evaluation import examples_from_queryset, metrics
from drafter.services.v2_future_window import digest
from drafter.services.v2_model import CompositionLogitModel


def forward_check(protocol, revision):
    if protocol.get('schema') != 'development-forward-confirmation-1':
        raise ValueError('Unsupported forward development protocol')
    start=parse_datetime(protocol['start_inclusive']);end=parse_datetime(protocol['end_exclusive'])
    if not start or not end or start>=end:
        raise ValueError('Invalid fixed forward interval')
    if timezone.now()<end:
        raise ValueError('Forward development interval has not closed; no scoring')
    archive=Path(protocol['candidate_archive']).read_bytes()
    if hashlib.sha256(archive).hexdigest()!=protocol['candidate_archive_sha256']:
        raise ValueError('Frozen development candidates changed')
    fitted=json.loads(archive)
    if fitted['selected_development_candidate']!=protocol['candidate']:
        raise ValueError('Candidate differs from frozen development selection')
    original=Path('data/brawl_reports/v2_challenger.json').read_bytes()
    if hashlib.sha256(original).hexdigest()!=V2_HASH:
        raise ValueError('Frozen V2 control changed')
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        # This is an as-of inventory, not a changed collector clock: only raw
        # actually fetched by the fixed end is accepted as provenance.
        inventory,_=new_development_inventory(end)
        members=[r for r in inventory if start<=parse_datetime(r['played_at'])<end]
        membership=digest(members)
        if len(members)<protocol['minimum_eligible']:
            return {'status':'DATA_UNAVAILABLE','n':len(members),'membership_sha256':membership,
                'members':members,'protocol_sha256':digest(protocol),'code_revision':revision,
                'final_test':False,'metrics_computed':False,'interval_extended':False}
        rows,skipped=examples_from_queryset(Match.objects.filter(fingerprint__in=[r['fingerprint'] for r in members]))
        if skipped or len(rows)!=len(members):
            raise ValueError('Forward membership missing or ineligible')
    frozen_models={'frozen_V2':json.loads(original)['model'],
        'retrained_team_l2_1':fitted['models']['retrained_team_l2_1'],
        protocol['candidate']:fitted['models'][protocol['candidate']]}
    results={'B0':{'validation':metrics(lambda row:.5,rows)}}
    for name,body in frozen_models.items():
        model=CompositionLogitModel.from_dict(body)
        result=metrics(model.predict,rows)
        started=perf_counter()
        for row in rows:model.predict(row)
        results[name]={'validation':result,**feature_coverage(model,rows),
            'mean_prediction_ms_per_row':1000*(perf_counter()-started)/len(rows)}
    candidate=results[protocol['candidate']]['validation']
    confirms=all(candidate['log_loss']<results[c]['validation']['log_loss'] and
        candidate['brier']<=results[c]['validation']['brier'] for c in ('frozen_V2','retrained_team_l2_1'))
    return {'status':'FORWARD_DEVELOPMENT_CONFIRMED' if confirms else 'NOT_CONFIRMED',
        'n':len(rows),'members':members,'membership_sha256':membership,
        'protocol_sha256':digest(protocol),'code_revision':revision,'results':results,
        'final_test':False,'Legacy_evaluated':False,'working_artifact_changed':False,
        'interpretation':'graph-discovered development confirmation; not an independent final test'}
