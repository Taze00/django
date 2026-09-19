# -*- coding: utf-8 -*-
"""Die vollstaendige Bewertung eines Brawlers in einer Draftlage - auf dem Terminal.

Fuer die Fehlersuche und den Praxistest: warum steht EDGAR hier auf
Platz 71? Die Vorschlagsliste zeigt acht Namen, diese Ausgabe zeigt
einen beliebigen - mit Rang, allen Komponenten, ihren Quellen und den
einzelnen Counter- und Synergiewerten gegen jeden Gegner und
Mitspieler.

    python manage.py drafter_analyse --map belles-rock \\
        --eigene gus,gray --gegner belle,sandy,mortis --brawler edgar

**Derselbe Rechenweg wie die Empfehlung.** Das Kommando ruft
`DraftEngine.analyse()` auf, also denselben Lauf, der auch die
Vorschlagsliste erzeugt; es rechnet selbst nichts und veraendert nichts.
Wuerde hier eine andere Zahl stehen als im Panel, waere das ein Fehler -
ein Test haelt beides gegeneinander.

Brawlernamen werden wie im Praxisfall-Kommando aufgeloest (Name, Slug,
externe ID, beliebige Schreibweise) und nie geraten.
"""

import json

from django.core.management.base import BaseCommand, CommandError

from drafter.models import BrawlMap
from drafter.services import analyse as analyse_dienst
from drafter.services.anfrage import context_aus_daten
from drafter.services.context import DraftFehler
from drafter.services.draft_engine import DraftEngine
from drafter.services.identitaet import Mehrdeutig, finde_brawler


def _slugs(text, feld):
    """Kommagetrennte Eingaben auf Katalog-Slugs aufloesen."""
    ergebnis = []
    for eingabe in [t.strip() for t in (text or "").replace(";", ",").split(",") if t.strip()]:
        try:
            brawler = finde_brawler(eingabe)
        except Mehrdeutig as fehler:
            raise CommandError(f"--{feld}: {fehler}")
        if brawler is None:
            raise CommandError(f"--{feld}: unbekannter Brawler '{eingabe}'")
        ergebnis.append(brawler.slug)
    return ergebnis


def _zahl(wert, stellen=1):
    """Vorzeichen immer mitschreiben - ohne es liest man Beitraege falsch."""
    return f"{wert:+.{stellen}f}"


