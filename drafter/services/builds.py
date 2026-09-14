"""Build-Empfehlung: Gadget, Star Power, Gears, Hypercharge.

Kontextabhaengig statt global - dasselbe Gadget kann gegen zwei
Nahkaempfer die richtige und auf einer offenen Map die falsche Wahl
sein. Die Entscheidung faellt ueber `BuildRule`-Bedingungen, die hier
ausgewertet werden.

Zur Auswertung: das Bedingungsformat ist ein festes, kleines Vokabular
(siehe `BuildRule`), das diese Datei Schluessel fuer Schluessel prueft.
Kein `eval`, kein Ausdrucksparser - eine Regelsprache waere maechtiger
und genau deshalb eine Angriffsflaeche und eine Fehlerquelle.

Zur Datenlage: ob die offizielle API Builds gespielter Matches liefert,
ist ungeprueft. Bis das feststeht, kommen die Empfehlungen aus
gepflegten Regeln und sind als solche gekennzeichnet. Fehlen Regeln und
Gegenstaende, liefert diese Datei `None` - die Empfehlung erscheint dann
ohne Build statt mit einem erfundenen.
"""

from drafter.models import BrawlerItem
from drafter.services.scoring import klemme

# Wie viele Gears ein Build hat.
GEAR_PLAETZE = 2


def _erfuellt(bedingung, kandidat, ctx):
    """Prueft eine Regelbedingung. Alle Schluessel gelten als UND."""
    if not bedingung:
        return True

    gegner = list(ctx.enemy_picks)
    eigene = list(ctx.own_picks)

    for schluessel, wert in bedingung.items():
        if schluessel == "enemy_role_count":
            for rolle, mindestens in wert.items():
                treffer = sum(1 for g in gegner if rolle in g.alle_rollen)
                if treffer < mindestens:
                    return False

        elif schluessel == "enemy_has":
            slugs = {g.slug for g in gegner}
            if not set(wert) & slugs:
                return False

        elif schluessel == "enemy_attr_min":
            for key, schwelle in wert.items():
                if max((g.wert(key) for g in gegner), default=0.0) < schwelle:
                    return False

        elif schluessel == "own_has_role":
            rollen = {r for b in eigene for r in b.alle_rollen}
            if not set(wert) & rollen:
                return False

        elif schluessel == "own_missing":
            from drafter.services.team_coverage import teamprofil
            profil = teamprofil(eigene + [kandidat])
            for key in wert:
                if profil.get(key, 0.0) >= 0.5:
                    return False

        elif schluessel == "map_trait_min":
            if not ctx.brawl_map:
                return False
            for key, schwelle in wert.items():
                if ctx.brawl_map.trait(key) < schwelle:
                    return False

        elif schluessel == "map_trait_max":
            if not ctx.brawl_map:
                return False
            for key, schwelle in wert.items():
                if ctx.brawl_map.trait(key) > schwelle:
                    return False

        elif schluessel == "mode":
            if not ctx.game_mode or ctx.game_mode.slug not in wert:
                return False

        else:
            # Unbekannter Schluessel: die Regel greift nicht. Lieber eine
            # Regel verschenken als eine Bedingung stillschweigend
            # ignorieren und den Build falsch begruenden.
            return False

    return True


def _bewerte(gegenstaende, kandidat, ctx):
    """Je Gegenstand: (Punktzahl, Gruende) aus Grundwert und Regeln."""
    bewertet = []
    for gegenstand in gegenstaende:
        punkte = gegenstand.base_weight
        gruende = []
        for regel in gegenstand.rules.all():
            if not regel.is_active:
                continue
            if _erfuellt(regel.condition, kandidat, ctx):
                punkte += regel.weight
                gruende.append(_text(regel, kandidat, ctx))
        bewertet.append((punkte, gegenstand, gruende))
    bewertet.sort(key=lambda p: -p[0])
    return bewertet


def _text(regel, kandidat, ctx):
    """Begruendung einer Regel mit eingesetzten Platzhaltern."""
    gegner = ", ".join(g.name for g in ctx.enemy_picks) or "dem Gegner"
    return regel.reason_template.format(
        brawler=kandidat.name,
        map=ctx.brawl_map.name if ctx.brawl_map else "dieser Map",
        mode=ctx.game_mode.name if ctx.game_mode else "diesem Modus",
        gegner=gegner,
    )


def empfehlung(kandidat, ctx):
    """Build fuer einen Brawler im aktuellen Draftkontext.

    Gibt None zurueck, wenn zu diesem Brawler nichts gepflegt ist.
    """
    eigene = list(
        BrawlerItem.objects.filter(brawler=kandidat, is_active=True).prefetch_related("rules")
    )
    generische = list(
        BrawlerItem.objects.filter(brawler__isnull=True, is_active=True).prefetch_related("rules")
    )
    if not eigene and not generische:
        return None

    build = {"quelle": "regeln", "ist_demo": True, "gruende": []}
    alle_gruende = []

    for kind, feld in (
        (BrawlerItem.Kind.GADGET, "gadget"),
        (BrawlerItem.Kind.STAR_POWER, "star_power"),
        (BrawlerItem.Kind.HYPERCHARGE, "hypercharge"),
    ):
        auswahl = [g for g in eigene if g.kind == kind]
        if not auswahl:
            build[feld] = None
            continue
        bewertet = _bewerte(auswahl, kandidat, ctx)
        punkte, bester, gruende = bewertet[0]
        build[feld] = {
            "name": bester.name,
            "beschreibung": bester.description,
            "punkte": round(klemme(punkte, 0, 2) / 2, 2),
        }
        alle_gruende += gruende
        build["ist_demo"] = build["ist_demo"] and bester.is_demo

        # Zweitbester nur, wenn es eine echte Alternative ist - sonst
        # taeuscht die Anzeige eine Wahl vor, die keine ist.
        if len(bewertet) > 1 and bewertet[1][0] > punkte - 0.25:
            build[feld]["alternative"] = bewertet[1][1].name

    gears = [g for g in eigene + generische if g.kind == BrawlerItem.Kind.GEAR]
    if gears:
        bewertet = _bewerte(gears, kandidat, ctx)
        build["gears"] = [g.name for _, g, _ in bewertet[:GEAR_PLAETZE]]
        for _, _, gruende in bewertet[:GEAR_PLAETZE]:
            alle_gruende += gruende
    else:
        build["gears"] = []

    # Gleiche Begruendung mehrfach (z.B. Gadget und Gear wegen derselben
    # Gegnercomp) nur einmal zeigen.
    build["gruende"] = list(dict.fromkeys(g for g in alle_gruende if g))

    # Ehrlich bleiben, statt eine halbe Empfehlung wie eine ganze
    # aussehen zu lassen: sind zu diesem Brawler nur die generischen
    # Gears gepflegt, steht das auch da.
    if not eigene:
        build["hinweis"] = (
            "Für diesen Brawler sind noch keine Gadgets und Star Powers "
            "gepflegt - nur die allgemeinen Gears."
        )
    return build
