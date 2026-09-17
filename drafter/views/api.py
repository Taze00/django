"""JSON-Schnittstelle des Drafters.

Bewusst **kein** DRF: das Projekt stellt DRF global auf JWT und
`IsAuthenticated` (siehe settings REST_FRAMEWORK) - das ist fuer CORVIS
richtig und fuer eine oeffentlich nutzbare Draft-Seite falsch. Statt
diese Voreinstellungen in jeder View zu ueberschreiben, benutzt der
Drafter schlichte Django-Views mit Session und CSRF. Weniger
beweglicher Teile, keine Wechselwirkung mit der Fitness-API.

Alle Endpunkte antworten auch im Fehlerfall mit JSON - die Oberflaeche
soll einen Fehlertext anzeigen koennen und nicht auf eine HTML-Seite
laufen.
"""

import json

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from drafter import attributes as attr
from drafter import config
from drafter.models import Brawler, BrawlMap, GameMode
from drafter.services.anfrage import context_aus_daten
from drafter.services.context import DraftFehler
from drafter.services.draft_engine import DraftEngine
from drafter.services import personal


def _rumpf(request):
    try:
        return json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        raise DraftFehler("Ungültiges JSON im Request")


def _fehler(nachricht, status=400):
    return JsonResponse({"fehler": str(nachricht)}, status=status)


def katalog(request):
    """Brawler, Modi und Maps - einmal beim Laden der Seite.

    Die Oberflaeche haelt danach alles im Speicher. Ein Klick auf einen
    Pick loest deshalb genau eine Anfrage aus (die Empfehlung) und nicht
    zusaetzlich Nachschlagen von Namen und Bildern.
    """
    # Der VOLLE Katalog: alle aktiven Brawler plus alle, die die offizielle
    # API kennt (external_id gesetzt). Letztere haben oft kein gepflegtes
    # Profil und sind deshalb inaktiv - die Engine bewertet und empfiehlt
    # sie nicht, und die Oberflaeche markiert sie als "Limited Data".
    # Waehlen, bannen und suchen muss man sie trotzdem koennen: sie sind
    # im Spiel, also auch im echten Draft.
    brawler = [
        {
            "slug": b.slug,
            "name": _anzeigename(b.name),
            "rolle": b.role,
            "rollen": b.rollen_label,
            "tags": b.alle_rollen,
            "farbe": b.color,
            "initialen": b.initialen,
            "image_url": b.image_url,
            "ist_demo": b.is_demo,
            "limited": not b.is_active,
            # Im Ranked-Modus nicht waehlbar - bleibt im Katalog, wird aber
            # nie empfohlen und zaehlt nirgends als fehlende Datenlage.
            "ranked_verfuegbar": b.ranked_verfuegbar,
            "draft_rolle": b.draft_rolle_label,
            "draft_faehigkeiten": list(b.draft_faehigkeiten or []),
        }
        for b in Brawler.objects.filter(
            Q(is_active=True) | Q(external_id__isnull=False)
        ).order_by("name")
    ]
    modi = [
        {
            "slug": m.slug,
            "name": m.name,
            "beschreibung": m.description,
            "maps": [
                {"slug": k.slug, "name": k.name, "notiz": k.notes,
                 "image_url": k.image_url}
                for k in m.maps.filter(is_active=True)
            ],
        }
        for m in GameMode.objects.filter(is_active=True).prefetch_related("maps")
    ]
    return JsonResponse({
        "brawler": brawler,
        "modi": modi,
        "rang_pools": [{"key": k, "label": v} for k, v in config.RANG_POOLS],
        # Das Rollen-Vokabular in seiner kanonischen Reihenfolge. Die
        # Oberflaeche baute den Rollenfilter vorher aus den Tags der
        # geladenen Brawler und sortierte alphabetisch - damit hiessen
        # die Knoepfe "damage" statt "Damage Dealer", und ihre Reihenfolge
        # hing davon ab, welche Brawler gerade gepflegt sind.
        "rollen": [{"key": k, "label": v} for k, v in attr.ROLLEN],
        "persoenlich": {
            b.slug: eintrag["confidence"]
            for b, eintrag in _persoenliche_paare(request)
        },
        "angemeldet": request.user.is_authenticated,
    })


