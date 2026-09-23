"""Exact additive attribution, distinct from gameplay/counterfactual evidence.

Never evaluates partial teams. Removing the root candidate below only partitions
the feature vector algebraically; no partial-team probability is computed.
"""
from dataclasses import replace
from drafter.services.v2_model import _feature_counts, OPPONENT_VERSION

FAMILIES = ('individual', 'mode', 'map', 'teammate', 'enemy')
PREFIX = {'brawler': 'individual', 'brawler_context': 'mode', 'brawler_map': 'map',
          'pair': 'teammate', 'opponent': 'enemy'}
LABELS = {'individual': 'Brawler-Beitrag', 'mode': 'Modus-Beitrag', 'map': 'Map-Beitrag',
          'teammate': 'Gelernte Team-Paarterme', 'enemy': 'Gegnerspezifische Paarterme'}


def _weighted(model, features):
    return sum(model.weights[model.manifest[name]] * amount for name, amount in features.items() if name in model.manifest)


def diagnose(model, row, candidate, support, names, continuation):
    full = _feature_counts(row, model.feature_version)
    background = _feature_counts(replace(row, team_a=tuple(b for b in row.team_a if b != candidate)), model.feature_version)
    root = {key: amount - background.get(key, 0) for key, amount in full.items()
            if amount != background.get(key, 0)}
    families = {}
    for family in FAMILIES:
        active = family != 'enemy' or model.feature_version == OPPONENT_VERSION
        terms = []
        for key, amount in root.items():
            prefix, rest = key.split(':', 1)
            if PREFIX[prefix] != family:
                continue
            known = key in model.manifest
            ids = rest.split(':') if prefix in ('pair', 'opponent') else [rest.rsplit(':', 1)[-1]]
            terms.append({'feature': key, 'subjects': [names.get(i, 'UNKNOWN') for i in ids],
                          'amount': amount, 'weight': model.weights[model.manifest[key]] if known else None,
                          'logit_contribution': amount * model.weights[model.manifest[key]] if known else None,
                          'training_matches': support.get(key), 'status': 'LEARNED' if known else 'UNKNOWN'})
        unknown = sum(t['status'] == 'UNKNOWN' for t in terms)
        families[family] = {'label': LABELS[family], 'active': active,
                            'status': 'INACTIVE' if not active else 'PARTIAL' if unknown else 'LEARNED',
                            'modeled_logit': sum(t['logit_contribution'] for t in terms if t['logit_contribution'] is not None) if active else None,
                            'unknown_terms': unknown, 'terms': terms,
                            'interpretation': 'association; independent feature benefit not established' if active else 'not included in active model'}
    total = _weighted(model, full)
    root_total = _weighted(model, root)
    return {
        'families': families, 'candidate_logit': root_total,
        'background_logit': total - root_total, 'total_logit': total,
        'search': {'active': bool(continuation), 'status': 'HYPOTHETICAL_CONTINUATION' if continuation else 'LAST_PICK_NO_FUTURE_MOVES',
                   'independent_bonus': False},
        'missing_evidence': ['mechanics/terrain/roles not modeled', 'uncertainty interval UNKNOWN',
                             'current patch applicability UNKNOWN', 'no causal or independently validated family attribution'],
        'ranking_limit': ('Bei diesem Last Pick unterscheiden nur additive gelernte Brawler-, Map-/Modus- und Team-Paarterme die Kandidaten. '
                          'Keine aktive gegnerspezifische Pick-Interaktion; keine belegte Anti-Tank-, Kontroll- oder Rollenbegründung.'
                          if model.feature_version != OPPONENT_VERSION and not continuation else
                          'Additive Modellterme der ausgewiesenen vollständigen Komposition; keine kausale Taktikbegründung.'),
    }


def compare_candidates(candidate, reference):
    a, b = candidate['diagnostic'], reference['diagnostic']
    groups = {family: (a['families'][family]['modeled_logit'] - b['families'][family]['modeled_logit'])
              if a['families'][family]['active'] and b['families'][family]['active'] else None
              for family in FAMILIES}
    future = bool(candidate['continuation'] or reference['continuation'])
    return {'reference_slug': reference['slug'], 'reference_name': reference['name'],
            'probability_difference_pp': 100 * (candidate['p_win'] - reference['p_win']),
            'total_logit_difference': a['total_logit'] - b['total_logit'],
            'candidate_family_logit_differences': groups,
            'background_logit_difference': a['background_logit'] - b['background_logit'],
            'background_interpretation': 'different_hypothetical_continuations' if future else 'shared_fixed_draft_cancels',
            'uncertainty_of_difference': 'UNKNOWN',
            'interpretation': 'exact_model_decomposition_not_causal_effect_or_significance'}
