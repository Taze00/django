"""Independent raw-count and archive verification; no Django/database access."""
import argparse
from collections import Counter, defaultdict
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path
import json
from drafter.offline.legacy_bundle import load, sha


def verify(a,b,replay):
    if a!=b: raise ValueError('Independent rebuild differs')
    if sha(a['empirical'])!=a['empirical_sha256'] or sha(a['probes'])!=a['probe_sha256']:
        raise ValueError('Bundle component integrity mismatch')
    inputs=a['inputs'];train=set(inputs['train']['fingerprints'])
    matches={r['pk']:r['fields'] for r in inputs['matches']}
    if len(matches)!=6094 or {r['fingerprint'] for r in matches.values()}!=train: raise ValueError('Train membership changed')
    players=defaultdict(list)
    for r in inputs['players']:
        if r['fields']['match'] not in matches: raise ValueError('Non-Train player')
        players[r['fields']['match']].append(r['fields'])
    if inputs['bans'] or any(p.get('build') for team in players.values() for p in team):
        raise ValueError('Independent build/ban raw-count audit requires implementation for observed data')
    prior=[r for r in inputs['priors']]
    if len(prior)!=137 or sha(prior)!=a['prior_sha256']: raise ValueError('Prior identity mismatch')
    if replay.get('match_rows')!=0 or replay.get('raw_payload_rows')!=0: raise ValueError('Replay accessed a populated observation database')
    if replay['status']!='REPLAY_VERIFIED' or replay['probe_sha256']!=a['probe_sha256'] or replay['prior_sha256']!=a['prior_sha256']:
        raise ValueError('Independent scoring replay failed')
    reference=date.fromisoformat(inputs['reference_date'])
    patches=[r['fields'] for r in inputs['catalog'] if r['model']=='drafter.patch' and date.fromisoformat(r['fields']['released_on'])<=reference]
    confirmed=[p for p in patches if p['datum_bestaetigt']]
    patch_start=max(date.fromisoformat(p['released_on']) for p in (confirmed or patches))
    counts=Counter();wins=Counter();partitions={}
    for pool_window,actual in a['aggregate_membership'].items():
        pool,window=pool_window.split('/');days=inputs['configuration']['AGGREGATIONS_FENSTER'][window]
        start=reference-timedelta(days=days-1) if days else patch_start
        chosen={pk:m for pk,m in matches.items() if start<=date.fromisoformat(m['played_at'][:10])<=reference
                and m['source']=='api' and m['is_ranked'] and m['battle_type']=='soloRanked'
                and not m['has_conflict'] and m['winner_side'] in ('a','b') and (pool=='alle' or m['rank_pool']==pool)}
        expected=sorted(m['fingerprint'] for m in chosen.values())
        if expected!=actual: raise ValueError('Aggregate source-membership mismatch')
        partitions[pool_window]=len(expected)
        for pk,m in chosen.items():
            team=players[pk];contexts=[('global',None,None)]
            if m['game_mode']: contexts.append(('modus',m['game_mode'],None))
            if m['brawl_map']: contexts.append(('map',m['game_mode'],m['brawl_map']))
            for level,mode,map_id in contexts:
                def add(art,ident,won):
                    if level not in inputs['configuration']['AGGREGATIONS_EBENEN'][art]: return
                    key=(pool,window,mode,map_id,art,*ident);counts[key]+=1;wins[key]+=int(won)
                for p in team: add('brawler',(p['brawler'],),p['side']==m['winner_side'])
                for p in team:
                    if p['side']!='a': continue
                    for q in team:
                        if q['side']!='b' or p['brawler']==q['brawler']: continue
                        low,high=sorted((p,q),key=lambda x:x['brawler'])
                        add('counter',(low['brawler'],high['brawler']),low['side']==m['winner_side'])
                for side in ('a','b'):
                    for pair in combinations(sorted({p['brawler'] for p in team if p['side']==side}),2):
                        add('synergy',pair,side==m['winner_side'])
    seen=set()
    for row in a['empirical']:
        f=row['fields'];kind=row['model'].split('.')[1].replace('stat','')
        if kind=='build': raise ValueError('Unexpected empirical build data')
        ids=(f['brawler'],) if kind=='brawler' else (f['brawler'],f['enemy']) if kind=='counter' else (f['brawler_a'],f['brawler_b'])
        key=(f['rank_pool'],f['window_label'],f['game_mode'],f['brawl_map'],kind,*ids)
        if key in seen or f['games']!=counts[key] or f['wins']!=wins[key] or f['source']!='api':
            raise ValueError(f'Independent raw-count mismatch: {key}')
        seen.add(key)
    if seen!=set(counts): raise ValueError('Missing/extra empirical rows')
    return {'schema':'legacy-bundle-verification-1','status':'VERIFIED','policy':inputs['policy'],'bundle_sha256':sha(a),'input_sha256':sha(inputs),
            'empirical_sha256':a['empirical_sha256'],'prior_sha256':a['prior_sha256'],
            'prior_d021_sha256':inputs['prior_d021_sha256'],'train_content_sha256':inputs['train']['examples_sha256'],
            'frozen_at':inputs['captured_at'],'train_n':6094,'prior_n':137,'empirical_n':len(seen),
            'partitions':partitions,'probe_n':len(a['probes']),'probe_sha256':a['probe_sha256'],
            'required_unknown_inputs':[],'checks':{'independent_rebuild':True,'independent_raw_counts':True,
            'prior_identity':True,'train_membership':True,'scoring_replay':True},
            'classification':inputs['classification'],'consumed_tables':a['consumed_tables'],'environment':a['environment']}


def main():
    p=argparse.ArgumentParser();p.add_argument('first');p.add_argument('second');p.add_argument('replay');p.add_argument('output')
    p.add_argument('--bundle-sha256',required=True);p.add_argument('--replay-sha256',required=True);args=p.parse_args()
    report=verify(load(args.first,args.bundle_sha256),load(args.second,args.bundle_sha256),load(args.replay,args.replay_sha256))
    with Path(args.output).open('x') as stream: json.dump(report,stream,sort_keys=True,indent=2);stream.write('\n')
    print(json.dumps({'status':report['status'],'bundle_sha256':report['bundle_sha256'],'empirical_n':report['empirical_n']}))

if __name__=='__main__': main()
