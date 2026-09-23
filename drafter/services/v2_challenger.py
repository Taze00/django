"""Opt-in experimental runtime; never imports the frozen Legacy scorer."""
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.db.models import Q

from drafter.models import Brawler
from drafter.services.context import DraftFehler
from drafter.services.v2_model import CompositionLogitModel, FEATURE_VERSIONS, _feature_counts
from drafter.services.v2_explanation import contributions
from drafter.services.v2_search import _row, legal_candidates


class ChallengerUnavailable(ValueError):
    pass


def load_artifact():
    path = Path(getattr(settings, 'DRAFTER_V2_MODEL_PATH',
                        Path(settings.BASE_DIR) / 'data/brawl_reports/v2_challenger.json'))
    try:
        with path.open('rb') as stream:
            body = stream.read(16 * 1024 * 1024 + 1)
        if len(body) > 16 * 1024 * 1024:
            raise ValueError('oversized')
        data = json.loads(body)
        model = CompositionLogitModel.from_dict(data['model'])
        if (data['schema'] != 'drafter-v2-challenger-1'
                or data['status'] != 'EXPERIMENTAL_NOT_PROMOTED'
                or model.feature_version not in FEATURE_VERSIONS
                or not model.manifest or len(model.manifest) != len(model.weights)
                or set(model.manifest.values()) != set(range(len(model.weights)))
                or any(type(i) is not int for i in model.manifest.values())
                or any(type(w) not in (int, float) or not math.isfinite(w) for w in model.weights)
                or any(type(i) is not int or i < 1 for i in data['catalog'].values())
                or any(type(n) is not int or n < 1 for n in data['feature_support'].values())
                or set(data['feature_support']) != set(model.manifest)
                or any(type(data['provenance'][part]['n']) is not int or data['provenance'][part]['n'] < 1 for part in ('train', 'validation'))
                or not isinstance(data['limitations'], list)
                or any(not isinstance(item, str) for item in data['limitations'])
                or not isinstance(data['contexts'], dict)):
            raise ValueError('invalid contract')
        for context in data['contexts'].values():
            if not all(isinstance(context[k], str) and context[k] for k in ('mode', 'map_name')):
                raise ValueError('invalid context')
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError) as error:
        raise ChallengerUnavailable('V2-Modell fehlt oder ist ungültig; kein Legacy-Fallback.') from error
    return data, model, hashlib.sha256(body).hexdigest()


def recommend(ctx):
    started = perf_counter()
    if not ctx.brawl_map:
        raise DraftFehler('V2 benötigt eine Map.')
    if len(ctx.own_picks) != 2 or len(ctx.enemy_picks) != 3:
        raise DraftFehler('V2 Last Pick benötigt zwei eigene und drei gegnerische Picks.')
    data, model, artifact_digest = load_artifact()
    context = data['contexts'].get(ctx.brawl_map.slug)
    if context is None:
        raise ChallengerUnavailable('Für diese Map fehlt ein eindeutiger Trainingskontext.')
    catalog = list(Brawler.objects.filter(Q(is_active=True) | Q(external_id__isnull=False)))
    if any(b.slug in data['catalog'] and data['catalog'][b.slug] != b.id for b in catalog):
        raise ChallengerUnavailable('Modell und Brawler-Katalog haben unterschiedliche Identitäten.')
    all_picks = ctx.own_picks + ctx.enemy_picks
    if any(not b.ranked_verfuegbar for b in all_picks):
        raise DraftFehler('Ein gewählter Brawler ist nicht Ranked-verfügbar.')
    if any(data['catalog'].get(b.slug) != b.id for b in all_picks):
        raise ChallengerUnavailable('Ein gewählter Brawler fehlt im Modellkatalog.')
    by_id = {b.id: b for b in catalog if b.ranked_verfuegbar}
    own, enemy = tuple(b.id for b in ctx.own_picks), tuple(b.id for b in ctx.enemy_picks)
    candidates = legal_candidates(by_id, own, enemy, tuple(b.id for b in ctx.bans))
    result, unavailable = [], []
    for candidate in candidates:
        brawler = by_id[candidate]
        if data['catalog'].get(brawler.slug) != candidate or f'brawler:{candidate}' not in model.manifest:
            unavailable.append(brawler.slug)
            continue
        row = _row(own + (candidate,), enemy, **context)
        features = _feature_counts(row, model.feature_version)
        unknown = sorted(set(features) - set(model.manifest))
        result.append({
            'slug': brawler.slug, 'name': brawler.name, 'p_win': model.predict(row),
            'contributions': contributions(model, row, limit=8),
            'evidence': {'kind': 'jointly_fitted_association_not_causal',
                         'feature_support': {name: data['feature_support'].get(name) for name in features},
                         'unknown_features': unknown},
            'uncertainty': {'status': 'UNKNOWN', 'interval': None},
        })
    result.sort(key=lambda item: (-item['p_win'], item['slug']))
    return {
        'engine': 'v2_challenger', 'status': 'EXPERIMENTAL_NOT_PROMOTED',
        'model_version': model.feature_version, 'artifact_sha256': artifact_digest,
        'recommendations': result, 'unavailable_candidates': unavailable,
        'provenance': {name: {k: v for k, v in data['provenance'][name].items() if k != 'fingerprints'}
                       for name in ('train', 'validation')},
        'limitations': data['limitations'], 'context': context,
        'elapsed_ms': round((perf_counter() - started) * 1000, 3),
    }
