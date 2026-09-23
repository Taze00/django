"""Signed, user-bound experimental decision snapshots; never training inputs."""
import uuid
import hashlib
import json
from django.db import transaction
from django.core import signing
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drafter.models import Praxisfall

SALT = 'drafter.challenger.snapshot.v1'


def response_digest(value):
    # PostgreSQL JSONB normalizes integral floats (including -0.0) to integers.
    def normalize(item):
        if isinstance(item, dict):
            return {key: normalize(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)):
            return [normalize(val) for val in item]
        if isinstance(item, float) and item.is_integer():
            return int(item)
        return item
    return hashlib.sha256(json.dumps(normalize(value), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def snapshot_token(user, ctx, result):
    payload = {
        'key': uuid.uuid4().hex, 'user_id': user.pk, 'at': timezone.now().isoformat(),
        'map_id': ctx.brawl_map.id, 'mode_id': ctx.game_mode.id,
        'own': [b.slug for b in ctx.own_picks], 'enemy': [b.slug for b in ctx.enemy_picks],
        'bans': [b.slug for b in ctx.bans], 'own_first': ctx.own_team_first_pick,
        'phase': 'last' if ctx.picks_gesamt == 5 else 'first' if not ctx.picks_gesamt else 'mid',
        'result': result, 'draft_context': ctx.als_dict(),
    }
    return signing.dumps(payload, salt=SALT, compress=True)


def save_snapshot(user, token, chosen=None):
    if not isinstance(token, str) or len(token) > 2_000_000:
        raise ValueError('Ungültiger Snapshot.')
    try:
        payload = signing.loads(token, salt=SALT, max_age=7200)
    except signing.BadSignature as error:
        raise ValueError('Snapshot ungültig oder abgelaufen; erneut berechnen.') from error
    if payload['user_id'] != user.pk:
        raise ValueError('Snapshot gehört zu einem anderen Nutzer.')
    result = payload['result']
    ranks = {r['slug']: i for i, r in enumerate(result['recommendations'], 1)}
    if chosen is not None and (not isinstance(chosen, str) or chosen not in ranks):
        raise ValueError('Gewählter Pick fehlt in diesem Snapshot.')
    record, created = Praxisfall.objects.get_or_create(snapshot_key=payload['key'], defaults={
        'gespielt_am': parse_datetime(payload['at']), 'game_mode_id': payload['mode_id'],
        'brawl_map_id': payload['map_id'], 'draft_phase': payload['phase'],
        'eigener_first_pick': payload['own_first'], 'bans': payload['bans'],
        'own_picks': payload['own'], 'enemy_picks': payload['enemy'],
        'empfehlungen': result['recommendations'], 'gewaehlt': chosen or '',
        'gewaehlter_rang': ranks.get(chosen), 'gewaehlter_score': None,
        'modellstand': result['model_version'],
        'snapshot_metadata': {'owner_id': user.pk, 'artifact_sha256': result['artifact_sha256'],
                              'response': result, 'training_eligible': False,
                              'result_provenance': 'user_report_not_verified',
                              'schema': 'drafter-shadow-1',
                              'draft_context': payload.get('draft_context'),
                              'response_sha256': response_digest(result),
                              'capture_provenance': result.get('observation', {'sampling': 'manual_selected_pick'}),
                              'captured_at': payload['at'],
                              'played_at_provenance': 'UNKNOWN; gespielt_am is recommendation time',
                              'events': ([{'at': timezone.now().isoformat(), 'chosen': chosen,
                                           'provenance': 'user_report_not_verified'}] if chosen else [])},
    })
    if not created and chosen is not None and record.gewaehlt != chosen:
        raise ValueError('Dieser Snapshot wurde bereits mit einem anderen Pick gespeichert.')
    return record, created


@transaction.atomic
def report_observation(user, pk, data):
    """Append user reports; immutable recommendations never recomputed or edited."""
    if not isinstance(data, dict) or not set(data) <= {'chosen', 'result'} or not data:
        raise ValueError('Pick oder Ergebnis angeben.')
    record = Praxisfall.objects.select_for_update().filter(pk=pk, snapshot_metadata__owner_id=user.pk).first()
    if record is None:
        return None
    if 'result' in data and data['result'] not in ('win', 'loss', 'unknown'):
        raise ValueError('Ergebnis muss win, loss oder unknown sein.')
    response = record.snapshot_metadata['response']
    ranks = {r['slug']: i for i, r in enumerate(response['recommendations'], 1)}
    legal = response.get('legacy', {}).get('receipt', {}).get('candidate_pool', list(ranks))
    chosen = data.get('chosen', record.gewaehlt)
    if 'chosen' in data and (not isinstance(chosen, str) or chosen not in legal):
        raise ValueError('Pick fehlt im archivierten legalen Kandidatenpool.')
    if data.get('result') in ('win', 'loss') and not chosen:
        raise ValueError('Zuerst tatsächlich gewählten Pick angeben.')
    changed = ('chosen' in data and chosen != record.gewaehlt) or ('result' in data and data['result'] != record.ergebnis)
    if changed:
        metadata = dict(record.snapshot_metadata)
        metadata['events'] = [*metadata.get('events', []), {'at': timezone.now().isoformat(),
                              **data, 'provenance': 'user_report_not_verified'}]
        if 'chosen' in data:
            record.gewaehlt = chosen
            record.gewaehlter_rang = ranks.get(chosen)
        if 'result' in data:
            record.ergebnis = data['result']
        record.snapshot_metadata = metadata
        record.save(update_fields=['gewaehlt', 'gewaehlter_rang', 'ergebnis', 'snapshot_metadata'])
    return record
