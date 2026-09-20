"""Der Brawler-Katalog."""

from django.core.exceptions import ValidationError
from django.db import models

from drafter import attributes as attr
from drafter.models.base import BildUrlFeld, Datenquelle, Zeitstempel


class Brawler(Zeitstempel):
    """Ein Brawler mit Eigenschaftsprofil und Draft-Verhalten.

    Die 32 Eigenschaften liegen als JSON und nicht als 32 Spalten oder
    als Zeilentabelle vor:

    - 32 Spalten waeren bei jeder neuen Eigenschaft eine Migration und
      im Admin ein unbenutzbares Formular.
    - Eine Zeilentabelle (brawler, key, value) braucht fuer jede
      Bewertung einen Join ueber tausende Zeilen, und die Engine liest
      immer *alle* Eigenschaften *aller* Kandidaten.

    JSON kostet dafuer die Typsicherheit - die holt `clean()` zurueck,
    indem es gegen `drafter.attributes` prueft. Unbekannte Schluessel
    kommen damit gar nicht erst in die Datenbank.
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

    role = models.CharField(
        max_length=20, choices=attr.ROLLEN, default="damage", blank=True,
        help_text=(
            "Hauptarchetyp - für Filter, Anzeige und Rollenredundanz. "
            "Leer bei Einträgen ohne gepflegtes Profil (aus der API übernommen)."
        ),
    )
    tags = models.JSONField(
        default=list, blank=True,
        help_text="Weitere Archetypen, z.B. ['aggro', 'controller']",
    )

    attributes = models.JSONField(
        default=dict, blank=True,
        help_text="Schlüssel aus drafter.attributes, Werte 0-100. Fehlender Schlüssel = UNBEKANNT, eingetragene 0 = kann es wirklich nicht.",
    )
    draft_values = models.JSONField(
        default=dict, blank=True,
        help_text="Historisch. Seit 2026-09-20 nicht mehr im Scoring - Flexibilität und Draft-Position kommen aus Messung.",
    )

    # Bilder liegen NICHT im Repository: die Brawler-Artworks gehoeren
    # Supercell. Quelle ist das offizielle Fan Kit, von Hand geladen und
    # mit `import_fankit_bilder` eingespielt (liegt dann gitignored unter
    # static/drafter/fankit/). Ohne Bild zeigt die Oberflaeche eine
    # eingefaerbte Kachel mit Kuerzel.
    image_url = BildUrlFeld()
    color = models.CharField(
        max_length=7, default="#3a3f4b",
        help_text="Hex-Farbe der Platzhalterkachel, z.B. #7d5fff",
    )

    # --- Gepflegtes Draft-Wissen (Role & Ability Map) -------------------
    # Fachquelle, keine Messung: was ein Brawler im Draft TUT, nicht wie
    # stark er gerade ist. Leer, solange nichts gepflegt ist.
    draft_rolle = models.CharField(
        max_length=20, choices=attr.DRAFT_ROLLEN, blank=True,
        help_text="Aufgabe im Draft laut Role-&-Ability-Map (nicht die Katalogrolle)",
    )
    # Die Mechanikschicht: was ein Brawler objektiv HAT, nicht wie gut er
    # darin ist. Heute leer - gefuellt wird sie aus der Fachquelle
    # (services/mechanik.py), und dieses Feld ist der Platz fuer das, was
    # spaeter von Hand nachgetragen wird. Schluessel: mechanik.SCHLUESSEL.
    mechanik = models.JSONField(
        default=dict, blank=True,
        help_text="has_healing, has_wallbreak, range_category, … - Tatsachen, "
                  "keine Bewertungen. Fehlender Schlüssel = unbekannt.",
    )
    draft_faehigkeiten = models.JSONField(
        default=list, blank=True,
        help_text="Zusatzfähigkeiten laut Map: good_hyper, knockback_stun, wallbreak, "
                  "pierce, special. Leere Liste = keine der hervorgehobenen.",
    )

    # Ob dieser Brawler im Ranked-Modus ueberhaupt waehlbar ist. False
    # heisst: er fehlt dort NICHT - er gehoert nicht hin. Solche Brawler
    # zaehlen nirgends als Datenluecke und tauchen in keiner Empfehlung
    # auf, bleiben aber im Katalog. Supercell aendert das von Zeit zu
    # Zeit; die Sperre ist deshalb ein Feld und kein Codezweig.
    ranked_verfuegbar = models.BooleanField(
        default=True,
        help_text="Im Ranked-Modus wählbar? Aus = weder Empfehlung noch Datenlücke.",
    )

    source = models.CharField(
        max_length=20, choices=Datenquelle.choices, default=Datenquelle.DEMO
    )
    is_active = models.BooleanField(
        default=True, help_text="Aus dem Spiel entfernt oder noch nicht gepflegt"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Brawler"
        verbose_name_plural = "Brawler"

    def __str__(self):
        return self.name

    # --- Validierung ----------------------------------------------------
    def clean(self):
        fehler = attr.pruefe_attribute(self.attributes, attr.ATTRIBUT_KEYS, "attributes")
        fehler += attr.pruefe_attribute(
            self.draft_values, attr.DRAFTWERT_KEYS, "draft_values"
        )
        if self.draft_faehigkeiten is not None:
            if not isinstance(self.draft_faehigkeiten, list):
                fehler.append("draft_faehigkeiten: erwartet eine Liste")
            else:
                unbekannt = [
                    f for f in self.draft_faehigkeiten
                    if f not in attr.DRAFT_FAEHIGKEITEN_KEYS
                ]
                if unbekannt:
                    fehler.append(f"draft_faehigkeiten: unbekannt {unbekannt}")
        if not isinstance(self.tags, list):
            fehler.append("tags: erwartet eine Liste")
        else:
            unbekannt = [t for t in self.tags if t not in attr.ROLLEN_KEYS]
            if unbekannt:
                fehler.append(f"tags: unbekannte Rollen {unbekannt}")
        if fehler:
            raise ValidationError(fehler)

    # --- Datenstand ----------------------------------------------------
    @property
    def draft_rolle_label(self):
        return attr.DRAFT_ROLLEN_LABEL.get(self.draft_rolle, "")

    def kann(self, faehigkeit):
        """Traegt dieser Brawler diese Zusatzfaehigkeit laut Map?"""
        return faehigkeit in (self.draft_faehigkeiten or [])

    @property
    def hat_profil(self):
        """Gibt es ein gepflegtes Eigenschaftsprofil?

        Seit dem 2026-09-20 liefert `wert()` bei Unbekanntem `None`, die
        Unterscheidung steckt also im Zugriff selbst. `hat_profil` bleibt
        die grobe Frage "gibt es ueberhaupt gepflegte Eigenschaften" -
        fuer einzelne Schluessel fragt man `bekannt(key)`.
        """
        return bool(self.attributes)

    @property
    def hat_draftwerte(self):
        """Gepflegte Draft-Werte? Ohne sie liefert `draftwert()` 0.5 -
        ein Durchschnitt, der nicht gemessen, sondern angenommen waere."""
        return bool(self.draft_values)

    # --- Zugriff --------------------------------------------------------
    def bekannt(self, key):
        """Steht zu dieser Eigenschaft ueberhaupt etwas?

        Der Unterschied, um den es geht: **nicht eingetragen** heisst
        "wir wissen es nicht", **eingetragen mit 0** heisst "er kann das
        wirklich nicht". Bis zum 2026-09-20 war beides dasselbe, und
        daraus entstanden Phantomluecken - PAM mit 14 gepflegten
        Eigenschaften galt in den uebrigen 18 als nachweislich
        unfaehig, AMBER ohne Profil in allen 32.
        """
        return self.attributes is not None and key in self.attributes

    def wert(self, key):
        """Eigenschaft als 0-1 - oder **None**, wenn nichts bekannt ist.

        Wer eine Zahl braucht, nimmt `wert_oder()` und sagt damit
        ausdruecklich, welcher Ersatz gemeint ist. Eine stille 0 ist
        keine Antwort, sondern eine Behauptung.
        """
        if not self.bekannt(key):
            return None
        return float(self.attributes.get(key) or 0) / 100.0

    def wert_oder(self, key, standard=0.0):
        """Eigenschaft als 0-1, mit ausdruecklichem Ersatz bei Unbekannt.

        Nur dort benutzen, wo der Ersatz wirklich gemeint ist - etwa in
        einer Summe, die ohne den Term genauso weiterlaeuft. Nie dort,
        wo aus dem Ersatz eine Aussage ueber den Brawler wuerde.
        """
        wert = self.wert(key)
        return standard if wert is None else wert

    def bekannte_werte(self):
        """{key: 0-1} nur fuer das, was wirklich eingetragen ist."""
        return {k: self.wert(k) for k in (self.attributes or {})
                if k in attr.ATTRIBUT_KEYS}

    def vektor(self):
        """Vollstaendiges Eigenschaftsprofil als {key: 0-1}."""
        return attr.als_vektor(self.attributes)

    def draftwert(self, key):
        """Gepflegter Draft-Wert als 0-1 - oder None.

        **Nicht mehr im aktiven Scoring.** Die sechs Draftwerte stammen
        vollstaendig aus der Demo-Handarbeit vom 2026-09-14 und sagen
        ueber die heutige Meta nichts; Flexibilitaet und Draft-Position
        kommen inzwischen aus gemessenen Ableitungen. Das Feld bleibt
        fuer Historie und Debug lesbar, und `None` macht sichtbar, dass
        nichts dasteht - statt einen erfundenen Durchschnitt zu liefern.
        """
        if not self.draft_values or key not in self.draft_values:
            return None
        return float(self.draft_values.get(key) or 0) / 100.0

    @property
    def alle_rollen(self):
        """Hauptrolle plus Tags, ohne Doppelung."""
        return list(dict.fromkeys(r for r in [self.role] + list(self.tags or []) if r))

    @property
    def rollen_label(self):
        return [attr.ROLLEN_LABEL.get(r, r) for r in self.alle_rollen]

    @property
    def initialen(self):
        """Kuerzel fuer die Platzhalterkachel."""
        teile = self.name.replace("-", " ").replace(".", " ").split()
        if len(teile) >= 2:
            return (teile[0][0] + teile[1][0]).upper()
        return self.name[:2].upper()

    @property
    def is_demo(self):
        return self.source == Datenquelle.DEMO

    def staerken(self, grenze=70, anzahl=4):
        """Die auffaelligsten Eigenschaften - fuer Coach-Texte."""
        gefunden = [
            (k, v) for k, v in (self.attributes or {}).items()
            if v >= grenze and k in attr.EIGENSCHAFT_NACH_KEY
        ]
        gefunden.sort(key=lambda p: -p[1])
        return [attr.EIGENSCHAFT_NACH_KEY[k] for k, _ in gefunden[:anzahl]]

    def schwaechen(self, grenze=25, anzahl=3):
        """Knappe Eigenschaften, die dieser Brawler NICHT liefert."""
        gefunden = [
            attr.EIGENSCHAFT_NACH_KEY[k] for k in attr.KNAPPE_KEYS
            if float((self.attributes or {}).get(k, 0)) <= grenze
        ]
        return gefunden[:anzahl]
