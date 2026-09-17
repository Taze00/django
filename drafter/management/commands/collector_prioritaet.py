# -*- coding: utf-8 -*-
"""Welche Spieler schliessen die groessten Datenluecken? Ohne Netz.

    python manage.py collector_prioritaet
    python manage.py collector_prioritaet --top 30
    python manage.py collector_prioritaet --brawler COSMO
    python manage.py collector_prioritaet --vergleich

Das Kommando **ruft die API nicht auf**. Es liest die bereits
importierten Partien, rechnet Defizite und sortiert die noch nie
abgefragten Spieler danach. Abgerufen wird erst mit
`collect_brawl_matches --strategie luecken`.

Die Zahlen hinter der Sortierung stehen in drafter/config.py
(PRIORITAET_ZIELE, PRIORITAET_GEWICHTE, PRIORITAET_MAX_BEITRAEGE).

Ein Defizit ist eine Reihenfolge, keine Qualitaetsaussage: es sagt "hier
fehlen Daten", nicht "diese Daten sind jetzt belastbar".
"""

import random

from django.core.management.base import BaseCommand, CommandError

from drafter import config
from drafter.models import Brawler
from drafter.services.prioritaet import Datenluecken, Priorisierung, katalog_brawler_ids


class Command(BaseCommand):
    help = "Priorisiert nie abgefragte Spieler nach Datenluecken (ohne API-Zugriff)."

    def add_arguments(self, parser):
        parser.add_argument("--top", type=int, default=100,
                            help="Wie viele Spieler ausgeben (Standard: %(default)s)")
        parser.add_argument("--brawler", help="Nur Spieler, die diesen Brawler gespielt haben")
        parser.add_argument("--vergleich", action="store_true",
                            help="Priorisierte gegen zufällige Auswahl stellen")
        parser.add_argument("--stichprobe", type=int, default=5,
                            help="Läufe für die Zufallsauswahl im Vergleich")

    def handle(self, *args, **opts):
        luecken = Datenluecken()
        katalog_ids = katalog_brawler_ids()
        prio = Priorisierung(luecken=luecken, katalog_ids=katalog_ids)
        offen = prio.offene_spieler()

        self.stdout.write(self.style.MIGRATE_HEADING("Datenlage"))
        self.stdout.write(
            f"  Ziele: {config.PRIORITAET_ZIELE} | Gewichte: {config.PRIORITAET_GEWICHTE}"
        )
        selten = luecken.seltene_brawler()
        self.stdout.write(
            f"  Brawler unter Ziel: {len(selten)} | Stufe katalog: {len(katalog_ids)} | "
            f"nie abgefragte Spieler: {offen.count()}"
        )

        if opts["brawler"]:
            self._fuer_brawler(prio, luecken, opts["brawler"], opts["top"])
            return

        rang = prio.rangliste(anzahl=opts["top"])
        self._tabelle(rang, luecken, katalog_ids)
        self._abdeckung(rang, luecken, katalog_ids)
        if opts["vergleich"]:
            self._vergleich(prio, luecken, katalog_ids, opts["top"], opts["stichprobe"])

    # ------------------------------------------------------------------
    def _fuer_brawler(self, prio, luecken, name, anzahl):
        brawler = (Brawler.objects.filter(slug__iexact=name).first()
                   or Brawler.objects.filter(name__iexact=name).first()
                   or Brawler.objects.filter(name__icontains=name).first())
        if brawler is None:
            raise CommandError(f"Unbekannter Brawler '{name}'")
        gespielt = luecken.brawler_global.get(brawler.id, 0)
        treffer = prio.fuer_brawler(brawler, anzahl=anzahl)
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n{brawler.name}: {gespielt} gezählte Partien, "
            f"Defizit bis Ziel {config.PRIORITAET_ZIELE['brawler_global']}: "
            f"{max(0, config.PRIORITAET_ZIELE['brawler_global'] - gespielt)}"
        ))
        if not treffer:
            self.stdout.write("  Kein offener Spieler mit diesem Brawler in der Historie.")
            return
        self.stdout.write(f"  {len(treffer)} offene Spieler haben ihn gespielt:")
        for i, b in enumerate(treffer, 1):
            eigene = luecken.spieler_brawler[b.tag].get(brawler.id, 0)
            self.stdout.write(
                f"  {i:>3}. {b.tag:<12} {b.punkte:>6.2f} Punkte | {eigene}× gespielt | "
                f"Partien bekannt {b.partien:>3}"
                + (f" | Trophäen {b.trophaeen}" if b.trophaeen else "")
            )

    def _tabelle(self, rang, luecken, katalog_ids):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\nTop {len(rang)} (nie abgefragt)"))
        for i, b in enumerate(rang, 1):
            je = b.punkte_je_kategorie()
            teile = " ".join(f"{k}={v:.2f}" for k, v in sorted(je.items()))
            self.stdout.write(
                f"{i:>3}. {b.tag:<12} {b.punkte:>6.2f} | {teile}"
                + (f" | Rang {b.rang}" if b.rang else "")
                + (f" | Trophäen {b.trophaeen}" if b.trophaeen else "")
            )
            if b.katalog_brawler:
                self.stdout.write(self.style.WARNING(
                    f"      Catalog-Only: {', '.join(b.katalog_brawler)}"))
            gruende = b.gruende()
            if gruende:
                self.stdout.write("      Gründe: " + " · ".join(str(g) for g in gruende))

    def _abdeckung(self, rang, luecken, katalog_ids):
        """Was die ausgewählten Spieler laut bekannter Historie berühren."""
        tags = [b.tag for b in rang]
        erreicht = set()
        modus_luecken = set()
        counter_luecken = set()
        synergie_luecken = set()
        for tag in tags:
            for brawler in luecken.spieler_brawler.get(tag, {}):
                if brawler in katalog_ids:
                    erreicht.add(brawler)
            modus_luecken |= {
                paar for paar in luecken.spieler_modus.get(tag, ())
                if luecken.brawler_modus.get(paar, 0) < config.PRIORITAET_ZIELE["brawler_modus"]
            }
            counter_luecken |= {
                paar for paar in luecken.spieler_counter.get(tag, ())
                if luecken.counter.get(paar, 0) < config.PRIORITAET_ZIELE["counter"]
            }
            synergie_luecken |= {
                paar for paar in luecken.spieler_synergie.get(tag, ())
                if luecken.synergie.get(paar, 0) < config.PRIORITAET_ZIELE["synergie"]
            }
        self.stdout.write(self.style.MIGRATE_HEADING("\nWas diese Auswahl berührt"))
        self.stdout.write(
            f"  Catalog-Only-Brawler: {len(erreicht)} von {len(katalog_ids)}"
            f" ({', '.join(sorted(luecken.name(b) for b in erreicht))})"
        )
        self.stdout.write(
            f"  Modus/Brawler-Lücken: {len(modus_luecken)} | "
            f"Counter-Paare: {len(counter_luecken)} | Synergie-Paare: {len(synergie_luecken)}"
        )

    def _vergleich(self, prio, luecken, katalog_ids, anzahl, laeufe):
        """Priorisiert gegen Zufall - an derselben bekannten Historie gemessen."""
        offen = list(prio.offene_spieler())
        rang = prio.rangliste(anzahl=anzahl)

        def deckung(tags):
            brawler, modus, counter, synergie = set(), set(), set(), set()
            for tag in tags:
                brawler |= {b for b in luecken.spieler_brawler.get(tag, {}) if b in katalog_ids}
                modus |= {p for p in luecken.spieler_modus.get(tag, ())
                          if luecken.brawler_modus.get(p, 0) < config.PRIORITAET_ZIELE["brawler_modus"]}
                counter |= {p for p in luecken.spieler_counter.get(tag, ())
                            if luecken.counter.get(p, 0) < config.PRIORITAET_ZIELE["counter"]}
                synergie |= {p for p in luecken.spieler_synergie.get(tag, ())
                             if luecken.synergie.get(p, 0) < config.PRIORITAET_ZIELE["synergie"]}
            return len(brawler), len(modus), len(counter), len(synergie)

        prior = deckung([b.tag for b in rang])
        wuerfel = random.Random(20260917)
        zufall = [deckung([s.tag for s in wuerfel.sample(offen, min(anzahl, len(offen)))])
                  for _ in range(laeufe)]
        mittel = [sum(w[i] for w in zufall) / len(zufall) for i in range(4)]

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nVergleich: {anzahl} priorisierte gegen {anzahl} zufällige Spieler "
            f"({laeufe} Zufallsläufe, Mittelwert)"
        ))
        zeilen = (
            ("Catalog-Only-Brawler", 0, len(katalog_ids)),
            ("Modus/Brawler-Lücken", 1, None),
            ("Counter-Paare", 2, None),
            ("Synergie-Paare", 3, None),
        )
        for name, i, von in zeilen:
            zusatz = f" von {von}" if von else ""
            self.stdout.write(
                f"  {name:<22} priorisiert {prior[i]:>5}{zusatz} | zufällig {mittel[i]:>7.1f}{zusatz}"
            )
