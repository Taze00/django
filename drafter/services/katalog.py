# -*- coding: utf-8 -*-
"""Katalog aus echten API-Antworten ergaenzen - Identitaeten, keine Eigenschaften.

Was hier passiert, und was bewusst nicht:

- **IDs eintragen.** Brawler bekommen die ID aus /brawlers, Modi die
  `event.modeId`, Maps die `event.id` aus Battlelogs. Ab dann ordnet der
  Import ueber IDs zu, nicht mehr ueber Namen.
- **Fehlende Eintraege anlegen - inaktiv und ohne Profil.** Ein neuer
  Brawler bekommt Name und ID, aber keine Rolle, keine Eigenschaften und
  keine Draft-Werte. Fehlende Eigenschaften zaehlen im Modell als 0 ("kann
  das nicht") - ein Profil voller Nullen waere also eine erfundene Aussage.
  `is_active=False` haelt solche Eintraege aus Engine und Oberflaeche
  heraus; Import und Aggregation zaehlen sie trotzdem.
- **Nie ueberschreiben.** Gepflegte Eintraege behalten Namen, Eigenschaften
  und Anforderungen. Gesetzt wird nur eine LEERE `external_id`. Traegt ein
  Eintrag bereits eine ANDERE ID, ist das ein Konflikt - gemeldet, nicht
  aufgeloest.

`event.id` bezeichnet Map UND Modus zusammen: in /events/rotation hatte
"Doom Shroom" drei IDs, eine je Showdown-Variante. Das passt zum Modell -
eine BrawlMap gehoert zu genau einem Modus.

**Der Modusname ist nicht eindeutig, die `modeId` schon.** Gemessen am
2026-09-16 ueber 298 Partien: "brawlBall" kam mit den IDs 5 (3v3), 32
(5v5) und 45 (3v3, in /events/rotation "airHockey") vor, "wipeout" mit 25
(3v3) und 31 (5v5). Umgekehrt traegt dieselbe ID in verschiedenen
Endpoints verschiedene Namen. Deshalb bekommt jede neue ID einen EIGENEN
Katalogeintrag; ist der Name schon vergeben, steht die ID im Namen.

Warum Maps schon bei der ERSTEN Sichtung angelegt werden: der
Fingerabdruck einer Partie haengt daran, ob der Katalog die Map kennt.
Kaeme sie erst nach mehreren Sichtungen dazu, bekaeme dieselbe Partie in
einem spaeter abgerufenen Battlelog einen anderen Fingerabdruck - und
wuerde doppelt gezaehlt. Jede weitere Sichtung wird stattdessen gegen den
Katalog geprueft (MatchImporter._widersprueche_pruefen).
"""

import re
from dataclasses import dataclass, field

from django.db import IntegrityError, transaction

from drafter.models import Brawler, BrawlMap, Datenquelle, GameMode
from drafter.services.ingest.fingerprint import katalog_schluessel

HINWEIS_OHNE_PROFIL = (
    "Aus der offiziellen API übernommen. Kein gepflegtes Profil – deshalb inaktiv: "
    "die Engine rechnet nicht damit, Import und Aggregation zählen es."
)

# Neue Modi ans Ende der Liste - sie sollen gepflegte nicht verdraengen.
ORDNUNG_NEUER_MODI = 100


def _api_id(wert):
    """IDs der API sind Ganzzahlen; gespeichert wird Text."""
    return str(wert) if isinstance(wert, int) and not isinstance(wert, bool) else None


def modus_anzeigename(roh):
    """"hotZone" -> "Hot Zone". Nur Worttrennung - keine Uebersetzung, kein Raten."""
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(roh or "")).strip()
    return text[:1].upper() + text[1:]


