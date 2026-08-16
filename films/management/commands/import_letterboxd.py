"""Liest den Letterboxd-CSV-Export in die Datenbank.

    python manage.py import_letterboxd
    python manage.py import_letterboxd --pfad /wo/anders
    python manage.py import_letterboxd --poster-ab 4.0

Idempotent: Schluessel ist die Letterboxd-URI, ein zweiter Lauf legt
nichts doppelt an. Die Dateien werden in einer festen Reihenfolge
gelesen, weil sie sich ergaenzen:

    watched.csv    Grundbestand, setzt `gesehen`
    ratings.csv    ergaenzt die Wertung
    diary.csv      ergaenzt das Sehdatum
    reviews.csv    ergaenzt Rezensionstext und Rezensionsdatum
    watchlist.csv  eigene Eintraege, setzt `auf_watchlist`

Watchlist-Filme sind ausdruecklich keine gesehenen Filme - sie bekommen
nur das Flag. comments.csv und profile.csv werden nicht gebraucht.

Poster holt der Import nur mit --poster-ab und nur fuer Filme ab dieser
Wertung. Fuer alle 216 waeren es 216 TMDB-Anfragen fuer Bilder, die zum
grossen Teil nirgends auftauchen.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from films import statistik, suchindex
from films.models import Film, normalisiere

STANDARD_PFAD = Path(settings.BASE_DIR) / "data" / "letterboxd"

# Spalten, die in jeder Datei stehen.
SPALTE_URI = "Letterboxd URI"
SPALTE_NAME = "Name"
SPALTE_JAHR = "Year"
SPALTE_DATUM = "Date"

TMDB_SUCHE = "https://api.themoviedb.org/3/search/movie"
TMDB_TIMEOUT = 5
USER_AGENT = "alex-volkmann-portfolio/1.0 (+https://alex.volkmann.com)"


def _datum(wert):
    """'2026-07-14' -> date. Leer oder unlesbar -> None."""
    if not wert:
        return None
    try:
        return datetime.strptime(wert.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _jahr(wert):
    try:
        return int(str(wert).strip())
    except (TypeError, ValueError):
        return None


def _wertung(wert):
    try:
        return float(str(wert).strip())
    except (TypeError, ValueError):
        return None


class Command(BaseCommand):
    help = "Importiert den Letterboxd-CSV-Export in die Filmtabelle."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pfad",
            default=str(STANDARD_PFAD),
            help=f"Ordner mit den CSV-Dateien (Standard: {STANDARD_PFAD})",
        )
        parser.add_argument(
            "--poster-ab",
            type=float,
            default=None,
            metavar="WERTUNG",
            help="Poster von TMDB nur fuer Filme ab dieser Wertung holen, z.B. 4.0.",
        )

    # -- Einlesen --------------------------------------------------------

    def _lies(self, ordner, name, pflicht=True):
        pfad = ordner / f"{name}.csv"
        if not pfad.exists():
            if pflicht:
                raise CommandError(f"{pfad} fehlt.")
            self.stdout.write(f"  {name}.csv nicht vorhanden, uebersprungen")
            return []
        with pfad.open(encoding="utf-8-sig", newline="") as datei:
            leser = csv.DictReader(datei)
            if SPALTE_URI not in (leser.fieldnames or []):
                raise CommandError(
                    f"{pfad.name}: Spalte {SPALTE_URI!r} fehlt. "
                    f"Gefunden: {leser.fieldnames}"
                )
            return list(leser)

    def handle(self, *args, **optionen):
        ordner = Path(optionen["pfad"])
        if not ordner.is_dir():
            raise CommandError(f"{ordner} ist kein Ordner.")

        self.stdout.write(f"Lese aus {ordner}")

        watched = self._lies(ordner, "watched")
        ratings = self._lies(ordner, "ratings")
        diary = self._lies(ordner, "diary", pflicht=False)
        reviews = self._lies(ordner, "reviews", pflicht=False)
        watchlist = self._lies(ordner, "watchlist", pflicht=False)

        with transaction.atomic():
            neu, aktualisiert = self._schreibe(
                watched, ratings, diary, reviews, watchlist
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{neu} neu, {aktualisiert} aktualisiert, "
                f"{Film.objects.count()} Filme gesamt"
            )
        )
        self.stdout.write(
            f"  gesehen:   {Film.objects.filter(gesehen=True).count()}\n"
            f"  bewertet:  {Film.objects.filter(wertung__isnull=False).count()}\n"
            f"  watchlist: {Film.objects.filter(auf_watchlist=True).count()}"
        )

        grenze = optionen["poster_ab"]
        if grenze is not None:
            self._hole_poster(grenze)

        # Der Suchindex haengt an einem Cache - ohne das hier lieferte
        # der Endpunkt nach dem Import bis zu eine Stunde lang den alten
        # Bestand.
        suchindex.leere_cache()
        statistik._leere_cache()
        self.stdout.write("Cache fuer Suchindex und Statistik verworfen.")

    # -- Schreiben -------------------------------------------------------

    def _schreibe(self, watched, ratings, diary, reviews, watchlist):
        """Alle Dateien in einen Datensatz je URI zusammenfuehren."""
        # Erst im Speicher zusammenbauen, dann einmal je Film schreiben -
        # sonst faehrt derselbe Datensatz bis zu fuenfmal in die Datenbank.
        bestand = {}
        self.ohne_zuordnung = []

        def eintrag(zeile):
            uri = (zeile.get(SPALTE_URI) or "").strip()
            if not uri:
                return None
            return bestand.setdefault(
                uri,
                {
                    "titel": (zeile.get(SPALTE_NAME) or "").strip(),
                    "jahr": _jahr(zeile.get(SPALTE_JAHR)),
                    "gesehen": False,
                    "auf_watchlist": False,
                    "wertung": None,
                    "eingetragen_am": _datum(zeile.get(SPALTE_DATUM)),
                    "gesehen_am": None,
                    "rezension": "",
                    "rezension_am": None,
                },
            )

        for zeile in watched:
            d = eintrag(zeile)
            if d is not None:
                d["gesehen"] = True

        for zeile in ratings:
            d = eintrag(zeile)
            if d is not None:
                d["wertung"] = _wertung(zeile.get("Rating"))
                # Eine Wertung ohne Eintrag in watched.csv gilt trotzdem
                # als gesehen - bewerten kann man nur, was man kennt.
                d["gesehen"] = True

        # diary.csv und reviews.csv fuehren in der Spalte "Letterboxd URI"
        # die URI des Tagebuch- bzw. Rezensionseintrags, nicht die des
        # Films - null Ueberschneidung mit watched.csv. Ueber die URI
        # angelegt, entstuenden Doppelgaenger. Zugeordnet wird deshalb
        # ueber normalisierten Titel und Jahr.
        nach_titel = {
            (normalisiere(d["titel"]), d["jahr"]): d for d in bestand.values()
        }

        def finde(zeile):
            schluessel = (
                normalisiere(zeile.get(SPALTE_NAME)),
                _jahr(zeile.get(SPALTE_JAHR)),
            )
            treffer = nach_titel.get(schluessel)
            if treffer is None:
                self.ohne_zuordnung.append(
                    f"{zeile.get(SPALTE_NAME)} ({zeile.get(SPALTE_JAHR)})"
                )
            return treffer

        for zeile in diary:
            d = finde(zeile)
            if d is not None:
                d["gesehen"] = True
                d["gesehen_am"] = _datum(zeile.get("Watched Date"))
                if d["wertung"] is None:
                    d["wertung"] = _wertung(zeile.get("Rating"))

        for zeile in reviews:
            # Zeilen ohne Text vor der Zuordnung aussortieren: sie
            # ueberschrieben sonst eine vorhandene Rezension mit Leere und
            # landeten, wenn der Film fehlt, in `ohne_zuordnung` - eine
            # Warnung ueber eine Rezension, die es gar nicht gibt.
            text = (zeile.get("Review") or "").strip()
            if not text:
                continue

            d = finde(zeile)
            if d is not None:
                d["gesehen"] = True
                d["rezension"] = text
                # `Date` ist hier das Datum der Rezension, nicht das des
                # Films - siehe Film.rezension_am.
                d["rezension_am"] = _datum(zeile.get(SPALTE_DATUM))
                if not d["gesehen_am"]:
                    d["gesehen_am"] = _datum(zeile.get("Watched Date"))

        for zeile in watchlist:
            d = eintrag(zeile)
            if d is not None:
                # Ausdruecklich kein `gesehen = True`.
                d["auf_watchlist"] = True

        if self.ohne_zuordnung:
            self.stdout.write(self.style.WARNING(
                f"  {len(self.ohne_zuordnung)} Tagebuch-/Rezensionseintraege ohne "
                f"passenden Film: {', '.join(self.ohne_zuordnung)}"
            ))

        neu = aktualisiert = 0
        for uri, werte in bestand.items():
            film, erzeugt = Film.objects.update_or_create(
                letterboxd_uri=uri, defaults=werte
            )
            neu += erzeugt
            aktualisiert += not erzeugt

        return neu, aktualisiert

    # -- Poster ----------------------------------------------------------

    def _hole_poster(self, grenze):
        api_key = getattr(settings, "TMDB_API_KEY", "")
        if not api_key:
            self.stdout.write(
                self.style.WARNING("TMDB_API_KEY fehlt - keine Poster geholt.")
            )
            return

        offen = Film.objects.filter(
            wertung__gte=grenze, gesehen=True, poster_pfad=""
        ).order_by("-wertung", "titel")

        self.stdout.write(f"\nPoster ab {grenze}: {offen.count()} offen")

        treffer = fehlschlaege = 0
        for film in offen:
            daten = self._suche_tmdb(film, api_key)
            if daten is None:
                fehlschlaege += 1
                self.stdout.write(f"  --  {film.titel} ({film.jahr})")
                continue
            film.tmdb_id = daten["id"]
            film.poster_pfad = daten.get("poster_path") or ""
            film.save(update_fields=["tmdb_id", "poster_pfad", "titel_normalisiert",
                                     "aktualisiert_am"])
            treffer += 1
            self.stdout.write(f"  ok  {film.titel} ({film.jahr})")

        self.stdout.write(
            self.style.SUCCESS(f"{treffer} Poster geholt, {fehlschlaege} ohne Treffer")
        )

    def _suche_tmdb(self, film, api_key):
        """TMDB kennt die Letterboxd-URI nicht - gesucht wird ueber Titel und Jahr."""
        frage = {"api_key": api_key, "query": film.titel}
        if film.jahr:
            frage["year"] = film.jahr

        anfrage = Request(
            f"{TMDB_SUCHE}?{urlencode(frage)}",
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        try:
            with urlopen(anfrage, timeout=TMDB_TIMEOUT) as antwort:
                ergebnisse = json.loads(antwort.read().decode("utf-8")).get("results")
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            return None

        return ergebnisse[0] if ergebnisse else None
