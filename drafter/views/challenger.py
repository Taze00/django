"""Separate experimental surface; the default recommendation endpoint is unchanged."""
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods
from drafter.models import Praxisfall, Ergebnis
from drafter.services.v2_snapshots import snapshot_token, save_snapshot
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
        result = recommend(ctx)
        if data.get('compare_legacy'):
            from drafter.services.v2_legacy_comparison import compare
            result['legacy'] = compare(ctx)
        if request.user.is_authenticated:
            result['snapshot_token'] = snapshot_token(request.user, ctx, result)
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
                             'draft': {'own': record.own_picks, 'enemy': record.enemy_picks, 'bans': record.bans}})
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict) or data.get('result') not in Ergebnis.values:
            raise ValueError('Ergebnis muss win, loss oder unknown sein.')
    except (ValueError, UnicodeDecodeError) as error:
        return JsonResponse({'fehler': str(error)}, status=400)
    updated = Praxisfall.objects.filter(pk=pk, snapshot_metadata__owner_id=request.user.pk).update(ergebnis=data['result'])
    if not updated:
        return JsonResponse({'fehler': 'Snapshot nicht gefunden.'}, status=404)
    return JsonResponse({'id': pk, 'result': data['result'], 'provenance': 'user_report_not_verified'})


@require_http_methods(['GET'])
def challenger_info(request):
    try:
        data, model, digest = load_artifact()
        return JsonResponse({'model_version': model.feature_version, 'artifact_sha256': digest,
                             'supported_maps': sorted(data['contexts']), 'status': data['status']})
    except ChallengerUnavailable as error:
        return JsonResponse({'fehler': str(error), 'status': 'MODEL_UNAVAILABLE'}, status=503)