def freier_slug(modell, basis, zusatz=""):
    """Ein noch freier Slug: basis, basis-zusatz, basis-2, ..."""
    basis = basis or "ohne-name"
    if not modell.objects.filter(slug=basis).exists():
        return basis
    if zusatz and not modell.objects.filter(slug=f"{basis}-{zusatz}").exists():
        return f"{basis}-{zusatz}"
    nummer = 2
    while modell.objects.filter(slug=f"{basis}-{nummer}").exists():
        nummer += 1
    return f"{basis}-{nummer}"


# =========================================================================
# Brawler aus /brawlers
# =========================================================================

@dataclass
class BrawlerAbgleich:
    bestaetigt: int = 0
    verknuepft: list = field(default_factory=list)
    neu: list = field(default_factory=list)
    konflikte: list = field(default_factory=list)
    uebersprungen: int = 0

    def zeilen(self):
        zeilen = [
            f"Brawler-Katalog: {self.bestaetigt} per ID bestätigt, "
            f"{len(self.verknuepft)} per Name verknüpft, {len(self.neu)} neu "
            f"(inaktiv, ohne Profil), {len(self.konflikte)} Konflikte, "
            f"{self.uebersprungen} ohne ID oder Name übersprungen"
        ]
        if self.verknuepft:
            zeilen.append("  verknüpft: " + ", ".join(self.verknuepft))
        if self.neu:
            zeilen.append("  neu: " + ", ".join(self.neu))
        return zeilen + [f"  ! {k}" for k in self.konflikte]


def brawler_abgleichen(items):
    """Eintraege von /brawlers mit dem Katalog abgleichen.

    Reihenfolge je Eintrag: ID bekannt -> bestaetigt. Sonst gleicher
    Katalogschluessel ohne ID -> ID eintragen. Sonst neu anlegen. Gelesen
    werden nur `id` und `name`; Gadgets, Star Powers und Gears bleiben in
    der gespeicherten Rohantwort, bis jemand sie braucht.
    """
    ergebnis = BrawlerAbgleich()
    nach_id = {b.external_id: b for b in Brawler.objects.exclude(external_id=None)}
    nach_slug = {b.slug: b for b in Brawler.objects.all()}

    for eintrag in items:
        if not isinstance(eintrag, dict):
            ergebnis.uebersprungen += 1
            continue
        ext = _api_id(eintrag.get("id"))
        name = eintrag.get("name") if isinstance(eintrag.get("name"), str) else ""
        if ext is None or not name.strip():
            ergebnis.uebersprungen += 1
            continue
        schluessel = katalog_schluessel(name)

        vorhanden = nach_id.get(ext)
        if vorhanden is not None:
            if katalog_schluessel(vorhanden.name) == schluessel:
                ergebnis.bestaetigt += 1
            else:
                ergebnis.konflikte.append(
                    f"ID {ext}: Katalog '{vorhanden.name}', API '{name}' - Name nicht geändert"
                )
            continue

        per_name = nach_slug.get(schluessel)
        if per_name is not None:
            if per_name.external_id:
                ergebnis.konflikte.append(
                    f"'{name}' (ID {ext}): Katalogeintrag '{per_name.name}' "
                    f"trägt schon ID {per_name.external_id}"
                )
                continue
            per_name.external_id = ext
            per_name.save(update_fields=["external_id", "updated_at"])
            nach_id[ext] = per_name
            ergebnis.verknuepft.append(f"{per_name.name} → {ext}")
            continue

        try:
            with transaction.atomic():
                neu = Brawler.objects.create(
                    name=name[:60], slug=freier_slug(Brawler, schluessel), external_id=ext,
                    role="", tags=[], attributes={}, draft_values={},
                    source=Datenquelle.API, is_active=False, notes=HINWEIS_OHNE_PROFIL,
                )
        except IntegrityError:
            ergebnis.konflikte.append(f"'{name}' (ID {ext}): Name schon vergeben - nicht angelegt")
            continue
        nach_id[ext] = neu
        nach_slug[neu.slug] = neu
        ergebnis.neu.append(name)
    return ergebnis


# =========================================================================
# Modi und Maps aus Partien
# =========================================================================

