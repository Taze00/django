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
        help_text="Schlüssel aus drafter.attributes, Werte 0-100. Fehlend = 0.",
    )
    draft_values = models.JSONField(
        default=dict, blank=True,
        help_text="blind_pick_value, last_pick_value, ... Werte 0-100. Fehlend = 50.",
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

        Ohne Profil liefert `wert()` fuer alles 0 - das heisst dann
        "unbekannt", nicht "kann nichts". Jede Rechnung, die Eigenschaften
        liest, muss vorher hier fragen, statt die 0 zu verrechnen.
        """
        return bool(self.attributes)

    @property
    def hat_draftwerte(self):
        """Gepflegte Draft-Werte? Ohne sie liefert `draftwert()` 0.5 -
        ein Durchschnitt, der nicht gemessen, sondern angenommen waere."""
        return bool(self.draft_values)

    # --- Zugriff --------------------------------------------------------
    def wert(self, key):
        """Eigenschaft als 0-1. Unbekannt oder fehlend = 0."""
        return float(self.attributes.get(key, 0)) / 100.0

    def vektor(self):
        """Vollstaendiges Eigenschaftsprofil als {key: 0-1}."""
        return attr.als_vektor(self.attributes)

    def draftwert(self, key):
        """Draft-Wert als 0-1. Fehlend = 0.5 (durchschnittlich)."""
        roh = self.draft_values.get(key, attr.DRAFTWERT_STANDARD)
        return float(roh) / 100.0

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
