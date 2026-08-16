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


# Merker fuer "bei TMDB gesucht, nichts gefunden". Steht hier und nicht
# in films/poster.py, weil beide ihn brauchen: poster.py schreibt ihn,
# Film.poster_url muss ihn erkennen. poster.py importiert models - die
# umgekehrte Richtung waere ein Zirkelschluss.
KEIN_TREFFER = "-"


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
        """Volle TMDB-Bild-URL oder None.

        KEIN_TREFFER muss hier mit abgefangen werden. Der Bindestrich
        ist ein Merker, kein Pfad - ohne die Pruefung entstand daraus
        ".../w342-", eine gueltig aussehende URL, die 404 liefert. Das
        Template haelt sie fuer ein Poster, zeigt ein <img> und damit
        ein kaputtes Bild samt Alt-Text, statt auf den
        Anfangsbuchstaben zurueckzufallen.

        films/poster.py kannte den Merker, diese Property nicht - er
        wurde an einer Stelle beachtet und an der anderen nicht.
        Deshalb steht er jetzt hier, wo beide ihn sehen.
        """
        if not self.poster_pfad or self.poster_pfad == KEIN_TREFFER:
            return None
        return f"https://image.tmdb.org/t/p/w342{self.poster_pfad}"

    @property
    def meine_wertung(self):
        """Alias fuer die Kachel-Templates.

        includes/kachel-poster.html bedient auch die kuratierten Listen
        aus films/data/, die dieses Feld so nennen. Mit dem Alias laesst
        sich ein Film-Objekt ohne Umbau derselben Kachel uebergeben.
        """
        return self.wertung
