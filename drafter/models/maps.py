"""Modi und Maps.

Der Kniff: **Maps benutzen dasselbe Vokabular wie Brawler.** Ein
Map-Eintrag sagt nicht "ich bin offen", sondern "lange Reichweite zaehlt
hier 90, Waendebrechen 15". Damit ist Map-Fit ein Skalarprodukt aus
Brawlerprofil und Mapanforderung - und dieselbe Eigenschaft ist je nach
Map unterschiedlich viel wert, ohne dass irgendwo eine Sonderregel
steht.
"""

from django.core.exceptions import ValidationError
from datetime import timedelta

from django.db import models

from drafter import attributes as attr
from drafter import config
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


class BrawlMapQuerySet(models.QuerySet):
    def waehlbare(self):
        """Gepflegte ODER aktuell in Ranked beobachtete Maps.

        Eine Abfrage statt einer Schleife ueber `waehlbar`, damit Views
        und Kommandos dieselbe Menge bekommen - die Definition steht nur
        hier. Siehe config.RANKED_MAP_FENSTER_TAGE.
        """
        from django.utils import timezone
        grenze = timezone.now() - timedelta(days=config.RANKED_MAP_FENSTER_TAGE)
        return self.filter(
            models.Q(is_active=True)
            | (models.Q(last_seen_ranked__gte=grenze)
               & models.Q(observed_ranked_games__gte=config.RANKED_MAP_MIN_PARTIEN))
        )


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
    # Von Hand freigeschaltet. Bleibt bestehen - eine Map, die jemand
    # bewusst gepflegt hat, verschwindet nicht, weil die Rotation sie
    # gerade nicht spielt.
    is_active = models.BooleanField(default=True)

    objects = BrawlMapQuerySet.as_manager()

    # Beobachtung statt Pflege: was in gezaehlten soloRanked-Partien
    # tatsaechlich vorkam. Wird aus den importierten Partien gerechnet
    # (`aktualisiere_ranked_maps`), nie von Hand gesetzt.
    #
    # Warum das ueberhaupt noetig ist: am 2026-09-19 lagen 10 188 gezaehlte
    # Partien auf 30 Maps - der Drafter bot 8 an, aus dem Demo-Seed, und
    # nur 1 966 Partien (20 %) lagen darauf. Bounty und Hot Zone hatten
    # keine einzige anwaehlbare Map, obwohl Hot Zone mit 2 240 Partien der
    # meistgespielte Modus ist.
    observed_ranked_games = models.PositiveIntegerField(default=0)
    last_seen_ranked = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["game_mode__order", "name"]
        # KEINE Eindeutigkeit ueber den Namen: Supercell vergibt denselben
        # Mapnamen mehrfach mit verschiedenen IDs (beobachtet bei
        # 'Siberian Stand Off', 'Stockpile Stadium', 'Insane Streamer').
        # Bis zum 2026-09-19 stand hier unique_together("name",
        # "game_mode") - die zweite Map liess sich dadurch nicht anlegen,
        # der Import meldete einen Widerspruch und verwarf sie. Zusammen-
        # gefuehrt wurden sie nie, aber verloren gingen sie eben doch.
        # Eindeutig ist `external_id`; der Name ist eine Beschriftung.
        verbose_name = "Map"
        verbose_name_plural = "Maps"

    def __str__(self):
        return f"{self.name} ({self.game_mode.name})"

    def clean(self):
        fehler = attr.pruefe_attribute(self.requirements, attr.ATTRIBUT_KEYS, "requirements")
        fehler += attr.pruefe_map_traits(self.traits or {})
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

    @property
    def ranked_aktuell(self):
        """Kam diese Map zuletzt in gezaehlten Ranked-Partien vor?

        Die Identitaet ist die `external_id`, nie der Name: zwei Maps
        koennen gleich heissen und verschiedene IDs tragen (beobachtet bei
        'Siberian Stand Off' und 'Stockpile Stadium'). Sie bleiben zwei
        Maps, auch wenn eine Zusammenfuehrung bequemer waere.
        """
        if self.last_seen_ranked is None:
            return False
        if self.observed_ranked_games < config.RANKED_MAP_MIN_PARTIEN:
            return False
        from django.utils import timezone
        alter = timezone.now() - self.last_seen_ranked
        return alter.days <= config.RANKED_MAP_FENSTER_TAGE

    @property
    def waehlbar(self):
        """Darf der Drafter sie anbieten? Gepflegt ODER aktuell beobachtet."""
        return bool(self.is_active or self.ranked_aktuell)

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
