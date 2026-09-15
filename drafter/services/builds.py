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

from django.db import models

from drafter import config
from drafter.models import BrawlerItem
from drafter.services.scoring import klemme

# Wie viele Gears ein Build hat.
GEAR_PLAETZE = 2


class Ausruestungskatalog:
    """Alle Ausruestungsgegenstaende einer Anfrage, einmal geladen.

    Ohne ihn fragt jeder Kandidat seine eigenen Gegenstaende UND die
    generischen Gears einzeln ab - bei acht angezeigten Empfehlungen
    sechzehn Abfragen fuer Daten, die sich waehrend einer Anfrage nicht
    aendern. Dieselbe Ueberlegung wie beim Datenraum, nur fuer Builds.

    Ohne Katalog funktioniert alles weiter (dann eben mit Einzelabfragen)
    - die Aufrufer muessen ihn nicht kennen.
    """

    def __init__(self, brawler=None):
        gegenstaende = BrawlerItem.objects.filter(is_active=True).prefetch_related("rules")
        if brawler is not None:
            ids = [b.id for b in brawler]
            gegenstaende = gegenstaende.filter(
                models.Q(brawler_id__in=ids) | models.Q(brawler__isnull=True)
            )

        self._nach_brawler = {}
        self._generische = []
        for gegenstand in gegenstaende:
            if gegenstand.brawler_id is None:
                self._generische.append(gegenstand)
            else:
                self._nach_brawler.setdefault(gegenstand.brawler_id, []).append(gegenstand)

    def fuer(self, brawler):
        return self._nach_brawler.get(brawler.id, [])

    @property
    def generische(self):
        return self._generische


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


def _bewerte(gegenstaende, kandidat, ctx, raum=None):
    """Je Gegenstand: (Punktzahl, Gruende) aus Grundwert, Regeln und Statistik.

    Die Statistik kommt obendrauf und verdraengt die Regeln nicht. Ihr
    Einfluss ist mit ihrer Confidence gewichtet: eine Build-Statistik aus
    zwanzig Partien verschiebt kaum etwas, eine aus zwanzigtausend deutlich.
    Ohne Datenraum oder ohne Build-Statistik ist das Ergebnis exakt das
    der Regeln allein.
    """
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

        stat = raum.build_stat(kandidat, gegenstand.kind, gegenstand.slug) if raum else None
        if stat is not None and stat.games:
            punkte += config.BUILD_STAT_EINFLUSS * stat.advantage * stat.confidence
            gruende.append(_statistik_text(stat, kandidat))
        bewertet.append((punkte, gegenstand, gruende, stat))
    bewertet.sort(key=lambda p: -p[0])
    return bewertet


def _statistik_text(stat, kandidat):
    """Begruendung aus einer Build-Statistik - mit Stichprobe und Herkunft."""
    richtung = "über" if stat.advantage >= 0 else "unter"
    herkunft = "" if stat.ist_gemessen else " (keine Messung: Demo- oder Testdaten)"
    return (
        f"in {stat.games} vergleichbaren Partien {richtung} "
        f"{kandidat.name}s Durchschnitt{herkunft}"
    )


def _text(regel, kandidat, ctx):
    """Begruendung einer Regel mit eingesetzten Platzhaltern."""
    gegner = ", ".join(g.name for g in ctx.enemy_picks) or "dem Gegner"
    return regel.reason_template.format(
        brawler=kandidat.name,
        map=ctx.brawl_map.name if ctx.brawl_map else "dieser Map",
        mode=ctx.game_mode.name if ctx.game_mode else "diesem Modus",
        gegner=gegner,
    )


def empfehlung(kandidat, ctx, katalog=None, raum=None):
    """Build fuer einen Brawler im aktuellen Draftkontext.

    Gibt None zurueck, wenn zu diesem Brawler nichts gepflegt ist.
    `katalog` ist optional - ohne ihn wird einzeln abgefragt.
    """
    if katalog is not None:
        eigene = list(katalog.fuer(kandidat))
        generische = list(katalog.generische)
    else:
        eigene = list(
            BrawlerItem.objects.filter(brawler=kandidat, is_active=True)
            .prefetch_related("rules")
        )
        generische = list(
            BrawlerItem.objects.filter(brawler__isnull=True, is_active=True)
            .prefetch_related("rules")
        )
    if not eigene and not generische:
        return None

    # "statistik" steht immer in der Antwort, auch als False - die
    # Oberflaeche soll nicht zwischen "fehlt" und "nein" unterscheiden muessen.
    build = {"quelle": "regeln", "ist_demo": True, "statistik": False, "gruende": []}
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
        bewertet = _bewerte(auswahl, kandidat, ctx, raum)
        punkte, bester, gruende, stat = bewertet[0]
        build["statistik"] = build["statistik"] or stat is not None
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
        bewertet = _bewerte(gears, kandidat, ctx, raum)
        build["gears"] = [g.name for _, g, _, _ in bewertet[:GEAR_PLAETZE]]
        for _, _, gruende, stat in bewertet[:GEAR_PLAETZE]:
            alle_gruende += gruende
            build["statistik"] = build["statistik"] or stat is not None
    else:
        build["gears"] = []

    # Gleiche Begruendung mehrfach (z.B. Gadget und Gear wegen derselben
    # Gegnercomp) nur einmal zeigen.
    build["gruende"] = list(dict.fromkeys(g for g in alle_gruende if g))
    if build["statistik"]:
        build["quelle"] = "regeln+statistik"

    # Ehrlich bleiben, statt eine halbe Empfehlung wie eine ganze
    # aussehen zu lassen: sind zu diesem Brawler nur die generischen
    # Gears gepflegt, steht das auch da.
    if not eigene:
        build["hinweis"] = (
            "Für diesen Brawler sind noch keine Gadgets und Star Powers "
            "gepflegt - nur die allgemeinen Gears."
        )
    return build
