"""Run via isolated manage.py shell; read-only runtime diagnostic, not evaluation.

Same anonymous session, DB transaction, map/mode, side, picks and empty bans.
No Match/RawPayload, training/evaluation command, credential or external request.
"""
import json
from django.db import connection, transaction
from django.test import Client, override_settings
from drafter.services.v2_diagnostics import compare_candidates

payload = {'map': 'hideout', 'mode': 'bounty', 'own_picks': ['mortis', 'gene'],
           'enemy_picks': ['piper', 'amber', 'pearl'], 'bans': [],
           'own_team_first_pick': False, 'compare_legacy': True}
with transaction.atomic(), override_settings(ALLOWED_HOSTS=['testserver']):
    with connection.cursor() as cursor:
        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    client = Client()
    normal_response = client.post('/draft/api/recommend/', json.dumps(payload), content_type='application/json')
    response = client.post('/draft/api/challenger/', json.dumps(payload), content_type='application/json')
    if normal_response.status_code != 200 or response.status_code != 200:
        raise RuntimeError('Diagnostic endpoints failed; no ranking comparison possible')
    normal, challenger = normal_response.json(), response.json()
    legacy = challenger['legacy']
    assert normal['empfehlungen'] == legacy['recommendations']
    assert normal['scores'] == legacy['scores']
    assert normal['draft_state'] == legacy['receipt']['draft_state']
    assert normal['datenlage'] == legacy['data_source']
    selected = {r['slug']: r for r in challenger['recommendations']}
    first_true = client.post('/draft/api/recommend/', json.dumps({**payload, 'own_team_first_pick': True}), content_type='application/json').json()
    report = {
        'kind': 'runtime_diagnostic_not_outcome_evaluation', 'request': payload,
        'legacy_identical': True, 'legacy_receipt': legacy['receipt'],
        'normal_legacy_top': [{'slug': r['slug'], 'score': r['score'], 'score_roh': r['score_roh']} for r in normal['empfehlungen']],
        'normal_first_pick_true_top': [r['slug'] for r in first_true['empfehlungen']],
        'v2_artifact_sha256': challenger['artifact_sha256'], 'v2_model': challenger['model_version'],
        'v2_top': [{'slug': r['slug'], 'p_win': r['p_win']} for r in challenger['recommendations'][:4]],
        'v2_diagnostics': {slug: selected[slug]['diagnostic'] for slug in ('wendy', 'shade', 'gus', 'belle') if slug in selected},
        'explicit_comparisons': {slug: compare_candidates(selected['wendy'], selected[slug]) for slug in ('gus', 'belle') if 'wendy' in selected and slug in selected},
        'limitation': 'User-reported Sprout/Carl/Gray order not reproduced locally; other instance/session inputs unavailable, no inferred cause.',
    }
    print(json.dumps(report, sort_keys=True, indent=2))
