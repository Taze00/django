# -*- coding: utf-8 -*-
"""Praxisfaelle: echte Drafts, dokumentiert zur spaeteren Auswertung.

Der Drafter ist ab dem 2026-09-19 eingefroren (Tag
`modell-praxistest-2026-09-19`). Was jetzt gebraucht wird, sind echte
Faelle - nicht weitere Theorie. Diese Tabelle ist reines Protokoll:

**Sie fuettert nichts zurueck.** Kein Score liest sie, kein Provider
kennt sie, keine Aggregation ruehrt sie an. Wer hier eintraegt,
veraendert keine Empfehlung - auch nicht die eigene beim naechsten Mal.
Das ist Absicht: ein Testdatensatz, der das System beeinflusst, das er
pruefen soll, beweist nichts mehr.

**Der Schnappschuss ist das Wertvolle.** Zu jedem Fall werden die
Empfehlungen samt vollstaendiger Erklaerung eingefroren (Current
Strength, Objective Fit, die Draft-Fit-Komponenten, Confidence,
Datenabdeckung, Quellen). Spaetere Modellaenderungen aendern die
Empfehlungen - der Schnappschuss haelt fest, was das Modell AN DIESEM
TAG gesagt hat, und nur so laesst sich hinterher pruefen, ob eine
Aenderung etwas verbessert hat.

Auch `modellstand` gehoert deshalb dazu: ein Fall ohne die Version, die
ihn erzeugt hat, ist nicht auswertbar.
"""

from django.db import models

from drafter.models.base import Zeitstempel


class Ergebnis(models.TextChoices):
    SIEG = "win", "Sieg"
    NIEDERLAGE = "loss", "Niederlage"
    UNBEKANNT = "unknown", "unbekannt"


class Fehlerklasse(models.TextChoices):
    """Wohin ein auffaelliger Fall gehoert - vergeben wird sie von Hand.

    Die Einteilung entscheidet spaeter, WO gesucht wird. Ein Fall, der
    nur "komisch" heisst, ist keine Information.
    """

    DATEN = "DATEN", "Daten: zu wenig, zu alt, verzerrt"
    MODUS = "MODUS", "Modus: Spielziel falsch verstanden"
    MAP = "MAP", "Map: Eigenschaft fehlt oder stimmt nicht"
    MATCHUP = "MATCHUP", "Matchup: Counter/Synergie unplausibel"
    DRAFT = "DRAFT", "Draft: First-/Mid-/Last-Pick-Logik unplausibel"
    PRIOR = "PRIOR", "Prior: Fachwissen/Profil traegt zu stark"
    ERKLAERUNG = "ERKLAERUNG", "Erklärung irreführend, Empfehlung plausibel"
    KEIN_FEHLER = "KEIN_FEHLER", "kein Fehler, nur andere Einschätzung"


class Praxisfall(Zeitstempel):
    """Eine dokumentierte echte Draftsituation."""

    gespielt_am = models.DateTimeField(
        help_text="Wann der Draft stattfand - nicht wann er eingetragen wurde.")
    game_mode = models.ForeignKey("drafter.GameMode", on_delete=models.PROTECT,
                                  related_name="praxisfaelle")
    brawl_map = models.ForeignKey("drafter.BrawlMap", on_delete=models.PROTECT,
                                  related_name="praxisfaelle")
    draft_phase = models.CharField(max_length=20)
    eigener_first_pick = models.BooleanField(
        default=True, help_text="Hat unser Team den ersten Pick?")

    # Slugs statt Fremdschluessel: ein Protokoll soll lesbar bleiben und
    # auch dann noch stimmen, wenn ein Katalogeintrag spaeter umgebaut
    # wird. Die Engine loest sie beim Eintragen auf und wuerde einen
    # unbekannten Slug sofort melden.
    bans = models.JSONField(default=list, blank=True)
    own_picks = models.JSONField(default=list, blank=True)
    enemy_picks = models.JSONField(default=list, blank=True)

    # Der eingefrorene Stand: Liste von `Empfehlung.als_dict()`.
    empfehlungen = models.JSONField(default=list, blank=True)

    gewaehlt = models.CharField(max_length=80, blank=True)
    gewaehlter_rang = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Platz des gewählten Brawlers in unserer Liste. Leer = war nicht dabei.")
    gewaehlter_score = models.PositiveIntegerField(null=True, blank=True)

    # Fremde Empfehlungen - nur Protokoll. Sie fliessen nirgends ein.
    competitor_top = models.JSONField(default=list, blank=True)

    ergebnis = models.CharField(max_length=10, choices=Ergebnis.choices,
                                default=Ergebnis.UNBEKANNT)
    auffaellig = models.BooleanField(default=False)
    fehlerklasse = models.CharField(max_length=20, choices=Fehlerklasse.choices,
                                    blank=True)
    notizen = models.TextField(blank=True)

    # Welche Fassung des Modells diesen Fall erzeugt hat.
    modellstand = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["-gespielt_am", "-id"]
        verbose_name = "Praxisfall"
        verbose_name_plural = "Praxisfälle"

    def __str__(self):
        return (f"{self.gespielt_am:%Y-%m-%d %H:%M} {self.brawl_map} "
                f"({self.draft_phase}) → {self.gewaehlt or '-'}")

    # --- Auswertung -----------------------------------------------------
    @property
    def spitze(self):
        """Die Slugs unserer Empfehlungen in ihrer Reihenfolge."""
        return [e.get("slug") for e in (self.empfehlungen or [])]

    def overlap(self, tiefe):
        """Wie viele der fremden Top-`tiefe` stehen auch bei uns in den Top-`tiefe`?

        Reine Beobachtung. Uebereinstimmung ist KEIN Qualitaetsmass - zwei
        Systeme koennen sich einig und beide falsch sein, und ein guter
        Pick kann bei genau einem von beiden stehen.
        """
        fremd = [s for s in (self.competitor_top or [])][:tiefe]
        if not fremd:
            return None
        unsere = set(self.spitze[:tiefe])
        return sum(1 for s in fremd if s in unsere)
