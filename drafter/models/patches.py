"""Patches und Balanceaenderungen.

Wozu: alte Matchdaten sind nach einem Rework wertlos und nach einem
kleinen Schadensnerf fast noch gueltig. Ohne festgehaltene Patches kann
das System diesen Unterschied nicht kennen und wuerde Daten von vor
sechs Monaten so ernst nehmen wie die von gestern.

Im MVP sind hier nur ein Eintrag und keine Aenderungen gepflegt - die
Gewichtungslogik (services/patch_weighting.py) laeuft trotzdem und
liefert dann neutrale Faktoren.
"""

from django.db import models

from drafter.models.base import Zeitstempel


class Patch(Zeitstempel):
    name = models.CharField(max_length=60, unique=True, help_text="z.B. '2026-09 Herbstupdate'")
    released_on = models.DateField()
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)

    # Ein Patchdatum ist EXTERNE fachliche Information. Es darf nicht aus
    # der ersten gesehenen Partie, dem letzten Collector-Lauf oder dem
    # heutigen Datum abgeleitet werden - ein geratenes Datum sieht genauso
    # aus wie ein gepflegtes und schneidet still die Statistik.
    #
    # Genau das ist am 2026-09-19 passiert: `seed_brawl_data` schrieb bei
    # jedem Lauf `released_on = heute`, der Platzhalter sprang dadurch auf
    # einen Tag NACH der juengsten Partie, und das Fenster "seit Patch"
    # war leer. Deshalb steht hier jetzt, woher das Datum kommt.
    datum_bestaetigt = models.BooleanField(
        default=False,
        help_text="True nur, wenn das Datum aus einer externen Quelle gepflegt wurde",
    )
    datum_quelle = models.CharField(
        max_length=200, blank=True,
        help_text="Woher das Datum stammt - Ankündigung, Patch Notes, Beobachtung",
    )

    class Meta:
        ordering = ["-released_on"]
        verbose_name = "Patch"
        verbose_name_plural = "Patches"

    def __str__(self):
        return self.name

    @classmethod
    def aktueller(cls):
        return cls.objects.filter(is_current=True).first() or cls.objects.first()

    @property
    def datumslage(self):
        """Kurztext fuer Oberflaeche und Debug: taugt dieses Datum als Grenze?"""
        if self.datum_bestaetigt:
            return f"bestätigt{f' ({self.datum_quelle})' if self.datum_quelle else ''}"
        return "unbestätigt - Platzhalter, nicht als Patchgrenze belastbar"


class BrawlerBalanceChange(Zeitstempel):
    """Was ein Patch mit einem Brawler gemacht hat.

    `severity` ist das Feld, das die Statistikgewichtung tatsaechlich
    liest - die Einzelwerte darunter sind Dokumentation und spaetere
    Lernmerkmale. Lieber eine grobe, gepflegte Einstufung als sechs
    genaue Felder, die niemand fuellt.
    """

    class Severity(models.TextChoices):
        NONE = "none", "Keine Änderung"
        SMALL = "small", "Klein"
        MEDIUM = "medium", "Mittel"
        LARGE = "large", "Groß"
        REWORK = "rework", "Rework"

    class Richtung(models.TextChoices):
        BUFF = "buff", "Buff"
        NERF = "nerf", "Nerf"
        MIXED = "mixed", "Gemischt"
        NEUTRAL = "neutral", "Neutral"

    patch = models.ForeignKey(Patch, on_delete=models.CASCADE, related_name="changes")
    brawler = models.ForeignKey(
        "drafter.Brawler", on_delete=models.CASCADE, related_name="balance_changes"
    )

    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.SMALL)
    direction = models.CharField(max_length=10, choices=Richtung.choices, default=Richtung.NEUTRAL)

    health_change = models.FloatField(null=True, blank=True, help_text="Relativ, z.B. -0.05")
    damage_change = models.FloatField(null=True, blank=True)
    reload_change = models.FloatField(null=True, blank=True)
    range_change = models.FloatField(null=True, blank=True)
    gadget_change = models.CharField(max_length=200, blank=True)
    star_power_change = models.CharField(max_length=200, blank=True)
    hypercharge_change = models.CharField(max_length=200, blank=True)

    is_rework = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [("patch", "brawler")]
        ordering = ["-patch__released_on", "brawler__name"]
        verbose_name = "Balanceaenderung"
        verbose_name_plural = "Balanceaenderungen"

    def __str__(self):
        return f"{self.brawler} @ {self.patch}: {self.get_severity_display()}"

    def save(self, *args, **kwargs):
        # Ein Rework ist immer die hoechste Stufe - die beiden Felder
        # koennen sich sonst widersprechen.
        if self.is_rework:
            self.severity = self.Severity.REWORK
        elif self.severity == self.Severity.REWORK:
            self.is_rework = True
        super().save(*args, **kwargs)
