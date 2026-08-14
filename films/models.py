"""Filmbestand aus dem Letterboxd-Export.

Ein Datensatz je Film, egal ob gesehen oder nur vorgemerkt. Der
Letterboxd-URI ist der Schluessel: er steht in jeder Exportdatei und
aendert sich nicht, wenn ein Film umbenannt wird.

Watchlist ist ein eigenes Flag und kein gesehener Film - beides kann
theoretisch gleichzeitig zutreffen (gesehen, aber noch vorgemerkt),
deshalb zwei Felder statt eines Status.

Poster werden hier bewusst nicht fuer alle Filme geholt. Bei 216
Eintraegen waeren das 216 TMDB-Anfragen fuer Bilder, die zum grossen
Teil nie jemand sieht. `poster_pfad` fuellt der Import nur auf
ausdrueckliche Anforderung und nur fuer die Auswahl, die auch angezeigt
wird (siehe import_letterboxd --poster-ab).
"""

import unicodedata

from django.db import models


def normalisiere(titel):
    """Kleinschreibung ohne Akzente - fuer die Suche im Browser.

    "Amélie" -> "amelie", "Interstellar" -> "interstellar". Damit trifft
    die Suche unabhaengig von Gross-/Kleinschreibung und Akzenten.
    NFKD zerlegt Buchstabe und Akzent, das Filtern wirft die Akzente weg.
    """
    text = unicodedata.normalize("NFKD", str(titel or ""))
    ohne_akzente = "".join(z for z in text if not unicodedata.combining(z))
    return " ".join(ohne_akzente.lower().split())


class Film(models.Model):
    # --- Schluessel und Titel -------------------------------------------
    letterboxd_uri = models.URLField(
        unique=True,
        help_text="Kurzlink aus dem Export, z.B. https://boxd.it/pEeQ. Idempotenz-Schluessel.",
    )
    titel = models.CharField(max_length=300)
    titel_normalisiert = models.CharField(
        max_length=300,
        db_index=True,
        help_text="Klein, ohne Akzente. Wird beim Speichern gesetzt.",
    )
    jahr = models.PositiveSmallIntegerField(null=True, blank=True)

    # --- Status ---------------------------------------------------------
    gesehen = models.BooleanField(default=False, db_index=True)
    auf_watchlist = models.BooleanField(default=False, db_index=True)

    # 0.5 bis 5.0 in halben Schritten. Null heisst gesehen, aber nicht
    # bewertet - im Export gibt es davon zwei.
    wertung = models.DecimalField(
        max_digits=2, decimal_places=1, null=True, blank=True, db_index=True
    )

    # --- Daten ----------------------------------------------------------
    # `Date` aus dem Export: wann der Eintrag bei Letterboxd entstand.
    eingetragen_am = models.DateField(null=True, blank=True)
    # `Watched Date` aus diary.csv - nur fuer Filme mit Tagebucheintrag.
    gesehen_am = models.DateField(null=True, blank=True)

    rezension = models.TextField(blank=True)

    # --- TMDB (nur fuer angezeigte Filme gefuellt) ----------------------
    tmdb_id = models.PositiveIntegerField(null=True, blank=True)
    poster_pfad = models.CharField(
        max_length=200,
        blank=True,
        help_text="TMDB poster_path, z.B. /abc123.jpg. Leer = noch nicht geholt.",
    )

    aktualisiert_am = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Film"
        verbose_name_plural = "Filme"
        ordering = ["-wertung", "titel"]
        indexes = [
            models.Index(fields=["gesehen", "-wertung"]),
        ]

    def __str__(self):
        return f"{self.titel} ({self.jahr})" if self.jahr else self.titel

    def save(self, *args, **kwargs):
        # Zentral statt im Import: so stimmt das Feld auch, wenn ein
        # Datensatz im Admin oder in der Shell geaendert wird.
        self.titel_normalisiert = normalisiere(self.titel)
        super().save(*args, **kwargs)

    @property
    def poster_url(self):
        """Volle TMDB-Bild-URL oder None."""
        if not self.poster_pfad:
            return None
        return f"https://image.tmdb.org/t/p/w342{self.poster_pfad}"
