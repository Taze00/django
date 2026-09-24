"""Historical strict D-021 preflight. Never publishes a verified bundle.

D-022 permits frozen manual constants; use drafter_v2_legacy_export and the
offline builder/verifier for that versioned policy. This older gate remains
a diagnostic that demo rows are not Train-derived, not the current blocker.

Measured inputs may be rebuilt from Train; demo/manual priors cannot acquire
Train lineage by being frozen, hashed or copied into a scratch database.
"""
from collections import Counter
import hashlib
from pathlib import Path
from django.core import serializers
from drafter import config, models
from drafter.services.evaluation import examples_from_queryset
from drafter.services.v2_challenger_training import TRAIN_N, TRAIN_DIGEST, example_digest
from drafter.services.v2_legacy_comparison import _digest

STAT_MODELS = (models.BrawlerStat, models.CounterStat, models.SynergyStat, models.BuildStat)
CATALOG_MODELS = (models.GameMode, models.BrawlMap, models.Patch, models.Brawler,
                  models.BrawlerBalanceChange, models.BrawlerItem, models.BuildRule)


def verified_train(artifact):
    partition = artifact['provenance']['train']
    keys = partition['fingerprints']
    if len(keys) != TRAIN_N or len(set(keys)) != TRAIN_N or partition['examples_sha256'] != TRAIN_DIGEST:
        raise ValueError('Pinned Train membership/content contract mismatch')
    # Direct key selection: no historical freeze query and no Validation/holdout.
    queryset = models.Match.objects.filter(fingerprint__in=keys)
    examples, skipped = examples_from_queryset(queryset)
    if skipped or len(examples) != TRAIN_N or example_digest(examples) != TRAIN_DIGEST:
        raise ValueError('Train content mismatch; refuse bundle construction')
    if [r.fingerprint for r in examples] != keys:
        raise ValueError('Train membership order changed')
    return queryset, examples


def prior_gate(source_counts):
    unproven = {name: {source: count for source, count in counts.items()
                      if source in ('demo', 'manual') and count}
               for name, counts in source_counts.items()}
    unproven = {name: rows for name, rows in unproven.items() if rows}
    return {'status': 'BLOCKED_PRIOR_LINEAGE' if unproven else 'REQUIRES_TRAIN_REBUILD_AND_REPLAY',
            'non_train_priors': unproven, 'verified': False,
            'reason': 'Exact frozen provider priors have no Train observation lineage' if unproven else
                      'Absence of demo/manual rows alone does not prove aggregate lineage'}


def preflight(artifact):
    from django.db.models import Count
    from drafter.services.daten import Datenraum
    from drafter.services.providers.registry import hole_stat_provider
    queryset, examples = verified_train(artifact)
    source_counts = {m.__name__: {r['source']: r['n'] for r in m.objects.values('source').annotate(n=Count('pk'))}
                     for m in STAT_MODELS}
    catalog = {m._meta.label_lower: serializers.serialize('python', m.objects.order_by('pk')) for m in CATALOG_MODELS}
    priors = {m._meta.label_lower: serializers.serialize('python', m.objects.filter(source__in=('demo','manual')).order_by('pk'))
              for m in STAT_MODELS}
    configuration = {k:v for k,v in vars(config).items() if k.isupper() and type(v) in (dict,list,tuple,str,int,float,bool,type(None))}
    provider = hole_stat_provider()
    resolved = {}
    prior = getattr(provider, 'prior', None)
    if prior:
        from drafter.services.providers.records import StatAnfrage
        bmap = models.BrawlMap.objects.filter(slug='hideout').first()
        if bmap:
            room = Datenraum(brawl_map=bmap, rank_pool='masters', provider=provider)
            ids = frozenset(models.Brawler.objects.filter(ranked_verfuegbar=True).values_list('id',flat=True))
            query = StatAnfrage(brawler_ids=ids,game_mode_id=bmap.game_mode_id,brawl_map_id=bmap.pk,rank_pool='masters')
            for label,method,key in [('brawler','brawler_stats',lambda r:r.brawler_id),
                                     ('counter','counter_stats',lambda r:(r.brawler_id,r.partner_id)),
                                     ('synergy','synergy_stats',lambda r:tuple(sorted((r.brawler_id,r.partner_id)))),
                                     ('build','build_stats',lambda r:(r.brawler_id,r.item_kind,r.item_slug))]:
                rows=room._bestes_je_schluessel(getattr(prior,method)(query),key,ids)
                resolved[label]={'n':len(rows),'sources':dict(Counter(r.source for r in rows.values())), 'sha256':_digest(rows)}
    # Metadata only: never load raw bodies shared with other partitions.
    sources = list(queryset.values('source').annotate(n=Count('pk')).order_by('source'))
    provenance = list(models.RawPayload.objects.filter(matches__in=queryset).distinct().order_by('pk').values(
        'id','source','content_hash','format','sampling','collector_run_id'))
    report = {'schema':'legacy-train-bundle-preflight-1', **prior_gate(source_counts),
              'provider':type(provider).__name__, 'train':{'n':len(examples),'content_sha256':example_digest(examples),
                  'membership_sha256':_digest([r.fingerprint for r in examples]),
                  'first':examples[0].played_at.isoformat(),'last':examples[-1].played_at.isoformat(),'sources':sources},
              'runtime_stat_counts_not_lineage_proof':source_counts,'resolved_hideout_priors':resolved,
              'catalog_sha256':_digest(catalog),'configuration_sha256':_digest(configuration),'priors_sha256':_digest(priors),
              'source_metadata_sha256':_digest(provenance),
              'code_sha256':{str(p.relative_to(Path(__file__).resolve().parents[2])):hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted(Path(__file__).resolve().parent.rglob('*.py'))},
              'holdout_access':False,'validation_access':False,'bundle_published':False,'window_registered':False}
    return report
