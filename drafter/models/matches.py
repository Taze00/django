# -*- coding: utf-8 -*-
"""Rohdaten: gelieferte Antworten und die daraus gelesenen Matches.

Streng getrennt von den Stat-Tabellen. Hier steht, was passiert ist;
dort steht, was daraus folgt. Die Engine liest nur dort - nie hier.

Drei Ebenen, jede mit eigenem Zweck:

    RawPayload   die Lieferung, UNVERAENDERT  -> neu auswertbar ohne erneuten Abruf
    Match        eine Partie, dedupliziert     -> zaehlt genau einmal
    MatchPlayer  wer mit welchem Brawler       -> Grundlage aller Statistiken
    MatchBan     gebannte Brawler, falls die Quelle sie kennt

Kein MatchTeam-Modell: eine Partie hat genau zwei Seiten, und `side`
am Spieler plus `winner_side` am Match tragen dieselbe Information ohne
eine Tabelle, deren Zeilen nichts ausser einem Fremdschluessel enthielten.
"""

from django.db import models
from django.utils import timezone

from drafter.models.base import Datenquelle, Zeitstempel


class RawPayload(Zeitstempel):
    """Eine gelieferte Datei oder API-Antwort - so, wie sie kam.

    `content_hash` macht den Import idempotent: dieselbe Datei zweimal
    einzuspielen, aendert nichts. Und weil der Inhalt unveraendert
    bleibt, kann ein spaeter korrigierter Parser alte Lieferungen neu
    auswerten, ohne die Quelle erneut abzufragen.
    """

    class ParseStatus(models.TextChoices):
        PARSED = "parsed", "Ausgewertet"
        UNSUPPORTED = "unsupported", "Format noch nicht auswertbar"
        ERROR = "error", "Fehlerhaft"

    source = models.CharField(max_length=20, choices=Datenquelle.choices)
    format = models.CharField(max_length=60, help_text="z.B. drafter.match.v1")
    reference = models.CharField(
        max_length=300, blank=True, help_text="Dateiname, Spieler-Tag o.ae."
    )
    content_hash = models.CharField(max_length=64, unique=True)
    payload = models.JSONField()
    fetched_at = models.DateTimeField(default=timezone.now)

    parse_status = models.CharField(
        max_length=20, choices=ParseStatus.choices, default=ParseStatus.PARSED
    )
    parse_message = models.TextField(blank=True)
    match_count = models.PositiveIntegerField(default=0)
    new_match_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-fetched_at"]
        verbose_name = "Rohlieferung"
        verbose_name_plural = "Rohlieferungen"

    def __str__(self):
        return f"{self.reference or self.content_hash[:10]} ({self.format})"


