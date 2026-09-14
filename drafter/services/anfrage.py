"""Vom JSON-Request zum DraftContext.

Eine eigene Datei, damit die Views nichts weiter tun als: parsen,
Engine fragen, antworten. Hier steht die gesamte Eingabepruefung -
inklusive der Obergrenzen, die verhindern, dass ein manipulierter
Request die Engine mit 500 Picks beschaeftigt.

Grundhaltung: **nichts aus dem Request wird ungeprueft uebernommen.**
Unbekannte Slugs werden zu einem Fehler mit klarem Text, nicht still
ignoriert - sonst rechnet die Engine mit einem anderen Draft als dem,
den der Nutzer sieht.
"""

from drafter import config
from drafter.models import BrawlMap, Brawler, GameMode, Patch
from drafter.services.context import BANS_JE_TEAM, PICKS_JE_TEAM, DraftContext, DraftFehler
from drafter.services import personal

# Obergrenze fuer eingehende Listen, bevor ueberhaupt etwas nachgeschlagen wird.
MAX_LISTE = 10


def _slug_liste(daten, feld, maximal):
    roh = daten.get(feld) or []
    if not isinstance(roh, list):
        raise DraftFehler(f"'{feld}' muss eine Liste sein")
    if len(roh) > maximal:
        raise DraftFehler(f"'{feld}': hoechstens {maximal} Einträge")
    slugs = []
    for eintrag in roh[:MAX_LISTE]:
        if not isinstance(eintrag, str) or len(eintrag) > 60:
            raise DraftFehler(f"'{feld}': ungültiger Eintrag")
        slugs.append(eintrag)
    return slugs


def _aufloesen(slugs, nach_slug, feld):
    brawler = []
    for slug in slugs:
        b = nach_slug.get(slug)
        if b is None:
            raise DraftFehler(f"'{feld}': unbekannter Brawler '{slug}'")
        brawler.append(b)
    return tuple(brawler)


def context_aus_daten(daten, request=None):
    """Baut den DraftContext aus dem JSON-Rumpf eines Requests."""
    if not isinstance(daten, dict):
        raise DraftFehler("Erwartet wird ein JSON-Objekt")

    map_slug = daten.get("map")
    mode_slug = daten.get("mode")

    karte = None
    modus = None
    if map_slug:
        karte = BrawlMap.objects.filter(slug=map_slug, is_active=True).select_related(
            "game_mode"
        ).first()
        if karte is None:
            raise DraftFehler(f"Unbekannte Map '{map_slug}'")
        modus = karte.game_mode
    elif mode_slug:
        modus = GameMode.objects.filter(slug=mode_slug, is_active=True).first()
        if modus is None:
            raise DraftFehler(f"Unbekannter Modus '{mode_slug}'")

    eigene_slugs = _slug_liste(daten, "own_picks", PICKS_JE_TEAM)
    gegner_slugs = _slug_liste(daten, "enemy_picks", PICKS_JE_TEAM)
    ban_slugs = _slug_liste(daten, "bans", BANS_JE_TEAM * 2)

    alle = set(eigene_slugs) | set(gegner_slugs) | set(ban_slugs)
    nach_slug = {b.slug: b for b in Brawler.objects.filter(slug__in=alle)}

    rang_pool = daten.get("rank_pool") or config.RANG_POOL_STANDARD
    if rang_pool not in dict(config.RANG_POOLS):
        rang_pool = config.RANG_POOL_STANDARD

    alle_brawler = list(Brawler.objects.filter(is_active=True))
    ctx = DraftContext(
        game_mode=modus,
        brawl_map=karte,
        own_picks=_aufloesen(eigene_slugs, nach_slug, "own_picks"),
        enemy_picks=_aufloesen(gegner_slugs, nach_slug, "enemy_picks"),
        bans=_aufloesen(ban_slugs, nach_slug, "bans"),
        own_team_first_pick=bool(daten.get("own_team_first_pick", True)),
        patch=Patch.aktueller(),
        rank_pool=rang_pool,
        user=getattr(request, "user", None),
        personal=personal.laden(request, alle_brawler),
    )
    ctx.pruefe()
    return ctx
