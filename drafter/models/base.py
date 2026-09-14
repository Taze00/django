"""Gemeinsame Bausteine der Drafter-Modelle.

Namensgebung: **Feldnamen englisch, Kommentare und Anzeigetexte
deutsch.** Die Domaene ist durchgaengig englisch (Brawler, Gadget,
Star Power, anti_tank), deutsche Feldnamen neben englischen JSON-Keys
waeren ein Mischmasch. Dieselbe Linie faehrt `fitness/`.
"""

from django.db import models


class Datenquelle(models.TextChoices):
    """Woher ein Wert stammt - die wichtigste Angabe des ganzen Systems.

    Ohne dieses Feld kann die Oberflaeche nicht zwischen "von Hand
    geschaetzt" und "aus 40 000 Matches gerechnet" unterscheiden, und
    genau diese Unterscheidung trennt ein ehrliches Werkzeug von einem,
    das Zahlen erfindet.
    """

    DEMO = "demo", "Demo-Daten (geschätzt)"
    MANUAL = "manual", "Manuell gepflegt"
    AGGREGATED = "aggregated", "Aus Matchdaten berechnet"
    API = "api", "Aus der offiziellen API"


class Zeitstempel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class StatBasis(Zeitstempel):
    """Kontext und Stichprobe einer aggregierten Statistik.

    Eine nackte Zahl wie "Gale 58 %" ist wertlos - sie gilt fuer eine
    Map, einen Modus, einen Patch, einen Rangbereich und einen Zeitraum.
    Alle Stat-Tabellen erben deshalb diesen Kontext von Anfang an, auch
    wenn die MVP-Demodaten ihn nur teilweise fuellen. Spaetere Echtdaten
    brauchen so keine Migration der Wertespalten.

    `context_key` buendelt den Kontext zu einer Zeichenkette. Grund:
    Eindeutigkeit ueber mehrere NULL-faehige Fremdschluessel ist in SQL
    nicht portabel (NULL != NULL), und derselbe Schluessel dient
    nebenbei als Cache-Schluessel.
    """

    game_mode = models.ForeignKey(
        "drafter.GameMode", on_delete=models.CASCADE,
        null=True, blank=True, related_name="+",
        help_text="Leer = modusübergreifend",
    )
    brawl_map = models.ForeignKey(
        "drafter.BrawlMap", on_delete=models.CASCADE,
        null=True, blank=True, related_name="+",
        help_text="Leer = mapübergreifend",
    )
    patch = models.ForeignKey(
        "drafter.Patch", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
        help_text="Leer = patchübergreifend",
    )
    rank_pool = models.CharField(max_length=20, default="masters", db_index=True)

    window_start = models.DateField(null=True, blank=True)
    window_end = models.DateField(null=True, blank=True)

    games = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)

    # Der tatsaechlich benutzte Wert. Bei aggregierten Daten das Ergebnis
    # der Bayes-Glaettung, bei Demo-Daten die gepflegte Schaetzung.
    confidence = models.FloatField(
        default=0.0, help_text="0-1. Aus Stichprobe, Alter und Patchbezug."
    )
    source = models.CharField(
        max_length=20, choices=Datenquelle.choices, default=Datenquelle.DEMO
    )
    context_key = models.CharField(max_length=120, db_index=True, editable=False, blank=True)

    class Meta:
        abstract = True

    def berechne_context_key(self):
        teile = [
            f"m{self.game_mode_id or 0}",
            f"k{self.brawl_map_id or 0}",
            f"p{self.patch_id or 0}",
            f"r{self.rank_pool or '-'}",
        ]
        return "|".join(teile)

    def save(self, *args, **kwargs):
        self.context_key = self.berechne_context_key()
        super().save(*args, **kwargs)

    @property
    def is_demo(self):
        return self.source == Datenquelle.DEMO