# Namen, die .title() falsch schreibt (Abkuerzungen).
_NAMEN_SONDERFAELLE = {"EMZ": "EMZ", "R-T": "R-T"}


def _anzeigename(name):
    """Namen aus der API kommen in Grossbuchstaben ("EL PRIMO") - fuer die
    Kachel lesbar schreiben. Gepflegte Namen bleiben, wie sie sind."""
    if name != name.upper():
        return name
    return _NAMEN_SONDERFAELLE.get(name, name.title())


def _persoenliche_paare(request):
    alle = list(Brawler.objects.filter(is_active=True))
    werte = personal.laden(request, alle)
    nach_id = {b.id: b for b in alle}
    return [(nach_id[bid], eintrag) for bid, eintrag in werte.items() if bid in nach_id]


@require_POST
def empfehlen(request):
    """Der Hauptendpunkt: Draftzustand rein, Empfehlungen raus."""
    try:
        ctx = context_aus_daten(_rumpf(request), request)
        return JsonResponse(DraftEngine(ctx).als_dict())
    except DraftFehler as fehler:
        return _fehler(fehler)


@require_POST
def endanalyse(request):
    """Der Matchplan nach abgeschlossenem Draft."""
    try:
        daten = _rumpf(request)
        ctx = context_aus_daten(daten, request)
        if not ctx.own_picks:
            raise DraftFehler("Für den Matchplan wird mindestens ein eigener Pick gebraucht")
        return JsonResponse({
            "draft_state": ctx.als_dict(),
            "endanalyse": DraftEngine(ctx).endanalyse(),
        })
    except DraftFehler as fehler:
        return _fehler(fehler)


@require_POST
def detail(request):
    """Vollstaendige Begruendung fuer einen einzelnen Brawler."""
    try:
        daten = _rumpf(request)
        slug = daten.get("brawler")
        if not isinstance(slug, str):
            raise DraftFehler("'brawler' fehlt")
        brawler = Brawler.objects.filter(slug=slug, is_active=True).first()
        if brawler is None:
            raise DraftFehler(f"Unbekannter Brawler '{slug}'")

        ctx = context_aus_daten(daten, request)
        if brawler.id in ctx.gesperrte_ids:
            raise DraftFehler(f"{brawler.name} ist bereits gepickt oder gebannt")

        empfehlung = DraftEngine(ctx).detail(brawler)
        if empfehlung is None:
            raise DraftFehler("Keine Bewertung möglich")
        return JsonResponse(empfehlung.als_dict(ausfuehrlich=True))
    except DraftFehler as fehler:
        return _fehler(fehler)


@require_POST
def confidence_speichern(request):
    """Persoenliche Sicherheit zu einem Brawler speichern.

    Angemeldet: dauerhaft in der Datenbank. Als Gast: in der Session,
    damit der Drafter ohne Konto benutzbar bleibt - der Wert ist dann
    an diesen Browser gebunden und verschwindet mit ihm.
    """
    from drafter.models import UserBrawlerPreference

    try:
        daten = _rumpf(request)
        slug = daten.get("brawler")
        wert = daten.get("confidence")
        brawler = Brawler.objects.filter(slug=slug, is_active=True).first()
        if brawler is None:
            raise DraftFehler(f"Unbekannter Brawler '{slug}'")
        try:
            wert = int(wert)
        except (TypeError, ValueError):
            raise DraftFehler("'confidence' muss eine Zahl zwischen 0 und 100 sein")
        wert = max(0, min(100, wert))

        if request.user.is_authenticated:
            # Nur die eigenen Werte - der Nutzer kommt aus der Session,
            # nie aus dem Request.
            UserBrawlerPreference.objects.update_or_create(
                user=request.user, brawler=brawler,
                defaults={"confidence": wert, "avoid": bool(daten.get("avoid", False))},
            )
            gespeichert = "konto"
        else:
            werte = dict(request.session.get(personal.SESSION_SCHLUESSEL) or {})
            werte[brawler.slug] = wert
            request.session[personal.SESSION_SCHLUESSEL] = werte
            gespeichert = "session"

        return JsonResponse({"ok": True, "brawler": brawler.slug,
                             "confidence": wert, "gespeichert": gespeichert})
    except DraftFehler as fehler:
        return _fehler(fehler)
