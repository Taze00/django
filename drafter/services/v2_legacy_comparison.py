"""Experimental adapter around the exact normal Legacy response path.

No scoring, filtering or sorting here. The receipt identifies the resolved
context and loaded scoring inputs; it is not a snapshot of the entire database.
"""
import hashlib
import json
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from django.db.models import Model
from drafter import config
from drafter.services.draft_engine import DraftEngine


_TABLES = ('_stat', '_counter', '_synergie', '_build', '_spiele', '_ebenen',
           '_modus_zeilen', '_stat_prior', '_counter_prior', '_synergie_prior', '_build_prior')


def _plain(value):
    if isinstance(value, Model):
        return {f.attname: _plain(getattr(value, f.attname)) for f in value._meta.concrete_fields}
    if is_dataclass(value):
        return {f.name: _plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return [[str(k), _plain(v)] for k, v in sorted(value.items(), key=lambda pair: str(pair[0]))]
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise TypeError(f'Unsupported receipt value: {type(value).__name__}')


def _digest(value):
    return hashlib.sha256(json.dumps(_plain(value), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def compare(ctx):
    engine = DraftEngine(ctx)
    normal = engine.als_dict()  # Exactly /api/recommend/, including default depth and details.
    room = engine.raum
    inputs = {name: getattr(room, name) for name in _TABLES}
    inputs['catalog'] = room.brawler
    inputs['balance_changes'] = [list(b.balance_changes.all()) for b in room.brawler]
    inputs['map'], inputs['mode'], inputs['patch'] = ctx.brawl_map, ctx.game_mode, ctx.patch
    receipt = {
        'draft_state': normal['draft_state'],
        'resolved_ids': {'map': ctx.brawl_map.pk if ctx.brawl_map else None,
                         'mode': ctx.game_mode.pk if ctx.game_mode else None,
                         'patch': ctx.patch.pk if ctx.patch else None},
        'provider': room.quelle,
        'personal_preferences_sha256': _digest(ctx.personal),
        'personal_preferences_count': len(ctx.personal),
        'candidate_pool': sorted(normal['scores']),
        'loaded_scoring_inputs_sha256': _digest(inputs),
        'configuration_sha256': _digest({k: v for k, v in vars(config).items()
                                         if k.isupper() and type(v) in (dict, list, tuple, str, int, float, bool, type(None))}),
        'snapshot_scope': 'loaded_statistics_catalog_balance_map_mode_patch; not entire database',
        'entrypoint': 'DraftEngine(ctx).als_dict()',
    }
    receipt['context_sha256'] = _digest({'state': receipt['draft_state'], 'ids': receipt['resolved_ids'],
                                       'personal': receipt['personal_preferences_sha256']})
    return {'model_version': 'legacy-frozen-3a565bd', 'score_kind': 'heuristic_score_not_probability',
            'recommendations': normal['empfehlungen'], 'scores': normal['scores'],
            'receipt': receipt, 'data_source': normal['datenlage']}
