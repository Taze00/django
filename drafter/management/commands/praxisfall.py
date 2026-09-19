# -*- coding: utf-8 -*-
"""Einen echten Draft in wenigen Sekunden protokollieren.

    python manage.py praxisfall --map safe-zone --gewaehlt colt
    python manage.py praxisfall --map ring-of-fire --eigene gale \
        --gegner bull,belle --bans mortis,leon --gewaehlt amber \
        --ergebnis win --konkurrenz colette,penny,wendy
    python manage.py praxisfall --liste
    python manage.py praxisfall --markieren 7 --klasse MODUS --notiz "..."

Der Befehl fragt die Engine selbst - eingetippt wird nur, was man
ohnehin weiss: Map, was schon steht, was man genommen hat. Alles andere
(Phase, Empfehlungen, Erklaerungen, Rang des gewaehlten Brawlers) holt
er sich und friert es ein.

**Er veraendert nichts am Modell.** Keine Statistik, kein Score, kein
Profil - nur ein Eintrag in `Praxisfall`. Das ist der ganze Zweck: ein
Testdatensatz, der das System beeinflusst, das er pruefen soll, beweist
nichts mehr.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from drafter import config
from drafter.models import BrawlMap, Ergebnis, Fehlerklasse, Praxisfall
from drafter.services.anfrage import context_aus_daten
from drafter.services.draft_engine import DraftEngine
from drafter.services.identitaet import Mehrdeutig, finde_brawler

MODELLSTAND = "modell-praxistest-2026-09-19"


def _eingaben(text):
    """Kommagetrennte Eingabe in einzelne Stuecke - ohne sie zu deuten."""
    if not text:
        return []
    return [t.strip() for t in text.replace(";", ",").split(",") if t.strip()]


def _slugs(text, feld):
    """Eingaben auf Katalog-Slugs aufloesen - Name, Slug oder ID.

    Getippt wird, was man sieht ("WILLOW", "Larry & Lawrie", "R-T"); der
    Katalog kennt Slugs. Die Aufloesung ist dieselbe wie im Import
    (services/identitaet.py) und raet nie.
    """
    ergebnis = []
    for eingabe in _eingaben(text):
        try:
            b = finde_brawler(eingabe)
        except Mehrdeutig as fehler:
            raise CommandError(f"--{feld}: {fehler}")
        if b is None:
            raise CommandError(f"--{feld}: unbekannter Brawler '{eingabe}'")
        ergebnis.append(b.slug)
    return ergebnis


class Command(BaseCommand):
    help = "Protokolliert eine echte Draftsituation samt Empfehlungen (ändert nichts)."

    def add_arguments(self, parser):
        parser.add_argument("--map", dest="karte", help="Map-Slug, z.B. safe-zone")
        parser.add_argument("--eigene", default="", help="eigene Picks, kommagetrennt")
        parser.add_argument("--gegner", default="", help="gegnerische Picks")
        parser.add_argument("--bans", default="", help="Bans")
        parser.add_argument("--gegner-first", action="store_true",
                            help="Der Gegner hat den ersten Pick")
        parser.add_argument("--gewaehlt", default="", help="Was du genommen hast")
        parser.add_argument("--ergebnis", choices=[e.value for e in Ergebnis],
                            default=Ergebnis.UNBEKANNT)
        parser.add_argument("--konkurrenz", default="",
                            help="fremde Empfehlungen, nur Protokoll")
        parser.add_argument("--notiz", default="")
        parser.add_argument("--auffaellig", action="store_true")
        parser.add_argument("--klasse", choices=[f.value for f in Fehlerklasse],
                            default="")
        parser.add_argument("--tiefe", type=int, default=10,
                            help="Wie viele Empfehlungen einfrieren (Standard: %(default)s)")
        # Nachtraegliches Pflegen und Nachsehen
        parser.add_argument("--liste", action="store_true", help="Faelle auflisten")
        parser.add_argument("--markieren", type=int, metavar="ID",
                            help="Einen Fall nachträglich einordnen")

    def handle(self, *args, **o):
        if o["liste"]:
            return self._liste()
        if o["markieren"]:
            return self._markieren(o)
        if not o["karte"]:
            raise CommandError("--map fehlt (oder --liste / --markieren benutzen)")

        karte = BrawlMap.objects.waehlbare().filter(slug=o["karte"]).select_related(
            "game_mode").first()
        if karte is None:
            raise CommandError(
                f"Map '{o['karte']}' ist nicht wählbar. Verfügbar: "
                + ", ".join(k.slug for k in BrawlMap.objects.waehlbare()[:40]))

        daten = {
            "map": karte.slug,
            "own_picks": _slugs(o["eigene"], "eigene"),
            "enemy_picks": _slugs(o["gegner"], "gegner"),
            "bans": _slugs(o["bans"], "bans"),
            "own_team_first_pick": not o["gegner_first"],
        }
        ctx = context_aus_daten(daten)
        empfehlungen = DraftEngine(ctx).empfehlungen(anzahl=o["tiefe"])
        if not empfehlungen:
            raise CommandError("Die Engine liefert hier keine Empfehlung")

        gewaehlt = _slugs(o["gewaehlt"], "gewaehlt")[:1]
        rang = score = None
        if gewaehlt:
            for i, e in enumerate(empfehlungen, 1):
                if e.brawler.slug == gewaehlt[0]:
                    rang, score = i, e.anzeige_score
                    break

        fall = Praxisfall.objects.create(
            gespielt_am=timezone.now(),
            game_mode=karte.game_mode, brawl_map=karte,
            draft_phase=ctx.phase_label,
            eigener_first_pick=not o["gegner_first"],
            bans=daten["bans"], own_picks=daten["own_picks"],
            enemy_picks=daten["enemy_picks"],
            empfehlungen=[e.als_dict(ausfuehrlich=True) for e in empfehlungen],
            gewaehlt=gewaehlt[0] if gewaehlt else "",
            gewaehlter_rang=rang, gewaehlter_score=score,
            competitor_top=_slugs(o["konkurrenz"], "konkurrenz"),
            ergebnis=o["ergebnis"], auffaellig=o["auffaellig"],
            fehlerklasse=o["klasse"], notizen=o["notiz"],
            modellstand=MODELLSTAND,
        )

        self.stdout.write(self.style.SUCCESS(
            f"Fall #{fall.id} gespeichert: {karte.name} ({ctx.phase_label})"))
        for i, e in enumerate(empfehlungen[:5], 1):
            erk = e.erklaerung()
            marke = " <-- gewählt" if rang == i else ""
            self.stdout.write(
                f"  {i}. {e.brawler.name:<14} {e.anzeige_score:>3} | "
                f"CS {erk['current_strength']['punkte']:>+5.1f} | "
                f"Obj {(erk['objective_fit'] or {}).get('punkte', 0):>+5.1f} | "
                f"Fit {erk['draft_fit']['punkte']:>+5.1f} | "
                f"Conf {erk['statistical_confidence']['gesamt']:.2f}{marke}")
        if gewaehlt and rang is None:
            self.stdout.write(self.style.WARNING(
                f"  {gewaehlt[0]} stand nicht in den Top {o['tiefe']} - "
                "genau solche Fälle sind interessant."))
        gesamt = Praxisfall.objects.count()
        self.stdout.write(f"\n{gesamt} von {config.PRAXIS_MINDESTFAELLE} Fällen")

    def _liste(self):
        faelle = Praxisfall.objects.select_related("brawl_map", "game_mode")
        self.stdout.write(f"{faelle.count()} Fälle")
        for f in faelle[:40]:
            marke = "!" if f.auffaellig else " "
            self.stdout.write(
                f" {marke}#{f.id:<4} {f.gespielt_am:%m-%d %H:%M} "
                f"{f.game_mode.slug:<11} {f.brawl_map.name[:18]:<19} "
                f"{f.draft_phase:<14} {f.gewaehlt or '-':<12} "
                f"Rang {str(f.gewaehlter_rang or '-'):>3} {f.ergebnis:<8} "
                f"{f.fehlerklasse}")

    def _markieren(self, o):
        try:
            fall = Praxisfall.objects.get(pk=o["markieren"])
        except Praxisfall.DoesNotExist:
            raise CommandError(f"Kein Fall #{o['markieren']}")
        if o["klasse"]:
            fall.fehlerklasse = o["klasse"]
            fall.auffaellig = o["klasse"] != Fehlerklasse.KEIN_FEHLER
        if o["auffaellig"]:
            fall.auffaellig = True
        if o["notiz"]:
            fall.notizen = (fall.notizen + "\n" + o["notiz"]).strip()
        if o["ergebnis"] != Ergebnis.UNBEKANNT:
            fall.ergebnis = o["ergebnis"]
        if o["konkurrenz"]:
            fall.competitor_top = _slugs(o["konkurrenz"], "konkurrenz")
        fall.save()
        self.stdout.write(self.style.SUCCESS(
            f"#{fall.id}: {fall.fehlerklasse or 'ohne Klasse'}, "
            f"{fall.ergebnis}, auffällig={fall.auffaellig}"))
