# -*- coding: utf-8 -*-
"""Wen der Collector kennt - und was ein Lauf gebracht hat.

`TrackedPlayer` ist Warteschlange und Gedaechtnis zugleich: wer ansteht,
wer wann zuletzt abgefragt wurde, wer zuletzt einen Fehler lieferte.
`last_fetched_at` verhindert, dass derselbe Spieler in jedem Lauf erneut
abgerufen wird; `next_fetch_after` pausiert Spieler nach Fehlern.

`depth` begrenzt die Entdeckung: Saat (Rangliste, manuell) hat Tiefe 0,
ihre Mitspieler Tiefe 1. Gespeichert und abgerufen wird nur bis
`config.COLLECTOR_MAX_TIEFE` - es gibt keine offene Rekursion.
"""

from django.db import models
from django.utils import timezone

from drafter.models.base import Zeitstempel


class TrackedPlayer(Zeitstempel):
    class Origin(models.TextChoices):
        RANKING = "ranking", "Globale Trophäen-Rangliste"
        DISCOVERED = "discovered", "Aus einem soloRanked-Battlelog entdeckt"
        OFFICIAL_OBSERVED = "official_observed", "Direkt in offizieller API beobachtet (kein Ranked-Nachweis)"
        MANUAL = "manual", "Manuell angegeben"

    tag = models.CharField(max_length=20, unique=True)
    origin = models.CharField(max_length=20, choices=Origin.choices)
    depth = models.PositiveSmallIntegerField(
        default=0, help_text="0 = Saat (Rangliste, manuell), 1 = Mitspieler einer Saat, ..."
    )
    discovered_from = models.CharField(max_length=20, blank=True)
    # Wie geliefert von /rankings/global/players - bei jedem Ranglisten-
    # abruf neu gesetzt, fuer Spieler ausserhalb der Top 200 leer.
    ranking_position = models.PositiveIntegerField(null=True, blank=True)
    ranking_trophies = models.PositiveIntegerField(null=True, blank=True)

    # Letzte beantwortete Abfrage (200 oder 404). Voruebergehende Fehler
    # setzen stattdessen `next_fetch_after` - ein 503 soll den Spieler
    # nicht fuer den ganzen Abrufabstand sperren.
    last_fetched_at = models.DateTimeField(null=True, blank=True, db_index=True)
    next_fetch_after = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=20, blank=True)
    last_error = models.CharField(max_length=300, blank=True)
    fetch_count = models.PositiveIntegerField(default=0)
    error_streak = models.PositiveSmallIntegerField(default=0)
    last_battle_count = models.PositiveSmallIntegerField(null=True, blank=True)
    last_solo_ranked_count = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["depth", "ranking_position", "tag"]
        verbose_name = "Beobachteter Spieler"
        verbose_name_plural = "Beobachtete Spieler"

    def __str__(self):
        return f"{self.tag} (Tiefe {self.depth})"


class CollectorRun(models.Model):
    """Ein Lauf des Collectors - Parameter und Bericht, zum Nachlesen."""

    class Status(models.TextChoices):
        RUNNING = "running", "Läuft"
        FINISHED = "finished", "Beendet"
        ABORTED = "aborted", "Abgebrochen"

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    abort_reason = models.CharField(max_length=500, blank=True)
    parameters = models.JSONField(default=dict)
    report = models.JSONField(default=dict)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Collector-Lauf"
        verbose_name_plural = "Collector-Läufe"

    def __str__(self):
        return f"{self.started_at:%Y-%m-%d %H:%M} {self.get_status_display()}"


class TaggedPlayer(models.Model):
    """Neue, belegte Frontier; alte Warteschlangen-Zeilen sind keine Saat.

    Der eindeutige Tag und die unveraenderten Abruf-/Cooldown-Felder liegen
    am TrackedPlayer. Eine erneute Entdeckung setzt sie niemals zurueck.
    """

    class Source(models.TextChoices):
        RANKING = "ranking", "Offizielle Trophäenrangliste"
        RANKED = "solo_ranked", "Beobachtet in neuer soloRanked-Partie"

    player = models.OneToOneField(
        TrackedPlayer, on_delete=models.PROTECT, related_name="tagged_frontier",
    )
    first_source = models.CharField(max_length=20, choices=Source.choices)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()
    discovery_depth = models.PositiveIntegerField(default=0)
    first_run = models.ForeignKey(CollectorRun, on_delete=models.PROTECT, related_name="+")


class TaggedPlayerObservation(models.Model):
    """Append-only Beleg: exakter JSON-Pointer, Rohantwort, Lauf und Graphkante.

    `query` belegt die abgefragte Identitaet aus der Anfragehuelle; es ist
    keine Behauptung, dass der Tag auch in einem Match enthalten war.
    """

    class Source(models.TextChoices):
        RANKING = "ranking", "Ranglisten-Tag"
        RANKED = "solo_ranked", "Tag in neuer soloRanked-Partie"
        QUERY = "query", "Erfolgreich abgefragter Battlelog"

    player = models.ForeignKey(TaggedPlayer, on_delete=models.PROTECT, related_name="observations")
    source = models.CharField(max_length=20, choices=Source.choices)
    observed_at = models.DateTimeField()
    payload = models.ForeignKey("drafter.RawPayload", on_delete=models.PROTECT, related_name="tag_observations")
    run = models.ForeignKey(CollectorRun, on_delete=models.PROTECT, related_name="tag_observations")
    json_pointer = models.CharField(max_length=160)
    queried_player = models.ForeignKey(TrackedPlayer, on_delete=models.PROTECT, null=True, related_name="+")
    match = models.ForeignKey("drafter.Match", on_delete=models.PROTECT, null=True, related_name="+")

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["player", "payload", "run", "source", "json_pointer"],
            name="drafter_unique_tag_observation",
        )]
