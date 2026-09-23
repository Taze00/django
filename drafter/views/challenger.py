"""Separate experimental surface; the default recommendation endpoint is unchanged."""
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods
from drafter.models import Praxisfall, Ergebnis
from drafter.services.v2_snapshots import snapshot_token, save_snapshot, report_observation
from drafter.services.anfrage import context_aus_daten
from drafter.services.context import DraftFehler
from drafter.services.v2_challenger import ChallengerUnavailable, recommend, load_artifact


@ensure_csrf_cookie
def challenger(request):
    return render(request, 'drafter/challenger.html')


@require_POST
def challenger_recommend(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise DraftFehler('Erwartet wird ein JSON-Objekt.')
        for field in ('map', 'mode'):
            if field in data and (not isinstance(data[field], str) or len(data[field]) > 100):
                raise DraftFehler(f'Ungültiges Feld: {field}')
        if type(data.get('own_team_first_pick', True)) is not bool:
            raise DraftFehler('First Pick muss true oder false sein.')
        ctx = context_aus_daten(data, request)
        if type(data.get('compare_legacy', False)) is not bool:
            raise DraftFehler('Legacy-Vergleich muss true oder false sein.')
        shadow = data.get('shadow_capture', False)
        if type(shadow) is not bool:
            raise DraftFehler('Shadow-Protokoll muss true oder false sein.')
        if shadow and not request.user.is_authenticated:
            return JsonResponse({'fehler': 'Für Shadow-Protokoll bitte anmelden.'}, status=403)
        result = recommend(ctx)
        if data.get('compare_legacy') or shadow:
            from drafter.services.v2_legacy_comparison import compare
            result['legacy'] = compare(ctx)
        if shadow:
            result['observation'] = {
                'sampling': 'opt_in_request_before_choice', 'source': 'user_entered_draft',
                'real_match_verified': False, 'recommendation_exposure': 'both_engines_returned_display_unverified',
                'selection_bias': ['self_selected_users', 'self_selected_requests', 'recommendation_exposure', 'optional_outcome_reporting'],
                'training_eligible': False, 'independent_test_eligible': False,
            }
        if request.user.is_authenticated:
            token = snapshot_token(request.user, ctx, result)
            if shadow:
                record, _ = save_snapshot(request.user, token)
                result['snapshot_id'] = record.pk
            result['snapshot_token'] = token
        return JsonResponse(result)
    except (UnicodeDecodeError, json.JSONDecodeError, DraftFehler) as error:
        return JsonResponse({'fehler': str(error)}, status=400)
    except ChallengerUnavailable as error:
        return JsonResponse({'fehler': str(error), 'status': 'MODEL_UNAVAILABLE'}, status=503)


@require_http_methods(['GET', 'POST'])
def challenger_snapshots(request):
    if not request.user.is_authenticated:
        return JsonResponse({'fehler': 'Zum Speichern bitte anmelden.'}, status=403)
    if request.method == 'GET':
        records = Praxisfall.objects.filter(snapshot_metadata__owner_id=request.user.pk).order_by('-id')[:20]
        return JsonResponse({'snapshots': [{'id': r.id, 'chosen': r.gewaehlt, 'result': r.ergebnis,
                                           'model_version': r.modellstand, 'at': r.gespielt_am.isoformat()}
                                          for r in records]})
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError('Erwartet wird ein JSON-Objekt.')
        record, created = save_snapshot(request.user, data.get('token'), data.get('chosen'))
        return JsonResponse({'id': record.id, 'created': created}, status=201 if created else 200)
    except (ValueError, UnicodeDecodeError) as error:
        return JsonResponse({'fehler': str(error)}, status=400)


@require_http_methods(['GET', 'POST'])
def challenger_result(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'fehler': 'Bitte anmelden.'}, status=403)
    if request.method == 'GET':
        record = Praxisfall.objects.filter(pk=pk, snapshot_metadata__owner_id=request.user.pk).first()
        if record is None:
            return JsonResponse({'fehler': 'Snapshot nicht gefunden.'}, status=404)
        return JsonResponse({'id': pk, 'result': record.ergebnis,
                             'snapshot': record.snapshot_metadata['response'],
                             'metadata': {k: v for k, v in record.snapshot_metadata.items() if k not in ('response', 'owner_id')},
                             'draft': {'own': record.own_picks, 'enemy': record.enemy_picks, 'bans': record.bans}})
    try:
        data = json.loads(request.body)
        record = report_observation(request.user, pk, data)
    except (ValueError, UnicodeDecodeError) as error:
        return JsonResponse({'fehler': str(error)}, status=400)
    if record is None:
        return JsonResponse({'fehler': 'Snapshot nicht gefunden.'}, status=404)
    return JsonResponse({'id': pk, 'chosen': record.gewaehlt, 'result': record.ergebnis,
                         'provenance': 'user_report_not_verified'})


@require_http_methods(['GET'])
def challenger_info(request):
    try:
        data, model, digest = load_artifact()
        return JsonResponse({'model_version': model.feature_version, 'artifact_sha256': digest,
                             'supported_maps': sorted(data['contexts']), 'status': data['status']})
    except ChallengerUnavailable as error:
        return JsonResponse({'fehler': str(error), 'status': 'MODEL_UNAVAILABLE'}, status=503)
