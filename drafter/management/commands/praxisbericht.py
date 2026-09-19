# -*- coding: utf-8 -*-
"""Was die protokollierten Draftfaelle zeigen - und was nicht.

    python manage.py praxisbericht
    python manage.py praxisbericht --modus gem-grab
    python manage.py praxisbericht --auffaellig

Wertet nur aus, aendert nichts. Zwei Dinge stehen bewusst NICHT als
Qualitaetsmass darin:

* **Uebereinstimmung mit fremden Empfehlungen.** Sie wird gezeigt, weil
  sie auffaellig sein kann - aber zwei Systeme koennen sich einig und
  beide falsch sein, und ein guter Pick kann bei genau einem stehen.
* **Einzelne verlorene Partien.** Ein Draft entscheidet eine Partie nicht
  allein; bei dreissig Faellen ist jede Siegquote Rauschen.

Strukturell wird ein Problem erst, wenn derselbe Fehlertyp mehrfach
auftritt oder ein einzelner Fall einen klaren mathematischen oder
semantischen Fehler zeigt.
"""

from collections import Counter

from django.core.management.base import BaseCommand

from drafter import config
from drafter.models import Ergebnis, Praxisfall


class Command(BaseCommand):
    help = "Wertet die protokollierten Praxisfälle aus (ändert nichts)."

    def add_arguments(self, parser):
        parser.add_argument("--modus", help="nur ein Modus")
        parser.add_argument("--auffaellig", action="store_true",
                            help="nur markierte Fälle")

    def handle(self, *args, **o):
        faelle = Praxisfall.objects.select_related("game_mode", "brawl_map")
        if o["modus"]:
            faelle = faelle.filter(game_mode__slug=o["modus"])
        if o["auffaellig"]:
            faelle = faelle.filter(auffaellig=True)
        faelle = list(faelle)
        n = len(faelle)
        if not n:
            self.stdout.write("Noch keine Fälle protokolliert.")
            return

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"{n} Fälle (Ziel: {config.PRAXIS_MINDESTFAELLE})"))
        staende = Counter(f.modellstand or "-" for f in faelle)
        if len(staende) > 1:
            self.stdout.write(self.style.WARNING(
                "  Achtung, mehrere Modellstände: "
                + ", ".join(f"{k} ({v})" for k, v in staende.items())))

        self._verteilung("Nach Modus", Counter(f.game_mode.slug for f in faelle), n)
        self._verteilung("Nach Draftphase", Counter(f.draft_phase for f in faelle), n)
        self._verteilung("Nach Map", Counter(f.brawl_map.name for f in faelle), n)

        # --- Gewaehlte Raenge -------------------------------------------
        raenge = [f.gewaehlter_rang for f in faelle if f.gewaehlter_rang]
        ohne = sum(1 for f in faelle if f.gewaehlt and not f.gewaehlter_rang)
        self.stdout.write(self.style.MIGRATE_HEADING("\nGewählte Empfehlung"))
        if raenge:
            self.stdout.write(
                f"  Platz 1: {sum(1 for r in raenge if r == 1)} | "
                f"Top 3: {sum(1 for r in raenge if r <= 3)} | "
                f"Top 5: {sum(1 for r in raenge if r <= 5)} | "
                f"Top 10: {len(raenge)} | mittlerer Platz "
                f"{sum(raenge)/len(raenge):.1f}")
        self.stdout.write(f"  nicht in unserer Liste: {ohne}")

        # --- Ergebnis ---------------------------------------------------
        ergebnisse = Counter(f.ergebnis for f in faelle)
        bekannt = ergebnisse[Ergebnis.SIEG] + ergebnisse[Ergebnis.NIEDERLAGE]
        self.stdout.write(self.style.MIGRATE_HEADING("\nAusgang"))
        self.stdout.write(
            f"  Sieg {ergebnisse[Ergebnis.SIEG]} | Niederlage "
            f"{ergebnisse[Ergebnis.NIEDERLAGE]} | unbekannt "
            f"{ergebnisse[Ergebnis.UNBEKANNT]}")
        if bekannt:
            quote = ergebnisse[Ergebnis.SIEG] / bekannt
            self.stdout.write(
                f"  Siegquote {quote:.0%} aus {bekannt} Partien - bei dieser "
                "Zahl noch ohne Aussagekraft.")

        # --- Konkurrenz --------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING("\nÜberschneidung mit fremden Listen"))
        mit = [f for f in faelle if f.competitor_top]
        if not mit:
            self.stdout.write("  keine fremden Empfehlungen eingetragen")
        else:
            for tiefe in (1, 3, 5):
                werte = [f.overlap(tiefe) for f in mit]
                werte = [w for w in werte if w is not None]
                if werte:
                    moeglich = sum(min(tiefe, len(f.competitor_top)) for f in mit)
                    self.stdout.write(
                        f"  Top{tiefe}: {sum(werte)} von {moeglich} "
                        f"({100*sum(werte)/moeglich:.0f} %)")
            self.stdout.write(
                "  Kein Qualitätsmaß - nur eine Beobachtung.")

        # --- Auffaelliges ------------------------------------------------
        markiert = [f for f in faelle if f.auffaellig]
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nAuffällige Fälle: {len(markiert)} von {n}"))
        klassen = Counter(f.fehlerklasse or "(ohne Klasse)" for f in markiert)
        for klasse, anzahl in klassen.most_common():
            self.stdout.write(f"  {klasse:<14} {anzahl}")
            if anzahl >= 2 and klasse not in ("(ohne Klasse)", "KEIN_FEHLER"):
                betroffene = [f for f in markiert if f.fehlerklasse == klasse]
                modi = Counter(f.game_mode.slug for f in betroffene)
                self.stdout.write(self.style.WARNING(
                    f"     wiederkehrend - {dict(modi)}"))
        for f in markiert:
            self.stdout.write(
                f"  #{f.id} {f.game_mode.slug}/{f.brawl_map.name} "
                f"({f.draft_phase}): {f.notizen.splitlines()[0] if f.notizen else '-'}")

        # --- Was noch fehlt ----------------------------------------------
        fehlend = [m for m in ("gem-grab", "brawl-ball", "hot-zone", "knockout",
                               "bounty", "heist")
                   if not any(f.game_mode.slug == m for f in faelle)]
        if fehlend:
            self.stdout.write(self.style.MIGRATE_HEADING("\nNoch keine Fälle aus"))
            self.stdout.write("  " + ", ".join(fehlend))

    def _verteilung(self, titel, zaehler, gesamt):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{titel}"))
        for name, anzahl in zaehler.most_common():
            balken = "#" * anzahl
            self.stdout.write(f"  {name:<22} {anzahl:>3} {balken}")
