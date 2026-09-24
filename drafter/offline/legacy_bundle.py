"""Standalone scratch SQLite build/replay. No project DB configuration or network.

Run: python -m drafter.offline.legacy_bundle INPUT.gz OUTPUT.gz
Each build uses a fresh temporary database and the original aggregator/scorer.
"""
import argparse
import gzip
import hashlib
import json
import tempfile
import platform
import sqlite3
import re
from pathlib import Path


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(encode(value)).hexdigest()


def load(path,expected):
    body=gzip.decompress(Path(path).read_bytes())
    if hashlib.sha256(body).hexdigest()!=expected: raise ValueError('Pinned archive content hash mismatch')
    return json.loads(body)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('input');parser.add_argument('output')
    parser.add_argument('--expected-input-sha256',required=True);parser.add_argument('--replay',action='store_true')
    args=parser.parse_args();data=load(args.input,args.expected_input_sha256)
    inputs=data['inputs'] if args.replay else data
    root=Path(__file__).resolve().parents[2]
    for name,content in inputs['code'].items():
        if (root/name).read_text()!=content: raise ValueError(f'Frozen implementation changed: {name}')
    if inputs['policy']!='train_empirical_frozen_manual_constants_v1': raise ValueError('Unknown policy')
    with tempfile.TemporaryDirectory(prefix='legacy-bundle-') as tmp:
        from django.conf import settings
        settings.configure(INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes','drafter'],
                           DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':str(Path(tmp)/'scratch.sqlite3')}},
                           DRAFTER_STAT_PROVIDER=inputs['configuration']['STAT_PROVIDER'],
                           DRAFTER_GEMESSENE_STATS_FREIGEGEBEN=inputs['configuration']['GEMESSENE_STATS_FREIGEGEBEN'],
                           BASE_DIR=root,SECRET_KEY='offline-bundle-only',USE_TZ=True,TIME_ZONE='UTC',DEFAULT_AUTO_FIELD='django.db.models.BigAutoField')
        import django;django.setup()
        environment={'python':platform.python_version(),'django':django.get_version(),'sqlite':sqlite3.sqlite_version}
        if args.replay and data['environment']!=environment: raise ValueError('Frozen dependency environment changed')
        from django.apps import apps
        from django.db import connection, transaction
        from django.core import serializers
        from drafter import config, models
        from drafter.services.v2_legacy_bundle import STAT_MODELS
        actual={k:v for k,v in vars(config).items() if k.isupper() and type(v) in (dict,list,tuple,str,int,float,bool,type(None))}
        if sha(actual)!=sha(inputs['configuration']): raise ValueError('Configuration mismatch')
        with connection.schema_editor() as editor:
            for model in apps.get_models(): editor.create_model(model)
        def restore(rows):
            with connection.constraint_checks_disabled(), transaction.atomic():
                for row in serializers.deserialize('json',json.dumps(rows)): row.save()
            connection.check_constraints()
        restore(inputs['catalog']+inputs['priors'])
        priors_before=inputs['priors']
        if args.replay:
            restored=json.loads(json.dumps(data['empirical']))
            for row in restored:
                row['fields']['created_at']=inputs['captured_at']
                row['fields']['updated_at']=inputs['captured_at']
            restore(restored)
        else:
            restore(inputs['matches']+inputs['players']+inputs['bans'])
            from drafter.services.v2_legacy_bundle import verified_train
            verified_train({'provenance':{'train':inputs['train']}})
            from drafter.services.aggregation.aggregator import Aggregator
            from datetime import date
            aggregator=Aggregator(('api',),stichtag=date.fromisoformat(inputs['reference_date']))
            # Independent membership ledger per existing pool/window; no alternative selection.
            membership={}
            for pool in aggregator.rank_pools:
                for window in aggregator.fenster:
                    interval=aggregator._zeitraum(window)
                    membership[pool+'/'+window]=([] if interval is None else sorted(aggregator._partien(pool,*interval).values_list('fingerprint',flat=True)))
            if any(set(v)-set(inputs['train']['fingerprints']) for v in membership.values()): raise ValueError('Non-Train aggregate member')
            aggregator.ausfuehren()
        def dump(query): return json.loads(serializers.serialize('json',query.order_by('pk')))
        priors_after=[r for m in STAT_MODELS for r in dump(m.objects.filter(source__in=('demo','manual')))]
        if priors_after!=priors_before: raise ValueError('Frozen priors changed')
        empirical=[r for m in STAT_MODELS for r in dump(m.objects.filter(source='api'))]
        # Generated surrogate IDs/timestamps are not scorer inputs; canonicalize only these.
        for row in empirical:
            row['pk']=None
            for name in ('created_at','updated_at'): row['fields'].pop(name,None)
        from drafter.services.context import DraftContext
        from drafter.services.draft_engine import DraftEngine
        from drafter.services.daten import Datenraum
        # Train compositions are used only for replay invariants, not quality metrics.
        from datetime import date as real_date
        import drafter.services.patch_weighting as weighting
        class FrozenDate(real_date):
            @classmethod
            def today(cls): return real_date.fromisoformat(inputs['captured_at'][:10])
        weighting.date=FrozenDate  # Offline clock boundary; formula and scorer are unchanged.
        from drafter.services.v2_legacy_bundle import CATALOG_MODELS
        allowed={m._meta.db_table for m in (*CATALOG_MODELS,*STAT_MODELS)}
        consumed=set()
        def audit_queries(execute,sql,params,many,context):
            tables=set(re.findall(r'(?:FROM|JOIN) "([^"]+)"',sql))
            if tables-allowed: raise ValueError(f'Unsupported scoring input tables: {tables-allowed}')
            consumed.update(tables)
            return execute(sql,params,many,context)
        guard=connection.execute_wrapper(audit_queries);guard.__enter__()
        probes=[]
        seen=set()
        for row in inputs['matches']:
            f=row['fields'];key=(f['game_mode'],f['brawl_map'],f['patch'])
            if key in seen or None in key: continue
            players=[r['fields'] for r in inputs['players'] if r['fields']['match']==row['pk']]
            if len({p['brawler'] for p in players})!=6: continue
            own=tuple(models.Brawler.objects.get(pk=p['brawler']) for p in players if p['side']=='a')
            enemy=tuple(models.Brawler.objects.get(pk=p['brawler']) for p in players if p['side']=='b')
            if len(own)!=3 or len(enemy)!=3: continue
            bmap=models.BrawlMap.objects.get(pk=f['brawl_map']);mode=models.GameMode.objects.get(pk=f['game_mode']);patch=models.Patch.objects.get(pk=f['patch'])
            ctx=DraftContext(game_mode=mode,brawl_map=bmap,patch=patch,own_picks=own,enemy_picks=enemy,rank_pool='alle')
            room=Datenraum(brawl_map=bmap,game_mode=mode,patch=patch,rank_pool='alle').laden()
            direct=DraftEngine(ctx).siegchance();injected=DraftEngine(ctx,raum=room).siegchance()
            if direct!=injected: raise ValueError('Legacy entrypoint mismatch')
            last=DraftContext(game_mode=mode,brawl_map=bmap,patch=patch,own_picks=own[:2],enemy_picks=enemy,rank_pool='alle',own_team_first_pick=False)
            ranks=[r.als_dict() for r in DraftEngine(last).empfehlungen()]
            probes.append({'context':list(key),'probability':direct,'ranking':ranks})
            seen.add(key)
        guard.__exit__(None,None,None)
        if not probes: raise ValueError('No eligible replay probes')
        if args.replay:
            if sha(probes)!=data['probe_sha256']: raise ValueError('Archived scoring replay mismatch')
            result={'match_rows':models.Match.objects.count(),'raw_payload_rows':models.RawPayload.objects.count(),'status':'REPLAY_VERIFIED','probe_n':len(probes),'probe_sha256':sha(probes),'prior_sha256':sha(priors_after)}
        else:
            result={'schema':'legacy-evaluation-bundle-1','consumed_tables':sorted(consumed),'environment':environment,'inputs':inputs,'empirical':empirical,'aggregate_membership':membership,
                    'prior_sha256':sha(priors_after),'empirical_sha256':sha(empirical),'probe_sha256':sha(probes),'probes':probes,
                    'classification':inputs['classification'],'status':'BUILT_REQUIRES_INDEPENDENT_REBUILD_AND_REPLAY'}
        body=encode(result)
        with Path(args.output).open('xb') as stream: stream.write(gzip.compress(body,mtime=0))
        print(json.dumps({'sha256':hashlib.sha256(body).hexdigest(),'empirical_n':len(empirical),'probe_n':len(probes),'prior_sha256':sha(priors_after),'probe_sha256':sha(probes),'status':result['status']}))

if __name__=='__main__': main()
