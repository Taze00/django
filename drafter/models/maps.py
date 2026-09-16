"""Modi und Maps.

Der Kniff: **Maps benutzen dasselbe Vokabular wie Brawler.** Ein
Map-Eintrag sagt nicht "ich bin offen", sondern "lange Reichweite zaehlt
hier 90, Waendebrechen 15". Damit ist Map-Fit ein Skalarprodukt aus
Brawlerprofil und Mapanforderung - und dieselbe Eigenschaft ist je nach
Map unterschiedlich viel wert, ohne dass irgendwo eine Sonderregel
steht.
"""

from django.core.exceptions import ValidationError
from django.db import models

from drafter import attributes as attr
from drafter.models.base import BildUrlFeld, Datenquelle, Zeitstempel


class GameMode(Zeitstempel):
    """Spielmodus. Traegt Grundanforderungen, die fuer jede seiner Maps gelten.

    Gem Grab braucht immer Mid-Kontrolle, Heist immer Schaden aufs Ziel -
    unabhaengig davon, welche Map gerade laeuft. Die Map verfeinert das
    nur noch.
    """

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    # Kennung in der Datenquelle, z.B. die ID der offiziellen API. Leer,
    # bis sie aus echten Antworten bekannt ist - nicht erfunden, nicht
    # vorbefuellt. Der Import ordnet bevorzugt hierueber zu und faellt nur
    # ohne ID auf den Namen zurueck: Namen aendern Schreibweise und
    # Uebersetzung, IDs nicht.
    external_id = models.CharField(
        max_length=40, null=True, blank=True, unique=True,
        help_text="ID in der Datenquelle (z.B. offizielle API). Leer lassen, bis sie aus echten Antworten bekannt ist.",
    )
    description = models.CharField(max_length=200, blank=True)

    base_requirements = models.JSONField(
        default=dict, blank=True,
        help_text="Anforderungen des Modus, Schlüssel aus drafter.attributes, 0-100",
    )
    # Was der Modus vom Team verlangt, in Worten - fuer die Coach-Saetze
    # ("Win Condition: Mid halten und Edelsteine sichern").
    win_condition = models.CharField(max_length=200, blank=True)

    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Spielmodus"
        verbose_name_plural = "Spielmodi"

    def __str__(self):
        return self.name

    def clean(self):
        fehler = attr.pruefe_attribute(
            self.base_requirements, attr.ATTRIBUT_KEYS, "base_requirements"
        )
        if fehler:
            raise ValidationError(fehler)


class BrawlMap(Zeitstempel):
    """Eine Map.

    Heisst `BrawlMap` und nicht `Map`, damit `from ... import Map` in
    keiner Datei mit der eingebauten `map`-Funktion oder `typing.Map`-
    artigen Namen verwechselt werden kann.
    """

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)
    # Kennung in der Datenquelle, z.B. die ID der offiziellen API. Leer,
    # bis sie aus echten Antworten bekannt ist - nicht erfunden, nicht
    # vorbefuellt. Der Import ordnet bevorzugt hierueber zu und faellt nur
    # ohne ID auf den Namen zurueck: Namen aendern Schreibweise und
    # Uebersetzung, IDs nicht.
    external_id = models.CharField(
        max_length=40, null=True, blank=True, unique=True,
        help_text="ID in der Datenquelle (z.B. offizielle API). Leer lassen, bis sie aus echten Antworten bekannt ist.",
    )
    game_mode = models.ForeignKey(
        GameMode, on_delete=models.CASCADE, related_name="maps"
    )

    requirements = models.JSONField(
        default=dict, blank=True,
        help_text=(
            "Wie wichtig jede Eigenschaft auf dieser Map ist, 0-100. "
            "Überschreibt die Modus-Grundwerte."
        ),
    )
    traits = models.JSONField(
        default=dict, blank=True,
        help_text=(
            "Beschreibende Merkmale für Coach-Texte: openness, wall_density, "
            "bush_density, choke_points, lane_count (je 0-100 bzw. Anzahl)"
        ),
    )

    image_url = BildUrlFeld()
    notes = models.TextField(blank=True)
    source = models.CharField(
        max_length=20, choices=Datenquelle.choices, default=Datenquelle.DEMO
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["game_mode__order", "name"]
        unique_together = [("name", "game_mode")]
        verbose_name = "Map"
        verbose_name_plural = "Maps"

    def __str__(self):
        return f"{self.name} ({self.game_mode.name})"

    def clean(self):
        fehler = attr.pruefe_attribute(self.requirements, attr.ATTRIBUT_KEYS, "requirements")
        if fehler:
            raise ValidationError(fehler)

    def effektive_anforderungen(self):
        """Modus-Grundwerte, von den Map-Werten ueberschrieben.

        Bewusst Ueberschreiben statt Mitteln: wenn eine Map ausdruecklich
        sagt "lange Reichweite 20", soll der Modus-Grundwert 70 nicht zu
        45 verwaessern. Was die Map nicht erwaehnt, erbt sie.
        """
        werte = dict(self.game_mode.base_requirements or {})
        werte.update(self.requirements or {})
        return werte

    def anforderungs_vektor(self):
        """Anforderungen als {key: 0-1} ueber das volle Vokabular."""
        return attr.als_vektor(self.effektive_anforderungen())

    def trait(self, key, standard=50):
        return float((self.traits or {}).get(key, standard))

    @property
    def is_demo(self):
        return self.source == Datenquelle.DEMO

    def wichtigste_anforderungen(self, anzahl=4):
        """Die praegenden Eigenschaften dieser Map - fuer Erklaertexte."""
        werte = self.effektive_anforderungen()
        sortiert = sorted(
            ((k, v) for k, v in werte.items() if k in attr.EIGENSCHAFT_NACH_KEY),
            key=lambda p: -p[1],
        )
        return [attr.EIGENSCHAFT_NACH_KEY[k] for k, _ in sortiert[:anzahl]]
