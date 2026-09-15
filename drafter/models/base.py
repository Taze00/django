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
    FIXTURE = "fixture", "Aus gespeicherten Match-Dateien"
    SYNTHETIC = "synthetic", "Synthetische Testdaten"
    AGGREGATED = "aggregated", "Aus Matchdaten berechnet (gemischte Quellen)"
    API = "api", "Aus der offiziellen API"


# Quellen, deren Zahlen NICHT gemessen sind. Gepflegte Werte zaehlen
# ausdruecklich dazu: auch eine sorgfaeltige Einschaetzung von Hand ist
# keine Messung. Synthetische Fixtures ebenfalls - sie existieren, um die
# Pipeline zu testen, nicht um etwas ueber das Spiel auszusagen.
#
# Daran haengt der Confidence-Deckel (services/confidence.py): solange
# ein Draft nur auf solchen Quellen beruht, zeigt die Oberflaeche nie
# mehr als "Niedrig".
NICHT_GEMESSEN = frozenset({Datenquelle.DEMO, Datenquelle.MANUAL, Datenquelle.SYNTHETIC})


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
    # Welches Aggregationsfenster diese Zeile beschreibt. Gehoert zum
    # context_key: "Gale, 7 Tage" und "Gale, seit Patch" sind zwei
    # verschiedene Aussagen und duerfen sich nicht gegenseitig
    # ueberschreiben. Leer bei gepflegten Werten, die kein Fenster haben.
    window_label = models.CharField(
        max_length=20, blank=True, default="",
        help_text="7d, 30d, 90d, seit_patch - leer bei gepflegten Werten",
    )

    # --- Stichprobe -----------------------------------------------------
    # Drei Zahlen, weil sie drei verschiedene Fragen beantworten:
    #   games/wins   - was wurde tatsaechlich gezaehlt?
    #   sample_size  - wie viel davon zaehlt nach Zeit- und Patchabschlag?
    #   raw/adjusted - was folgt daraus, ungeglaettet und geglaettet?
    # Eine 62-%-Quote aus 30 Spielen, die alle vor einem Rework lagen, hat
    # games=30, aber sample_size nahe 0 - und genau das soll sichtbar sein.
    games = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    sample_size = models.FloatField(
        default=0.0,
        help_text="Effektive Stichprobe: Summe der Zeit- und Patchgewichte (<= games)",
    )
    raw_rate = models.FloatField(
        null=True, blank=True, help_text="wins / games - ungeglättet, ungewichtet",
    )
    adjusted_rate = models.FloatField(
        null=True, blank=True,
        help_text="Gewichtet und Bayes-geglättet - der Wert, mit dem gerechnet wird",
    )

    # Bei aggregierten Daten aus der effektiven Stichprobe gerechnet, bei
    # gepflegten Daten die gepflegte Einschaetzung.
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
            f"w{self.window_label or '-'}",
        ]
        return "|".join(teile)

    def save(self, *args, **kwargs):
        self.context_key = self.berechne_context_key()
        super().save(*args, **kwargs)

    @property
    def ist_gemessen(self):
        return self.source not in NICHT_GEMESSEN

    @property
    def is_demo(self):
        """Nicht gemessen - Demo, von Hand gepflegt oder synthetisch.

        Heisst weiter `is_demo`, weil die Engine an dieser Stelle genau
        eine Frage stellt: "darf ich diese Zahl als Messung ausgeben?"
        """
        return not self.ist_gemessen
