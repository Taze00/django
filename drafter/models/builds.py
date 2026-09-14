"""Builds: Gadgets, Star Powers, Gears, Hypercharges - und wann welcher passt.

Zwei Modelle statt einer Tabelle voller Empfehlungen:

`BrawlerItem` ist der **Katalog** (was es gibt), `BuildRule` die
**Begruendung** (wann es passt). Dadurch kann derselbe Gegenstand in
mehreren Situationen empfohlen werden, jedesmal mit eigenem Grund - und
die Oberflaeche kann "Standard" und "gegen zwei Nahkaempfer" getrennt
anzeigen, wie in der Aufgabenstellung gewuenscht.

Zur Datenlage: ob die offizielle API ueberhaupt Builds historischer
Matches liefert, ist ungeprueft. Deshalb kommen die Empfehlungen hier
aus gepflegten Regeln, und ein spaeterer `BuildDataProvider` kann sie
ergaenzen oder ersetzen. Fehlen zu einem Brawler alle Eintraege, liefert
die Engine schlicht keinen Build - sie bricht nicht ab.
"""

from django.db import models

from drafter.models.base import Datenquelle, Zeitstempel


class BrawlerItem(Zeitstempel):
    """Ein ausruestbarer Gegenstand.

    `brawler = None` heisst "gilt fuer alle" - so sind die generischen
    Gears (Schaden, Schild, Tempo, ...) ein einziger Datensatz statt
    einer Kopie je Brawler.
    """

    class Kind(models.TextChoices):
        GADGET = "gadget", "Gadget"
        STAR_POWER = "star_power", "Star Power"
        GEAR = "gear", "Gear"
        HYPERCHARGE = "hypercharge", "Hypercharge"

    brawler = models.ForeignKey(
        "drafter.Brawler", on_delete=models.CASCADE, related_name="items",
        null=True, blank=True, help_text="Leer = generisch (z.B. Gears)",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90)
    description = models.CharField(max_length=300, blank=True)

    # Grundwert ohne jeden Kontext: manche Gadgets sind schlicht immer
    # die bessere Wahl. Kontextregeln kommen obendrauf.
    base_weight = models.FloatField(
        default=0.5, help_text="0-1. Wie oft ist das die Standardwahl?"
    )
    source = models.CharField(
        max_length=20, choices=Datenquelle.choices, default=Datenquelle.DEMO
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["brawler__name", "kind", "name"]
        unique_together = [("brawler", "kind", "slug")]
        verbose_name = "Ausruestung"
        verbose_name_plural = "Ausruestung"

    def __str__(self):
        wer = self.brawler.name if self.brawler_id else "generisch"
        return f"{wer} - {self.get_kind_display()}: {self.name}"

    @property
    def is_demo(self):
        return self.source == Datenquelle.DEMO


class BuildRule(Zeitstempel):
    """Wann ein Gegenstand besonders gut passt.

    `condition` ist ein kleines, festes JSON-Vokabular - kein Code, kein
    eval. Die Auswertung steht in `services/builds.py` und kennt genau
    diese Schluessel:

        enemy_role_count  {"tank": 2}        mind. 2 Tanks im Gegnerteam
        enemy_has         ["buster"]         dieser Brawler ist gepickt
        enemy_attr_min    {"close_range": 0.6}  staerkster Gegner in dem Wert
        own_missing       ["anti_tank"]      unserem Team fehlt das
        own_has_role      ["sniper"]         wir haben so eine Rolle
        map_trait_min     {"choke_points": 60}
        map_trait_max     {"openness": 40}
        mode              ["gem-grab"]

    Mehrere Schluessel gelten als UND. Wer ein ODER braucht, legt zwei
    Regeln an - das ist lesbarer als eine Ausdruckssprache, die
    irgendwann doch ein Parser waere.
    """

    item = models.ForeignKey(BrawlerItem, on_delete=models.CASCADE, related_name="rules")
    condition = models.JSONField(default=dict, blank=True)
    weight = models.FloatField(
        default=0.3, help_text="Zuschlag auf base_weight, wenn die Bedingung zutrifft"
    )
    reason_template = models.CharField(
        max_length=200,
        help_text="Begründung im Coach-Text. Platzhalter: {brawler} {map} {mode} {gegner}",
    )
    priority = models.IntegerField(default=0, help_text="Höher = wird zuerst genannt")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-priority", "-weight"]
        verbose_name = "Build-Regel"
        verbose_name_plural = "Build-Regeln"

    def __str__(self):
        return f"{self.item.name}: {self.reason_template[:50]}"
