"""Persoenliche Sicherheit des Nutzers.

Die wichtigste Leitplanke steht in `config.PERSOENLICH_MAX_AUSSCHLAG`:
die eigene Uebung darf einen objektiv schlechten Pick **nicht** gut
machen. Sie verschiebt die Reihenfolge zwischen gleichwertigen
Vorschlaegen - mehr nicht. Wer Mortis nicht spielen kann, soll ihn
weiter unten sehen; wer ihn beherrscht, soll ihn nicht auf Platz eins
gehoben bekommen, wenn er in diesen Draft nicht passt.

Angemeldet kommen die Werte aus `UserBrawlerPreference`, als Gast aus
der Session. Die Engine merkt den Unterschied nicht - sie bekommt in
beiden Faellen ein Dict {brawler_id: {...}}.
"""

from drafter import config
from drafter.models import UserBrawlerPreference
from drafter.services.scoring import Grund, Komponente, klemme

SESSION_SCHLUESSEL = "drafter_confidence"


def aus_datenbank(user):
    if not user or not getattr(user, "is_authenticated", False):
        return {}
    eintraege = UserBrawlerPreference.objects.filter(user=user).select_related("brawler")
    return {
        e.brawler_id: {
            "confidence": e.combined_confidence,
            "favorite": e.favorite,
            "avoid": e.avoid,
        }
        for e in eintraege
    }


def aus_session(session):
    """Gastwerte aus der Session.

    Format in der Session ist bewusst schlicht {slug: 0-100} - was dort
    liegt, ueberlebt keinen Browserwechsel und soll niemanden zum
    Pflegen eines zweiten Datenbestands verleiten.
    """
    roh = (session or {}).get(SESSION_SCHLUESSEL) or {}
    return roh if isinstance(roh, dict) else {}


def laden(request, brawler_liste):
    """Persoenliche Werte fuer diesen Request, als {brawler_id: {...}}."""
    if request is not None and getattr(request, "user", None) is not None:
        werte = aus_datenbank(request.user)
        if werte:
            return werte

    nach_slug = {b.slug: b for b in brawler_liste}
    session_werte = aus_session(getattr(request, "session", None))
    werte = {}
    for slug, confidence in session_werte.items():
        b = nach_slug.get(slug)
        if b is None:
            continue
        try:
            zahl = float(confidence)
        except (TypeError, ValueError):
            continue
        werte[b.id] = {
            "confidence": max(0.0, min(100.0, zahl)),
            "favorite": False,
            "avoid": zahl <= 5,
        }
    return werte


def komponente(kandidat, ctx):
    """Persoenliche Komponente - hart gedeckelt.

    Der Deckel sitzt hier und nicht beim Aufrufer, damit er nicht
    versehentlich umgangen werden kann. Gewicht mal Wert plus Zuschlaege
    kann `PERSOENLICH_MAX_AUSSCHLAG` nie ueberschreiten.
    """
    komp = Komponente(key=config.K_PERSONAL)
    eintrag = (ctx.personal or {}).get(kandidat.id)
    if not eintrag:
        komp.confidence = 0.3
        return komp

    confidence = float(eintrag.get("confidence", config.PERSOENLICH_NEUTRAL))
    wert = klemme((confidence - config.PERSOENLICH_NEUTRAL) / config.PERSOENLICH_NEUTRAL)

    if eintrag.get("avoid"):
        wert -= config.PERSOENLICH_VERMEIDEN_ABZUG / max(1e-6, config.PERSOENLICH_MAX_AUSSCHLAG)
        komp.gruende.append(Grund(
            text="du hast ihn als 'spiele ich nicht' markiert", positiv=False, staerke=0.9,
        ))
    elif eintrag.get("favorite"):
        wert += config.PERSOENLICH_FAVORIT_BONUS / max(1e-6, config.PERSOENLICH_MAX_AUSSCHLAG)

    komp.wert = klemme(wert)
    komp.confidence = 1.0

    if confidence >= 80:
        komp.gruende.append(Grund(
            text=f"du spielst ihn sicher ({int(confidence)}/100)", positiv=True, staerke=0.35,
        ))
    elif confidence <= 25 and not eintrag.get("avoid"):
        komp.gruende.append(Grund(
            text=f"du spielst ihn selten ({int(confidence)}/100)", positiv=False, staerke=0.4,
        ))
    return komp


def deckel_anwenden(komp):
    """Beitrag der persoenlichen Komponente auf den Maximalausschlag kappen.

    Aufgerufen von der Engine, nachdem das Phasengewicht gesetzt ist.
    Ohne diesen Schritt koennte ein hohes Gewicht in der Konfiguration
    die Leitplanke aushebeln.
    """
    grenze = config.PERSOENLICH_MAX_AUSSCHLAG
    if komp.gewicht <= 0:
        return komp
    max_wert = grenze / komp.gewicht
    komp.wert = klemme(komp.wert, -max_wert, max_wert)
    return komp
