"""Die Seiten des Drafters.

Drei Stueck, alle bewusst duenn: rendern und den Katalog mitgeben. Die
gesamte Draft-Logik laeuft ueber die JSON-Schnittstelle, damit ein Klick
auf einen Pick keine Seite neu laedt.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from drafter import attributes as attr
from drafter.models import Brawler, GameMode, UserBrawlerPreference
from drafter.services import personal


def draft(request):
    """Die Draft-Oberflaeche unter /draft/."""
    return render(request, "drafter/draft.html", {
        "modi": GameMode.objects.filter(is_active=True).prefetch_related("maps"),
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
