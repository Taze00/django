"""Fixed preregistered chronological DEVELOPMENT comparison, never Legacy/test."""
import hashlib
import json
from pathlib import Path
from time import perf_counter
from django.db import connection,transaction
from django.utils.dateparse import parse_datetime
from drafter.models import Match
from drafter.services.development_dataset import (chronological_plan,new_development_inventory,V2_HASH)
from drafter.services.v2_challenger_training import example_digest,TRAIN_DIGEST
from drafter.services.evaluation import examples_from_queryset,metrics
from drafter.services.v2_future_window import digest
from drafter.services.v2_model import CompositionLogitModel,train_model,_feature_counts


def select_candidate(results):
    frozen=results['frozen_V2']['validation'];control=results['retrained_team_l2_1']['validation']
    selected=None
    for name in ('retrained_team_l2_1','retrained_team_l2_10','opponent_l2_10'):
        score=results[name]['validation']
        qualifies=score['log_loss']<frozen['log_loss'] and score['brier']<=frozen['brier']
        if name!='retrained_team_l2_1':
            qualifies=qualifies and score['log_loss']<control['log_loss'] and score['brier']<=control['brier']
        results[name]['eligible_development_candidate']=qualifies
        if qualifies and (selected is None or score['log_loss']<results[selected]['validation']['log_loss']):
            selected=name
    return selected


def feature_coverage(model, examples):
    """Count active feature occurrences; unknown terms are absent evidence, not zeros."""
    total=unknown=unknown_rows=0
    brawlers=set()
    for row in examples:
        terms=[key for key,value in _feature_counts(row,model.feature_version).items() if value]
        missing=sum(key not in model.manifest for key in terms)
        total+=len(terms);unknown+=missing;unknown_rows+=bool(missing)
        brawlers.update(row.team_a);brawlers.update(row.team_b)
    return {'rows_with_unknown_feature_terms':unknown_rows,
        'active_feature_occurrences':total,'unknown_feature_occurrences':unknown,
        'unknown_feature_fraction':unknown/total if total else None,
        'distinct_validation_brawlers':len(brawlers),
        'brawlers_without_train_main_effect':sorted(b for b in brawlers if f'brawler:{b}' not in model.manifest)}


def run_experiment(manifest,protocol,revision):
    if protocol['schema']!='chronological-development-experiment-1':
        raise ValueError('Unsupported development experiment')
    if manifest['dataset_sha256']!=digest({'original_train':manifest['original_train'],'new_development':manifest['new_development']}):
        raise ValueError('Immutable development dataset hash mismatch')
    plan=chronological_plan(manifest)
    if plan['status']!='READY_FOR_PREREGISTERED_DEVELOPMENT_VALIDATION':
        raise ValueError('Insufficient chronological development data; no fitting')
    body=Path('data/brawl_reports/v2_challenger.json').read_bytes()
    if hashlib.sha256(body).hexdigest()!=V2_HASH:
        raise ValueError('Frozen V2 control changed')
    frozen=CompositionLogitModel.from_dict(json.loads(body)['model'])
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        observed,_=new_development_inventory(parse_datetime(manifest['created_at']))
        observed={row['fingerprint']:row for row in observed}
        for row in manifest['new_development']:
            current=observed.get(row['fingerprint'])
            if (current is None or current['content_sha256']!=row['content_sha256']
                or any(o not in current['origins'] for o in row['origins'])):
                raise ValueError('Development content/provenance changed after snapshot')
        original,skipped=examples_from_queryset(Match.objects.filter(fingerprint__in=manifest['original_train']['fingerprints']))
        if skipped or len(original)!=6094 or example_digest(original)!=TRAIN_DIGEST:
            raise ValueError('Original Train content mismatch')
        train,skipped_train=examples_from_queryset(Match.objects.filter(fingerprint__in=plan['train_fingerprints']))
        validation,skipped_val=examples_from_queryset(Match.objects.filter(fingerprint__in=plan['validation_fingerprints']))
        if skipped_train or skipped_val or len(train)!=len(plan['train_fingerprints']) or len(validation)!=len(plan['validation_fingerprints']):
            raise ValueError('Snapshot membership missing or ineligible')
        if train[-1].played_at>=validation[0].played_at:
            raise ValueError('Chronological split overlaps')
    def evaluate(model):
        started=perf_counter();result=metrics(model.predict,validation);elapsed=perf_counter()-started
        inference_started=perf_counter()
        for row in validation:model.predict(row)
        inference_seconds=perf_counter()-inference_started
        return {'validation':result,'validation_seconds':elapsed,
            'mean_prediction_ms_per_row':1000*inference_seconds/len(validation),
            **feature_coverage(model,validation),'rows_scored':len(validation)}
    results={'frozen_V2':evaluate(frozen),'B0':{'validation':metrics(lambda row:0.5,validation)}}
    models={}
    for candidate in protocol['grid']:
        started=perf_counter()
        model=train_model(train,regularization=candidate['l2'],epochs=protocol['epochs'],
            learning_rate=protocol['learning_rate'],feature_version=candidate['feature_version'])
        seconds=perf_counter()-started
        models[candidate['id']]=model.as_dict()
        results[candidate['id']]={**evaluate(model),'training_seconds':seconds,'configuration':candidate}
    selected=select_candidate(results)
    return {'schema':'chronological-development-result-1','protocol_sha256':digest(protocol),
        'dataset_sha256':manifest['dataset_sha256'],'code_revision':revision,
        'train_n':len(train),'validation_n':len(validation),'validation_utc_day':plan['validation_utc_day'],
        'train_content_sha256':example_digest(train),'validation_content_sha256':example_digest(validation),
        'results':results,'models':models,'selected_development_candidate':selected,
        'final_test':False,'Legacy_evaluated':False,'working_artifact_changed':False,
        'interpretation':'development selection only; repeated-player/time dependence; forward confirmation required'}
