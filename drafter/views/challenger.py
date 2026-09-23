"""Separate experimental surface; the default recommendation endpoint is unchanged."""
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from drafter.services.anfrage import context_aus_daten
from drafter.services.context import DraftFehler
from drafter.services.v2_challenger import ChallengerUnavailable, recommend


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
        ctx = context_aus_daten(data, request)
        return JsonResponse(recommend(ctx))
    except (UnicodeDecodeError, json.JSONDecodeError, DraftFehler) as error:
        return JsonResponse({'fehler': str(error)}, status=400)
    except ChallengerUnavailable as error:
        return JsonResponse({'fehler': str(error), 'status': 'MODEL_UNAVAILABLE'}, status=503)