class Command(BaseCommand):
    help = "Vollstaendige Bewertung eines Brawlers in einer Draftlage (Debug)"

    def add_arguments(self, parser):
        parser.add_argument("--map", dest="karte", required=True,
                            help="Map-Slug, z.B. belles-rock")
        parser.add_argument("--brawler", required=True,
                            help="Wen analysieren? Name, Slug oder externe ID")
        parser.add_argument("--eigene", default="", help="eigene Picks, kommagetrennt")
        parser.add_argument("--gegner", default="", help="gegnerische Picks")
        parser.add_argument("--bans", default="", help="Bans")
        parser.add_argument("--gegner-first", action="store_true",
                            help="Der Gegner hat den ersten Pick")
        parser.add_argument("--json", action="store_true",
                            help="Rohantwort ausgeben statt der Tabelle")

    def handle(self, *args, **o):
        karte = BrawlMap.objects.waehlbare().filter(slug=o["karte"]).first()
        if karte is None:
            raise CommandError(f"Unbekannte oder nicht waehlbare Map '{o['karte']}'")

        gesucht = _slugs(o["brawler"], "brawler")
        if len(gesucht) != 1:
            raise CommandError("--brawler erwartet genau einen Brawler")
        brawler = finde_brawler(gesucht[0])

        daten = {
            "map": karte.slug,
            "own_picks": _slugs(o["eigene"], "eigene"),
            "enemy_picks": _slugs(o["gegner"], "gegner"),
            "bans": _slugs(o["bans"], "bans"),
            "own_team_first_pick": not o["gegner_first"],
        }
        try:
            ctx = context_aus_daten(daten)
        except DraftFehler as fehler:
            raise CommandError(str(fehler))
        if brawler.id in ctx.gesperrte_ids:
            raise CommandError(f"{brawler.name} ist in dieser Lage gepickt oder gebannt")

        engine = DraftEngine(ctx)
        empfehlung, rang, anzahl = engine.analyse(brawler)
        if empfehlung is None:
            raise CommandError(
                f"{brawler.name} ist hier nicht bewertbar "
                f"(Datenstufe '{engine.raum.stufe(brawler)}') - kein Score, kein Rang.")

        antwort = analyse_dienst.als_dict(empfehlung, rang, anzahl, ctx, engine.raum)
        if o["json"]:
            self.stdout.write(json.dumps(antwort, ensure_ascii=False, indent=2,
                                         default=str))
            return
        self._tabelle(antwort, karte, ctx)

    # --- Ausgabe --------------------------------------------------------
    def _tabelle(self, a, karte, ctx):
        schreib = self.stdout.write
        schreib(self.style.SUCCESS(f"\n{a['name']}"))
        schreib(f"  {karte.name} · {karte.game_mode.name} · {ctx.phase}")
        eigene = ", ".join(b.name for b in ctx.own_picks) or "-"
        gegner = ", ".join(b.name for b in ctx.enemy_picks) or "-"
        schreib(f"  Eigene:  {eigene}")
        schreib(f"  Gegner:  {gegner}")
        schreib("")
        schreib(f"  Rang:              {a['rang']} von {a['kandidaten']} Kandidaten")
        schreib(f"  Score:             {a['score']}/100  (roh {a['score_roh']:+.3f})")
        schreib(f"  Siegchance:        {a['win_probability']} %")
        schreib(f"  Current Strength:  {_zahl(a['current_strength_beitrag'])}")
        schreib(f"  Draft Fit:         {_zahl(a['draft_fit'])}")
        schreib(f"  Datenabdeckung:    {a['datenabdeckung']} % ({a['datenabdeckung_label']})")
        schreib(f"  Confidence:        {a['confidence']} ({a['confidence_label']})")
        schreib(f"  Datenstufe:        {a['datenstufe']}")

        schreib(self.style.HTTP_INFO("\n  Komponenten"))
        schreib(f"    {'Komponente':<20} {'Wert':>7} {'Gew':>6} {'Beitrag':>8}  Quelle")
        for k in a["komponenten"]:
            wert = "  n.b." if not k["verfuegbar"] else f"{k['wert']:+.3f}"
            schreib(f"    {k['label']:<20} {wert:>7} {k['gewicht']:>6.2f} "
                    f"{k['beitrag']:>+8.1f}  {k['quelle']}")
        if a["ausgelassen"]:
            schreib(f"    ausgelassen: {', '.join(a['ausgelassen'])}")

        matchups = a["matchups"]
        if matchups["counter"]:
            schreib(self.style.HTTP_INFO("\n  Counter je Gegner"))
            for z in matchups["counter"]:
                self._paarzeile(z)
        if matchups["synergie"]:
            schreib(self.style.HTTP_INFO("\n  Synergie je Mitspieler"))
            for z in matchups["synergie"]:
                self._paarzeile(z)

        erk = a.get("erklaerung") or {}
        if erk:
            schreib(self.style.HTTP_INFO("\n  Erklärung"))
            for zeile in _erklaerungszeilen(erk):
                schreib(f"    {zeile}")
        schreib("")

    def _paarzeile(self, z):
        if not z["bekannt"]:
            self.stdout.write(f"    {z['name']:<16}   unbekannt - zählt nicht mit")
            return
        art = " (Heuristik)" if z["heuristisch"] else ""
        grund = f"  {z['grund']}" if z["grund"] else ""
        self.stdout.write(
            f"    {z['name']:<16} {z['wert']:+.3f}  ({z['punkte']:+.1f} Punkte)  "
            f"Sicherheit {z['sicherheit']:.2f}  {z['quelle']}{art}{grund}")


def _erklaerungszeilen(erk):
    """Die Erklaerungsstruktur flach ausgeben, ohne sie zu deuten."""
    zeilen = []
    for schluessel, wert in erk.items():
        if isinstance(wert, dict):
            innen = ", ".join(f"{k}={v}" for k, v in wert.items()
                              if not isinstance(v, (dict, list)))
            zeilen.append(f"{schluessel}: {innen}" if innen else f"{schluessel}:")
        elif isinstance(wert, list):
            zeilen.append(f"{schluessel}: {len(wert)} Einträge")
        else:
            zeilen.append(f"{schluessel}: {wert}")
    return zeilen
