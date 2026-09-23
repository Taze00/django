"""Signed, user-bound experimental decision snapshots; never training inputs."""
import uuid
from django.core import signing
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drafter.models import Praxisfall

SALT = 'drafter.challenger.snapshot.v1'


def snapshot_token(user, ctx, result):
    payload = {
        'key': uuid.uuid4().hex, 'user_id': user.pk, 'at': timezone.now().isoformat(),
        'map_id': ctx.brawl_map.id, 'mode_id': ctx.game_mode.id,
        'own': [b.slug for b in ctx.own_picks], 'enemy': [b.slug for b in ctx.enemy_picks],
        'bans': [b.slug for b in ctx.bans], 'own_first': ctx.own_team_first_pick,
        'phase': 'last' if ctx.picks_gesamt == 5 else 'first' if not ctx.picks_gesamt else 'mid',
        'result': result,
    }
    return signing.dumps(payload, salt=SALT, compress=True)


def save_snapshot(user, token, chosen):
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
    if not isinstance(chosen, str) or chosen not in ranks:
        raise ValueError('Gewählter Pick fehlt in diesem Snapshot.')
    record, created = Praxisfall.objects.get_or_create(snapshot_key=payload['key'], defaults={
        'gespielt_am': parse_datetime(payload['at']), 'game_mode_id': payload['mode_id'],
        'brawl_map_id': payload['map_id'], 'draft_phase': payload['phase'],
        'eigener_first_pick': payload['own_first'], 'bans': payload['bans'],
        'own_picks': payload['own'], 'enemy_picks': payload['enemy'],
        'empfehlungen': result['recommendations'], 'gewaehlt': chosen,
        'gewaehlter_rang': ranks[chosen], 'gewaehlter_score': None,
        'modellstand': result['model_version'],
        'snapshot_metadata': {'owner_id': user.pk, 'artifact_sha256': result['artifact_sha256'],
                              'response': result, 'training_eligible': False,
                              'result_provenance': 'user_report_not_verified'},
    })
    if not created and record.gewaehlt != chosen:
        raise ValueError('Dieser Snapshot wurde bereits mit einem anderen Pick gespeichert.')
    return record, created