class KatalogErgaenzer:
    """Legt Modi und Maps an, die eine Partie mit Quellen-ID nennt.

    Arbeitet auf denselben Woerterbuechern wie der Importer - was hier
    entsteht, findet dessen Zuordnung sofort.
    """

    def __init__(self, modi, modi_ext, maps, maps_ext):
        self._modi = modi            # slug -> GameMode
        self._modi_ext = modi_ext    # external_id -> GameMode
        self._maps = maps            # slug -> BrawlMap
        self._maps_ext = maps_ext    # external_id -> BrawlMap

    def ergaenze(self, record, bericht):
        modus = self._modus(record, bericht)
        if modus is not None:
            self._karte(record, modus, bericht)

    def _modus(self, record, bericht):
        ext = record.external_mode_id
        if not ext or not record.mode:
            return None
        if ext in self._modi_ext:
            return self._modi_ext[ext]

        schluessel = katalog_schluessel(record.mode)
        modus = self._modi.get(schluessel)
        if modus is not None and modus.external_id:
            # Gleicher Name, andere ID: eine andere Spielart (3v3 gegen 5v5)
            # oder ein anderer Endpoint-Name derselben ID. Die ID entscheidet,
            # also bekommt sie einen eigenen Eintrag - mit ID im Namen, weil
            # der Name allein nicht mehr unterscheidet.
            modus = GameMode.objects.create(
                name=f"{modus_anzeigename(record.mode)} ({ext})"[:60],
                slug=freier_slug(GameMode, schluessel, ext), external_id=ext,
                description=HINWEIS_OHNE_PROFIL[:200], base_requirements={},
                is_active=False, order=ORDNUNG_NEUER_MODI,
            )
            self._modi[modus.slug] = modus
            self._modi_ext[ext] = modus
            bericht.katalog_neu.append(
                f"Modus {modus.name} - gleicher Name wie '{record.mode}', andere ID"
            )
            return modus
        if modus is not None:
            modus.external_id = ext
            modus.save(update_fields=["external_id", "updated_at"])
            self._modi_ext[ext] = modus
            bericht.katalog_verknuepft.append(f"Modus {modus.name} → {ext}")
            return modus

        modus = GameMode.objects.create(
            name=modus_anzeigename(record.mode)[:60], slug=freier_slug(GameMode, schluessel),
            external_id=ext, description=HINWEIS_OHNE_PROFIL[:200], base_requirements={},
            is_active=False, order=ORDNUNG_NEUER_MODI,
        )
        self._modi[modus.slug] = modus
        self._modi_ext[ext] = modus
        bericht.katalog_neu.append(f"Modus {modus.name} ({ext})")
        return modus

    def _karte(self, record, modus, bericht):
        ext = record.external_map_id
        if not ext or not record.map or ext in self._maps_ext:
            return

        schluessel = katalog_schluessel(record.map)
        karte = next(
            (k for k in self._maps.values()
             if k.game_mode_id == modus.id and katalog_schluessel(k.name) == schluessel),
            None,
        )
        if karte is not None:
            if karte.external_id:
                bericht.id_widersprueche.append(
                    f"Map '{record.map}' (ID {ext}): Katalog '{karte.name}' "
                    f"trägt schon ID {karte.external_id}"
                )
                return
            karte.external_id = ext
            karte.save(update_fields=["external_id", "updated_at"])
            self._maps_ext[ext] = karte
            bericht.katalog_verknuepft.append(f"Map {karte.name} ({modus.name}) → {ext}")
            return

        karte = BrawlMap.objects.create(
            name=record.map[:80], slug=freier_slug(BrawlMap, schluessel, modus.slug),
            external_id=ext, game_mode=modus, requirements={}, traits={},
            source=Datenquelle.API, is_active=False, notes=HINWEIS_OHNE_PROFIL,
        )
        self._maps[karte.slug] = karte
        self._maps_ext[ext] = karte
        bericht.katalog_neu.append(f"Map {karte.name} ({modus.name}, {ext})")
