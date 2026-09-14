"""Aggregierte Statistiken.

Drei Tabellen, ein Muster: jede Zeile traegt ihren vollen Kontext
(Modus, Map, Patch, Rangbereich, Zeitfenster) und ihre Stichprobe mit.

Wichtig fuer spaeter: **hier stehen keine Rohmatches.** Rohdaten kommen
in eigene Tabellen (Phase 14), diese hier sind das vorberechnete
Ergebnis. Eine Empfehlung darf nie Millionen Matches live aggregieren -
sie hat dafuer 200 Millisekunden.
"""

from django.db import models

from drafter.models.base import Datenquelle, StatBasis


class BrawlerStat(StatBasis):
    """Wie stark ein Brawler in einem Kontext ist.

    Ein Modell fuer drei Auswertungsebenen, unterschieden ueber die
    NULL-baren Kontextfelder:

    - Map und Modus leer  -> allgemeine Meta-Staerke
    - nur Modus gesetzt   -> Modusstaerke
    - Map gesetzt         -> Mapstaerke

    Drei getrennte Tabellen mit identischen Spalten waeren dieselbe
    Information in dreifacher Pflege.
    """

    brawler = models.ForeignKey(
        "drafter.Brawler", on_delete=models.CASCADE, related_name="stats"
    )

    # 0-1. Bei aggregierten Daten das Bayes-geglaettete Ergebnis, bei
    # Demo-Daten die gepflegte Einschaetzung.
    win_rate = models.FloatField(default=0.5)
    pick_rate = models.FloatField(default=0.0, help_text="0-1, Anteil der Drafts")
    ban_rate = models.FloatField(default=0.0, help_text="0-1")

    class Meta:
        verbose_name = "Brawler-Statistik"
        verbose_name_plural = "Brawler-Statistiken"
        indexes = [models.Index(fields=["brawler", "context_key"])]
        constraints = [
            models.UniqueConstraint(
                fields=["brawler", "context_key"], name="drafter_brawlerstat_eindeutig"
            )
        ]

    def __str__(self):
        wo = self.brawl_map or self.game_mode or "allgemein"
        return f"{self.brawler} @ {wo}: {self.win_rate:.0%}"

    @property
    def staerke(self):
        """Winrate als Abweichung von 50 % in [-1, +1].

        Eine 60-%-Winrate wird damit zu +0.2 - das ist die Skala, mit der
        die Scoring-Engine rechnet. Winrates direkt zu addieren waere der
        Fehler, den config.py ausdruecklich verbietet.
        """
        return max(-1.0, min(1.0, (self.win_rate - 0.5) * 2))


class CounterStat(StatBasis):
    """Wie gut `brawler` gegen `enemy` dasteht.

    `advantage` ist ein *vorzeichenbehafteter Vorteil* in [-1, +1] und
    keine Winrate. Grund steht in der Aufgabenstellung und ist wichtig:
    eine gemessene 62-%-Winrate ist kein 62-%-Counter, weil Map, Rang,
    Mitspieler und Patch mitreden. Der Vorteil ist die bereinigte
    Groesse, `win_rate` und `games` behalten die Rohmessung daneben.

    Die Beziehung ist **nicht** automatisch symmetrisch: der
    Gegenvorteil wird als eigene Zeile gepflegt, sonst kann man
    "beide tun sich schwer" nicht ausdruecken.
    """

    brawler = models.ForeignKey(
        "drafter.Brawler", on_delete=models.CASCADE, related_name="counter_stats"
    )
    enemy = models.ForeignKey(
        "drafter.Brawler", on_delete=models.CASCADE, related_name="countered_by_stats"
    )

    advantage = models.FloatField(
        default=0.0, help_text="-1 bis +1. Positiv = brawler ist im Vorteil."
    )
    win_rate = models.FloatField(null=True, blank=True, help_text="Rohmessung, falls vorhanden")
    reason = models.CharField(
        max_length=200, blank=True,
        help_text="Warum - wird im Coach-Text zitiert, z.B. 'schiebt ihn aus der Reichweite'",
    )

    class Meta:
        verbose_name = "Counter"
        verbose_name_plural = "Counter"
        indexes = [models.Index(fields=["brawler", "enemy"])]
        constraints = [
            models.UniqueConstraint(
                fields=["brawler", "enemy", "context_key"],
                name="drafter_counterstat_eindeutig",
            ),
            models.CheckConstraint(
                condition=~models.Q(brawler=models.F("enemy")),
                name="drafter_counter_nicht_gegen_sich_selbst",
            ),
        ]

    def __str__(self):
        return f"{self.brawler} vs {self.enemy}: {self.advantage:+.2f}"


class SynergyStat(StatBasis):
    """Wie gut zwei Brawler zusammen funktionieren.

    `synergy` ist bewusst der *Mehrwert*, nicht die gemeinsame Winrate.
    Sonst gaelten zwei ohnehin starke Brawler automatisch als gute
    Synergie - der haeufigste Denkfehler in Draft-Werkzeugen. Sobald
    Matchdaten da sind, gilt:

        synergy = gemeinsame Leistung - erwartete Einzelleistung

    Das Paar wird normalisiert gespeichert (kleinere ID zuerst), damit
    (A,B) und (B,A) nicht zwei Zeilen ergeben.
    """

    brawler_a = models.ForeignKey(
        "drafter.Brawler", on_delete=models.CASCADE, related_name="synergies_a"
    )
    brawler_b = models.ForeignKey(
        "drafter.Brawler", on_delete=models.CASCADE, related_name="synergies_b"
    )

    synergy = models.FloatField(
        default=0.0, help_text="-1 bis +1. Positiv = mehr als die Summe der Teile."
    )
    win_rate = models.FloatField(null=True, blank=True, help_text="Gemeinsame Rohwinrate")
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Synergie"
        verbose_name_plural = "Synergien"
        indexes = [models.Index(fields=["brawler_a", "brawler_b"])]
        constraints = [
            models.UniqueConstraint(
                fields=["brawler_a", "brawler_b", "context_key"],
                name="drafter_synergystat_eindeutig",
            ),
            models.CheckConstraint(
                condition=models.Q(brawler_a__lt=models.F("brawler_b")),
                name="drafter_synergie_paar_normalisiert",
            ),
        ]

    def __str__(self):
        return f"{self.brawler_a} + {self.brawler_b}: {self.synergy:+.2f}"

    def save(self, *args, **kwargs):
        # Paar normalisieren, bevor die Datenbank es ablehnt.
        if self.brawler_a_id and self.brawler_b_id and self.brawler_a_id > self.brawler_b_id:
            self.brawler_a_id, self.brawler_b_id = self.brawler_b_id, self.brawler_a_id
        super().save(*args, **kwargs)
