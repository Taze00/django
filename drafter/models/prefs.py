"""Persoenliche Einstellungen je Nutzer und Brawler.

Haengt am bestehenden `django.contrib.auth.User` des Projekts - kein
zweites Nutzersystem, keine Kopie von Profildaten. Wer nicht angemeldet
ist, kann den Drafter trotzdem benutzen; seine Werte liegen dann in der
Session (siehe services/personal.py) und dieses Modell bleibt leer.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from drafter.models.base import Zeitstempel


class UserBrawlerPreference(Zeitstempel):
    """Wie sicher ein Nutzer einen Brawler spielt.

    Drei Felder statt eines: `confidence` ist die selbst eingeschaetzte
    Sicherheit, `measured_performance` die spaeter aus echten Matches
    gemessene. Getrennt, weil beide unterschiedlich verlaesslich sind und
    man ihre Abweichung sehen koennen soll ("du haeltst dich fuer besser,
    als du bist" ist eine nuetzliche Aussage).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="brawler_preferences",
    )
    brawler = models.ForeignKey(
        "drafter.Brawler", on_delete=models.CASCADE, related_name="user_preferences"
    )

    confidence = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0-100. Selbsteinschätzung. 50 = neutral.",
    )
    favorite = models.BooleanField(default=False)
    avoid = models.BooleanField(default=False, help_text="Spiele ich nicht")
    notes = models.TextField(blank=True)

    games_played = models.PositiveIntegerField(default=0)
    measured_performance = models.FloatField(
        null=True, blank=True, help_text="0-100, später aus echten Matches"
    )

    class Meta:
        unique_together = [("user", "brawler")]
        ordering = ["brawler__name"]
        verbose_name = "Brawler-Einstellung"
        verbose_name_plural = "Brawler-Einstellungen"

    def __str__(self):
        return f"{self.user}: {self.brawler} ({self.confidence})"

    @property
    def combined_confidence(self):
        """Selbsteinschaetzung und Messung zusammengefuehrt.

        Solange keine Messung existiert, zaehlt allein die
        Selbsteinschaetzung. Mit Messung wandert das Gewicht dorthin -
        aber erst ab genug Spielen, sonst schlaegt ein Ausreisser durch.
        """
        if self.measured_performance is None or self.games_played < 10:
            return float(self.confidence)
        anteil = min(0.7, self.games_played / 100.0)
        return (1 - anteil) * self.confidence + anteil * self.measured_performance
