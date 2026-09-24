"""Read-only feasibility/common-context audit, no predictions or outcome metrics."""
import gzip
import hashlib
import json
from pathlib import Path
from collections import Counter
from drafter.models import Match, CollectorRun
from drafter.services.prospective_acquisition import catalog_identity
from drafter.services.tagged_frontier import eligible
from drafter.services.v2_future_window import digest

bundle_path = 'data/brawl_reports/legacy-evaluation-23069ec9ec9cbbc8b7475e590c18e9548c4666395834886e12c0cd8436830527.json.gz'
assert hashlib.sha256(Path(bundle_path).read_bytes()).hexdigest() == '879c8e73449280deeeb364ebcb2ed4f8997c091237175c6c006358f2eb89dede'
bundle = json.load(gzip.open(bundle_path,'rt'))
artifact_path = Path('data/brawl_reports/v2_challenger.json')
assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == '92e0b427bf9abce62e047419ea1008f740c9ee7b39b1458ae15692402b7cf52d'
artifact = json.loads(artifact_path.read_text())
records = bundle['inputs']['catalog']
identity = []
for model, fields in (
    ('drafter.brawler', ('name','slug','external_id')),
    ('drafter.gamemode', ('name','slug','external_id')),
    ('drafter.brawlmap', ('name','slug','external_id','game_mode_id')),
    ('drafter.patch', ('name','released_on','datum_bestaetigt','datum_quelle','is_current')),
):
    for row in sorted((r for r in records if r['model']==model),key=lambda r:r['pk']):
        identity.append({'model':model,'pk':row['pk'],
            **{k:row['fields'][k if k!='game_mode_id' else 'game_mode'] for k in fields}})
assert identity == catalog_identity(), 'Current identity/resolution catalog differs from frozen D-022'
mode_keys = {'gem-grab':'gemGrab','brawl-ball':'brawlBall','knockout':'knockout',
             'heist':'heist','bounty':'bounty','hot-zone':'hotZone'}
modes = {r['pk']:mode_keys.get(r['fields']['slug']) for r in records if r['model']=='drafter.gamemode'}
maps = {r['fields']['slug']:r for r in records if r['model']=='drafter.brawlmap'}
pairs = []
for slug, context in artifact['contexts'].items():
    row = maps[slug]
    assert modes[row['fields']['game_mode']] == context['mode']
    pairs.append([row['pk'], row['fields']['game_mode']])
brawlers = sorted(r['pk'] for r in records if r['model']=='drafter.brawler'
    and artifact['catalog'].get(r['fields']['slug']) == r['pk']
    and r['fields']['ranked_verfuegbar'] and f"brawler:{r['pk']}" in artifact['model']['manifest'])
common = {'patch_policy':'frozen_algorithmic_context_not_observed_game_patch',
    'legacy_patch_id':1, 'allowed_import_patch_ids':[1],
    'actual_game_patch':'UNKNOWN_not_supplied_by_battlelog_no_patch_specific_claim',
    'legacy_reference_date':bundle['inputs']['reference_date'], 'rank_pool':'alle',
    'own_team_first_pick':True, 'side_orientation':'stored_canonical_a_vs_b',
    'map_mode_pairs':sorted(pairs), 'brawler_ids':brawlers,
    'catalog_identity_sha256':digest(identity), 'catalog_identity':identity,
    'unknown_map_mode_brawler_or_import_patch':'exclude_no_fallback_no_catalog_refresh',
    'legacy_source_revision':'223574b'}
run=CollectorRun.objects.get(pk=7)
assert run.finished_at and run.report['new_eligible_solo_ranked_matches'] > 0
matches=list(Match.objects.filter(payloads__collector_run=run,
    played_at__gt='2026-09-18T15:04:42Z').distinct().prefetch_related('players'))
valid=[m for m in matches if eligible(m)]
common_valid=[m for m in valid if [m.brawl_map_id,m.game_mode_id] in pairs
    and m.patch_id == 1 and len({p.brawler_id for p in m.players.all()})==6
    and all(p.brawler_id in brawlers for p in m.players.all())]
development={'v2_train_examples_sha256':artifact['provenance']['train']['examples_sha256'],
    'v2_validation_examples_sha256':artifact['provenance']['validation']['examples_sha256'],
    'pilot_result_file_sha256':hashlib.sha256(Path('docs/drafter-v2/DISCOVERY_PILOT_RESULT.json').read_bytes()).hexdigest(),
    'pilot_linked_membership_sha256':digest(sorted(m.fingerprint for m in matches)),
    'pilot_linked_n':len(matches), 'pilot_eligible_n':len(valid),
    'pilot_completed_at':run.finished_at.isoformat(), 'automatic_training':False,
    'old_holdout':'permanently_closed_not_read'}
print(json.dumps({'common_context':common, 'development':development,
    'development_sha256':digest(development), 'pilot_common_eligible':len(common_valid),
    'pilot_import_patch_counts':dict(Counter(m.patch_id for m in valid)),
    'prediction_or_outcome_metrics_computed':False},indent=2,sort_keys=True))
