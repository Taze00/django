"""Die Seiten des Drafters.

Drei Stueck, alle bewusst duenn: rendern und den Katalog mitgeben. Die
gesamte Draft-Logik laeuft ueber die JSON-Schnittstelle, damit ein Klick
auf einen Pick keine Seite neu laedt.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from drafter import attributes as attr
from drafter.models import Brawler, BrawlMap, GameMode, UserBrawlerPreference
from drafter.services import personal


def _datenlage():
    """Woher die Zahlen kommen - fuer den Hinweis ueber dem Draft.

    Zwei getrennte Aussagen, weil sie getrennt wahr sind: die
    STATISTIKEN sind gemessen, die BRAWLERPROFILE (Eigenschaften,
    Draft-Werte) stammen weiterhin aus dem Demo-Seed.
    """
    from drafter import config
    from drafter.models import Brawler, Datenquelle
    from drafter.models.matches import Match
    from drafter.services.providers.registry import hole_stat_provider

    provider = hole_stat_provider()
    gemessen = provider.name != "demo"
    partien = Match.objects.filter(
        is_ranked=True,
        battle_type__in=config.DRAFT_STATISTIK_BATTLE_TYPEN).count() if gemessen else 0
    demo_profile = Brawler.objects.filter(source=Datenquelle.DEMO).exclude(
        attributes={}).count()
    return {
        "provider": provider.name,
        "gemessen": gemessen,
        "partien": partien,
        "demo_profile": demo_profile,
    }


def draft(request):
    """Die Draft-Oberflaeche unter /draft/."""
    return render(request, "drafter/draft.html", {
        # Nur Modi mit waehlbarer Map - siehe views/api.py.
        "modi": [m for m in GameMode.objects.filter(is_active=True)
                 .prefetch_related("maps") if m.maps.waehlbare().exists()],
        # Ob der Map-Knopf Platz fuer ein Vorschaubild reservieren muss.
        # Steht schon im HTML, damit der Knopftext nicht nach dem Laden
        # des Katalogs um die Bildbreite nach rechts springt.
        "karten_mit_bild": BrawlMap.objects.waehlbare().exclude(image_url="").exists(),
        # Die Datenlage steht auf der Seite, weil sie sich aendert. Bis
        # zum 2026-09-20 stand dort ein fest verdrahteter Demo-Hinweis -
        # er blieb stehen, als die Seite laengst mit gemessenen Statistiken
        # rechnete, und behauptete damit das Gegenteil der Wahrheit.
        "datenlage": _datenlage(),
    })


@login_required
def meine_brawler(request):
    """Confidence-Pflege fuer angemeldete Nutzer.

    Bewusst serverseitig gerendert und nicht Teil der Draft-Oberflaeche:
    hier wird gepflegt, dort gedraftet. Wer nicht angemeldet ist, landet
    ueber LOGIN_URL auf der Anmeldeseite des Drafters.
    """
    brawler = list(Brawler.objects.filter(is_active=True))
    vorhandene = {
        p.brawler_id: p
        for p in UserBrawlerPreference.objects.filter(user=request.user)
    }
    eintraege = [
        {
            "brawler": b,
            "confidence": vorhandene[b.id].confidence if b.id in vorhandene else 50,
            "avoid": vorhandene[b.id].avoid if b.id in vorhandene else False,
            "gepflegt": b.id in vorhandene,
        }
        for b in brawler
    ]
    return render(request, "drafter/meine_brawler.html", {
        "eintraege": eintraege,
        "rollen": attr.ROLLEN,
    })