class Match(Zeitstempel):
    """Eine gespielte Partie - genau einmal, egal wie oft gesehen.

    Wiedererkennung in zwei Stufen (services/ingest/fingerprint.py):

    1. `external_id` - die Partie-ID der Quelle, falls es eine gibt.
       Exakt, ohne Zeittoleranz.
    2. `reconstructed_fingerprint` - Fallback aus Zeit-Eimer, Map und
       beiden Teams, perspektivunabhaengig. Nur hier wirkt die
       Zeittoleranz.

    `fingerprint` ist der eindeutige Schluessel: bei bekannter Partie-ID
    deren Hash, sonst der rekonstruierte. Der rekonstruierte wird IMMER
    zusaetzlich gespeichert - sonst faende eine Sichtung ohne ID eine
    bereits gespeicherte Partie mit ID nicht wieder.

    Taucht dieselbe Partie in einem zweiten Battlelog auf, wird nur die
    Lieferung verknuepft - gezaehlt wird sie nicht noch einmal.

    Widersprechen sich zwei Sichtungen im Ergebnis, wird das Match als
    Konflikt markiert und bei der Aggregation ausgelassen. Welche Sicht
    stimmt, ist nicht entscheidbar; eine falsch gezaehlte Partie waere
    schlimmer als eine fehlende.
    """

    class Seite(models.TextChoices):
        A = "a", "Team A"
        B = "b", "Team B"
        DRAW = "draw", "Unentschieden"

    fingerprint = models.CharField(max_length=64, unique=True)
    reconstructed_fingerprint = models.CharField(max_length=64, blank=True, db_index=True)
    external_id = models.CharField(max_length=120, blank=True, db_index=True)
    source = models.CharField(max_length=20, choices=Datenquelle.choices, db_index=True)
    payloads = models.ManyToManyField(RawPayload, related_name="matches", blank=True)

    played_at = models.DateTimeField(db_index=True)
    game_mode = models.ForeignKey(
        "drafter.GameMode", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    brawl_map = models.ForeignKey(
        "drafter.BrawlMap", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    # Wie geliefert - auch wenn der Katalog Modus oder Map (noch) nicht
    # kennt. Dann bleibt der Fremdschluessel leer und der Name erhalten.
    mode_name = models.CharField(max_length=80, blank=True)
    map_name = models.CharField(max_length=120, blank=True)
    patch = models.ForeignKey(
        "drafter.Patch", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    rank_pool = models.CharField(max_length=20, default="alle", db_index=True)
    is_ranked = models.BooleanField(default=True)

    # Leer = unbekannt. Nie raten: eine Partie ohne bekanntes Ergebnis
    # zaehlt fuer keine Winrate.
    winner_side = models.CharField(max_length=5, blank=True, choices=Seite.choices)
    first_pick_side = models.CharField(max_length=1, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    # Partietyp, wie die Quelle ihn liefert. Offizielle API, beobachtet am
    # 2026-09-15: "ranked" = Trophaeen-Rangliste (trotz des Namens; mit
    # trophyChange), "soloRanked" = Ranked-Modus. `is_ranked` wird daraus
    # abgeleitet; der Rohwert bleibt, falls sich die Deutung als falsch erweist.
    battle_type = models.CharField(max_length=40, blank=True, db_index=True)
    # Kennungen der Quelle, roh. Offizielle API: event.modeId und event.id.
    # `event.id` bezeichnet Map UND Modus zusammen - dieselbe Map hat je
    # Modus eine eigene ID (beobachtet in /events/rotation).
    external_mode_id = models.CharField(max_length=40, blank=True, db_index=True)
    external_map_id = models.CharField(max_length=40, blank=True, db_index=True)

    has_conflict = models.BooleanField(default=False, db_index=True)
    conflict_note = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-played_at"]
        indexes = [models.Index(fields=["source", "played_at"])]
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"{self.played_at:%Y-%m-%d %H:%M} {self.map_name or '?'}"

    @property
    def ist_zaehlbar(self):
        """Darf diese Partie in Winrates eingehen?"""
        return self.winner_side in (self.Seite.A, self.Seite.B) and not self.has_conflict

    @property
    def gesehen(self):
        return self.payloads.count()


class MatchPlayer(models.Model):
    """Ein Spieler in einer Partie.

    `pick_order` und `build` bleiben leer, wenn die Quelle sie nicht
    kennt. Der offizielle Battlelog liefert beides nicht (geprueft am
    2026-09-15) - die Aggregation beruecksichtigt nur, was da ist.
    """

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="players")
    side = models.CharField(max_length=1)
    brawler = models.ForeignKey(
        "drafter.Brawler", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    brawler_name = models.CharField(max_length=80)
    player_tag = models.CharField(max_length=20, blank=True)
    pick_order = models.PositiveSmallIntegerField(null=True, blank=True)
    build = models.JSONField(null=True, blank=True)
    # Roh aus der Quelle. `trophies` bedeutet je nach Match.battle_type
    # etwas anderes: bei "soloRanked" war es in allen beobachteten Partien
    # der Ranked-Rang (bei allen sechs Spielern gleich), sonst Trophaeen.
    power = models.IntegerField(null=True, blank=True)
    trophies = models.IntegerField(null=True, blank=True)
    # Brawler-ID der Quelle, roh - unabhaengig davon, ob der Katalog sie kennt.
    external_brawler_id = models.CharField(max_length=40, blank=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["brawler", "side"])]
        verbose_name = "Match-Spieler"
        verbose_name_plural = "Match-Spieler"

    def __str__(self):
        return f"{self.brawler_name} ({self.side})"


class MatchBan(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="bans")
    side = models.CharField(max_length=1, blank=True)
    brawler = models.ForeignKey(
        "drafter.Brawler", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    brawler_name = models.CharField(max_length=80)
    order = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Match-Ban"
        verbose_name_plural = "Match-Bans"

    def __str__(self):
        return f"Ban {self.brawler_name}"
