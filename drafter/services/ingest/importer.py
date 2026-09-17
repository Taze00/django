# -*- coding: utf-8 -*-
"""Lieferungen eines MatchProviders in die Rohdaten-Tabellen schreiben.

Drei Garantien, jede mit eigenem Mechanismus:

1. **Idempotent je Lieferung.** Dieselbe Datei zweimal einzuspielen,
   aendert nichts - erkannt am Inhaltshash der Rohdaten.
2. **Dedupliziert je Partie.** Dieselbe Partie in zwei verschiedenen
   Lieferungen (zwei Battlelogs) wird einmal gespeichert und mit beiden
   Lieferungen verknuepft - erkannt am Fingerabdruck.
3. **Nichts wird geraten.** Unbekannte Brawler und Maps werden mit ihrem
   gelieferten Namen gespeichert und im Bericht genannt, nicht auf etwas
   Aehnliches abgebildet. Widerspruechliche Ergebnisse werden als
   Konflikt markiert, nicht mehrheitlich entschieden.

Der Importer rechnet keine Statistiken. Das ist Sache der Aggregation -
eine Trennung, die es erlaubt, nach einer Korrektur der Gewichtung alles
neu zu aggregieren, ohne neu zu importieren.
"""

import bisect
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field

from django.db import DatabaseError, transaction

from drafter.models import Brawler, BrawlMap, GameMode, Patch
from drafter.models.matches import Match, MatchBan, MatchPlayer, RawPayload
from drafter.services.katalog import KatalogErgaenzer
from drafter.services.ingest.fingerprint import (
    eindeutiger_fingerprint, ist_spiegel, kandidaten, kanonisiere, katalog_schluessel,
    rekonstruierter_fingerprint, standard_identitaet, standard_ort,
)


@dataclass
class ImportBericht:
    lieferungen: int = 0
    bereits_importiert: int = 0
    nicht_unterstuetzt: int = 0
    fehlerhaft: int = 0
    matches_gelesen: int = 0
    ungueltig: int = 0
    uebersprungen: int = 0
    neu: int = 0
    duplikate: int = 0
    konflikte: int = 0
    # Wie Brawler zugeordnet wurden. Solange "per Name" dominiert, haengt
    # die Zuordnung an Schreibweisen - ein Grund, externe IDs zu pflegen.
    zuordnung_per_id: int = 0
    zuordnung_per_name: int = 0
    unbekannte_brawler: set = field(default_factory=set)
    unbekannte_maps: set = field(default_factory=set)
    # Nach Partietyp der Quelle. Trophaeen- und Ranked-Partien sollen schon
    # im Importbericht getrennt sichtbar sein, nicht erst in der Aggregation.
    neu_nach_typ: Counter = field(default_factory=Counter)
    duplikate_nach_typ: Counter = field(default_factory=Counter)
    # Nur mit katalog_ergaenzen: angelegte bzw. per Name verknuepfte Eintraege.
    katalog_neu: list = field(default_factory=list)
    katalog_verknuepft: list = field(default_factory=list)
    # Bekannte Quellen-ID, die einen anderen Namen traegt als der Katalog.
    id_widersprueche: list = field(default_factory=list)
    meldungen: list = field(default_factory=list)

    def zeilen(self):
        zeilen = [
            f"Lieferungen:          {self.lieferungen}"
            f" (bereits importiert {self.bereits_importiert},"
            f" nicht auswertbar {self.nicht_unterstuetzt}, fehlerhaft {self.fehlerhaft})",
            f"Partien gelesen:      {self.matches_gelesen} (ungültig verworfen {self.ungueltig},"
            f" übersprungen - keine Draft-Partie {self.uebersprungen})",
            f"  neu gespeichert:    {self.neu}",
            f"  Duplikate:          {self.duplikate}",
            f"  Konflikte:          {self.konflikte}",
            f"Brawler zugeordnet:   per ID {self.zuordnung_per_id},"
            f" per Name {self.zuordnung_per_name}",
        ]
        if self.unbekannte_brawler:
            zeilen.append(f"Unbekannte Brawler:   {', '.join(sorted(self.unbekannte_brawler))}")
        if self.unbekannte_maps:
            zeilen.append(f"Unbekannte Maps:      {', '.join(sorted(self.unbekannte_maps))}")
        if self.neu_nach_typ or self.duplikate_nach_typ:
            typen = sorted(set(self.neu_nach_typ) | set(self.duplikate_nach_typ))
            zeilen.append("Nach Partietyp:       " + ", ".join(
                f"{typ}: neu {self.neu_nach_typ[typ]}, Dublette {self.duplikate_nach_typ[typ]}"
                for typ in typen
            ))
        if self.katalog_neu:
            zeilen.append(f"Katalog neu (inaktiv): {', '.join(self.katalog_neu)}")
        if self.katalog_verknuepft:
            zeilen.append(f"Katalog verknüpft:    {', '.join(self.katalog_verknuepft)}")
        if self.id_widersprueche:
            zeilen.append(f"ID-Widersprüche:      {len(self.id_widersprueche)}")
            zeilen += [f"  ! {w}" for w in self.id_widersprueche[:10]]
        return zeilen + [f"  - {m}" for m in self.meldungen]


def inhalts_hash(rohdaten):
    """Stabiler Hash ueber den INHALT, unabhaengig von Schluesselreihenfolge."""
    text = json.dumps(rohdaten, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class MatchImporter:
    def __init__(self, provider, trockenlauf=False, katalog_ergaenzen=False):
        self.provider = provider
        self.trockenlauf = trockenlauf
        # Kataloge einmal laden - eine Abfrage je Partie waere bei
        # grossen Importen der teuerste Teil.
        brawler = list(Brawler.objects.all())
        modi = list(GameMode.objects.all())
        karten = list(BrawlMap.objects.select_related("game_mode"))
        self._brawler = {b.slug: b for b in brawler}
        self._modi = {m.slug: m for m in modi}
        self._maps = {k.slug: k for k in karten}
        # Externe IDs zuerst - Namen sind nur der Rueckfall.
        self._brawler_ext = {b.external_id: b for b in brawler if b.external_id}
        self._modi_ext = {m.external_id: m for m in modi if m.external_id}
        self._maps_ext = {k.external_id: k for k in karten if k.external_id}
        # Mit `katalog_ergaenzen` legt der Ergaenzer fehlende Modi und Maps
        # an, sobald eine Partie ihre Quellen-ID nennt - auf denselben
        # Woerterbuechern, sodass die Zuordnung sie sofort findet.
        self._ergaenzer = (
            KatalogErgaenzer(self._modi, self._modi_ext, self._maps, self._maps_ext)
            if katalog_ergaenzen else None
        )
        self._patches = list(Patch.objects.order_by("released_on"))
        self._patch_daten = [p.released_on for p in self._patches]

    # --- Ablauf ---------------------------------------------------------
    def ausfuehren(self):
        """Alle Lieferungen importieren.

        **Ohne umspannende Transaktion** (ausser im Trockenlauf): jede
        Lieferung und jede Partie sichert sich selbst. Frueher lag alles in
        EINER Transaktion - ein einziger Fehler nahm damit auch die schon
        gespeicherte Rohantwort zurueck, und die Antwort war ohne neuen
        Abruf nicht wiederherstellbar (2026-09-17: ein Battlelog, 17 Partien).
        """
        bericht = ImportBericht()
        if self.trockenlauf:
            with transaction.atomic():
                for lieferung in self.provider.lieferungen():
                    self._lieferung(lieferung, bericht)
                transaction.set_rollback(True)
                bericht.meldungen.append("Trockenlauf - nichts wurde gespeichert")
            return bericht
        for lieferung in self.provider.lieferungen():
            self._lieferung(lieferung, bericht)
        return bericht

    def _lieferung(self, lieferung, bericht):
        bericht.lieferungen += 1

        # Nicht lesbare Dateien werden nicht gespeichert: es gibt keinen
        # Inhalt, der sich spaeter neu auswerten liesse.
        if lieferung.rohdaten is None:
            bericht.fehlerhaft += 1
            bericht.meldungen.append(f"{lieferung.referenz}: {lieferung.meldung}")
            return

        hash_wert = inhalts_hash(lieferung.rohdaten)
        # Schon gespeicherte Rohantwort: die Partien werden trotzdem noch
        # einmal durchgegangen. Nur so laesst sich eine Antwort, deren
        # Import beim ersten Mal teilweise scheiterte, spaeter nachholen -
        # ohne neuen Abruf. Neu entsteht dabei nichts: die Deduplizierung
        # erkennt jede vorhandene Partie am Fingerprint.
        vorhandene = RawPayload.objects.filter(content_hash=hash_wert).first()
        if vorhandene is not None:
            bericht.bereits_importiert += 1
            bericht.meldungen.append(
                f"{lieferung.referenz}: Rohantwort lag schon vor - Partien erneut geprüft"
            )

        status = {
            "ausgewertet": RawPayload.ParseStatus.PARSED,
            "nicht_unterstuetzt": RawPayload.ParseStatus.UNSUPPORTED,
        }.get(lieferung.status, RawPayload.ParseStatus.ERROR)

        # 1. Rohantwort ZUERST und in eigener Transaktion. Sie ist das
        #    Original; alles andere laesst sich daraus neu rechnen. Schlaegt
        #    der Import danach fehl, bleibt sie erhalten und kann mit
        #    `import_brawl_fixture` erneut eingespielt werden.
        try:
            with transaction.atomic():
                payload = vorhandene or RawPayload.objects.create(
                    source=lieferung.source,
                    format=lieferung.format[:60],
                    reference=lieferung.referenz[:300],
                    content_hash=hash_wert,
                    payload=lieferung.rohdaten,
                    parse_status=status,
                    parse_message=lieferung.meldung,
                )
        except (DatabaseError, ValueError, TypeError) as fehler:
            bericht.fehlerhaft += 1
            bericht.meldungen.append(
                f"{lieferung.referenz}: Rohantwort nicht speicherbar - {fehler}")
            return

        if lieferung.matches is None:
            if status == RawPayload.ParseStatus.UNSUPPORTED:
                bericht.nicht_unterstuetzt += 1
            else:
                bericht.fehlerhaft += 1
            bericht.meldungen.append(f"{lieferung.referenz}: {lieferung.meldung}")
            return

        # 2. Jede Partie einzeln absichern. Eine kaputte Partie (etwa eine
        #    Map, deren Katalogeintrag sich nicht anlegen laesst) kostet
        #    genau diese Partie - nicht den ganzen Battlelog.
        neu_vorher = bericht.neu
        for record in lieferung.matches:
            bericht.matches_gelesen += 1
            try:
                with transaction.atomic():
                    self._match(record, payload, lieferung.source, bericht)
            except (DatabaseError, ValueError, TypeError) as fehler:
                bericht.fehlerhaft += 1
                bericht.meldungen.append(
                    f"{lieferung.referenz}: Partie übersprungen - {self._kennung(record)}: {fehler}"
                )

        bericht.ungueltig += len(lieferung.fehler)
        bericht.uebersprungen += len(lieferung.uebersprungen)
        for fehler in lieferung.fehler[:5]:
            bericht.meldungen.append(f"{lieferung.referenz}: {fehler}")

        try:
            with transaction.atomic():
                payload.match_count = len(lieferung.matches)
                payload.new_match_count = bericht.neu - neu_vorher
                if lieferung.fehler or lieferung.uebersprungen:
                    payload.parse_message = "\n".join(
                        [f"FEHLER: {f}" for f in lieferung.fehler]
                        + [f"ÜBERSPRUNGEN: {u}" for u in lieferung.uebersprungen]
                    )
                payload.save(update_fields=["match_count", "new_match_count", "parse_message"])
        except DatabaseError as fehler:   # Zaehler sind Beiwerk, die Daten stehen
            bericht.meldungen.append(f"{lieferung.referenz}: Zähler nicht gespeichert - {fehler}")

    def _kennung(self, record):
        """Was eine Partie im Fehlertext identifizierbar macht."""
        try:
            modus, karte, ort = self._ort_fuer(record)
            fingerprint = eindeutiger_fingerprint(record, self._identitaet, ort)[:16]
        except Exception:      # noqa: BLE001 - im Fehlerpfad nie noch einmal scheitern
            fingerprint = "?"
        return (
            f"fingerprint {fingerprint}, Partie-ID '{record.external_id or '-'}', "
            f"Map '{record.map or '-'}' (ID {record.external_map_id or '-'}), "
            f"Modus '{record.mode or '-'}' (ID {record.external_mode_id or '-'}), "
            f"Typ '{record.battle_type or '-'}', gespielt {record.played_at}"
        )

    # --- Aufloesung gegen den Katalog -----------------------------------
    def _brawler_fuer(self, name, externe_id):
        """(Brawler, Weg) - Weg ist "id", "name" oder None."""
        if externe_id and externe_id in self._brawler_ext:
            return self._brawler_ext[externe_id], "id"
        brawler = self._brawler.get(katalog_schluessel(name)) if name else None
        return (brawler, "name") if brawler else (None, None)

    def _identitaet(self, spieler):
        """Katalog-Identitaet fuer den Fingerabdruck.

        Loest ID oder Name auf DENSELBEN Katalogeintrag auf - so fuehrt
        eine Sichtung mit IDs und eine mit Namen zum selben Fingerabdruck.
        Nur was der Katalog nicht kennt, behaelt seine gelieferte Form.
        """
        brawler, _ = self._brawler_fuer(spieler.brawler, spieler.external_brawler_id)
        return f"brawler:{brawler.id}" if brawler else standard_identitaet(spieler)

    def _ort_fuer(self, record):
        """(Modus, Map, Identitaet des Orts) - IDs vor Namen."""
        karte = (self._maps_ext.get(record.external_map_id) if record.external_map_id else None) \
            or self._maps.get(katalog_schluessel(record.map))
        modus = (self._modi_ext.get(record.external_mode_id) if record.external_mode_id else None) \
            or self._modi.get(katalog_schluessel(record.mode))
        if karte is not None and modus is None:
            modus = karte.game_mode
        ort = f"karte:{karte.id}" if karte else standard_ort(record)
        return modus, karte, ort

    def _finde(self, record, ort):
        """Bereits gespeicherte Partie - in fester Rangfolge.

        1. Partie-ID der Quelle: exakt, ohne Zeittoleranz.
        2. Fallback: rekonstruierter Fingerabdruck innerhalb der Toleranz.
           Eine Partie mit ANDERER Partie-ID ist dabei nie ein Treffer.
        """
        if record.external_id:
            treffer = Match.objects.filter(external_id=record.external_id).first()
            if treffer is not None:
                return treffer
        for kandidat in Match.objects.filter(
            reconstructed_fingerprint__in=kandidaten(record, self._identitaet, ort)
        ):
            if record.external_id and kandidat.external_id \
                    and kandidat.external_id != record.external_id:
                continue
            return kandidat
        return None

    # --- Eine Partie ----------------------------------------------------
    def _match(self, record, payload, quelle, bericht):
        record, _ = kanonisiere(record, self._identitaet)
        # Bei spiegelgleichen Teams ist nicht feststellbar, welche Seite
        # gewonnen hat - das Ergebnis bleibt dann unbekannt.
        sieger = "" if ist_spiegel(record, self._identitaet) else (record.winner or "")
        if self._ergaenzer is not None:
            self._ergaenzer.ergaenze(record, bericht)
        modus, karte, ort = self._ort_fuer(record)
        self._widersprueche_pruefen(record, modus, karte, bericht)

        vorhanden = self._finde(record, ort)
        if vorhanden is not None:
            self._zusammenfuehren(vorhanden, record, sieger, payload, bericht)
            return

        if karte is None:
            bericht.unbekannte_maps.add(record.map or f"id:{record.external_map_id}")

        match = Match.objects.create(
            fingerprint=eindeutiger_fingerprint(record, self._identitaet, ort),
            reconstructed_fingerprint=rekonstruierter_fingerprint(record, self._identitaet, ort),
            external_id=record.external_id or "",
            source=quelle,
            played_at=record.played_at,
            game_mode=modus,
            brawl_map=karte,
            mode_name=record.mode[:80],
            map_name=record.map[:120],
            patch=self._patch_fuer(record.played_at),
            rank_pool=record.rank_pool,
            is_ranked=record.ranked,
            winner_side=sieger,
            first_pick_side=record.first_pick or "",
            duration_seconds=record.duration_seconds,
            battle_type=(record.battle_type or "")[:40],
            external_mode_id=(record.external_mode_id or "")[:40],
            external_map_id=(record.external_map_id or "")[:40],
        )
        match.payloads.add(payload)

        spieler = []
        for seite in ("a", "b"):
            for s in record.teams[seite]:
                brawler, weg = self._brawler_fuer(s.brawler, s.external_brawler_id)
                gelieferter_name = s.brawler or f"id:{s.external_brawler_id}"
                if weg == "id":
                    bericht.zuordnung_per_id += 1
                    if s.brawler and katalog_schluessel(s.brawler) != katalog_schluessel(brawler.name):
                        bericht.id_widersprueche.append(
                            f"Brawler-ID {s.external_brawler_id}: Katalog '{brawler.name}', "
                            f"geliefert '{s.brawler}'"
                        )
                elif weg == "name":
                    bericht.zuordnung_per_name += 1
                else:
                    bericht.unbekannte_brawler.add(gelieferter_name)
                spieler.append(MatchPlayer(
                    match=match, side=seite, brawler=brawler,
                    brawler_name=gelieferter_name[:80], player_tag=(s.player_tag or "")[:20],
                    pick_order=s.pick_order, build=s.build,
                    power=s.power, trophies=s.trophies,
                    external_brawler_id=(s.external_brawler_id or "")[:40],
                ))
        MatchPlayer.objects.bulk_create(spieler)

        bans = []
        for ban in record.bans:
            brawler, _ = self._brawler_fuer(ban.get("brawler"), ban.get("external_brawler_id"))
            bans.append(MatchBan(
                match=match, side=ban.get("side") or "", brawler=brawler,
                brawler_name=(ban.get("brawler") or f"id:{ban.get('external_brawler_id')}")[:80],
                order=ban.get("order"),
            ))
        MatchBan.objects.bulk_create(bans)
        bericht.neu += 1
        bericht.neu_nach_typ[record.battle_type or "-"] += 1

    def _zusammenfuehren(self, vorhanden, record, sieger, payload, bericht):
        """Eine erneute Sichtung einer bekannten Partie."""
        bericht.duplikate += 1
        bericht.duplikate_nach_typ[record.battle_type or "-"] += 1
        vorhanden.payloads.add(payload)

        felder = []
        if sieger and vorhanden.winner_side and sieger != vorhanden.winner_side:
            if not vorhanden.has_conflict:
                vorhanden.has_conflict = True
                vorhanden.conflict_note = (
                    f"Widersprüchliches Ergebnis: gespeichert '{vorhanden.winner_side}', "
                    f"in {payload.reference or 'weiterer Lieferung'} '{sieger}'"
                )[:300]
                felder += ["has_conflict", "conflict_note"]
                bericht.konflikte += 1
        elif sieger and not vorhanden.winner_side and not vorhanden.has_conflict:
            # Das Ergebnis war bisher unbekannt und ist es jetzt nicht mehr.
            vorhanden.winner_side = sieger
            felder.append("winner_side")

        if record.external_id and not vorhanden.external_id:
            vorhanden.external_id = record.external_id
            felder.append("external_id")

        if felder:
            vorhanden.save(update_fields=felder + ["updated_at"])

    def _widersprueche_pruefen(self, record, modus, karte, bericht):
        """Bekannte Quellen-ID, aber anderer Name? Melden, nicht korrigieren.

        IDs haben Vorrang - zugeordnet wird weiterhin ueber sie. Ein
        Widerspruch heisst: die ID wurde neu vergeben oder der Name hat sich
        geaendert. Beides soll jemand ansehen, bevor daraus Statistik wird.
        """
        if karte is not None and record.external_map_id \
                and karte.external_id == record.external_map_id:
            if record.map and katalog_schluessel(karte.name) != katalog_schluessel(record.map):
                bericht.id_widersprueche.append(
                    f"Map-ID {record.external_map_id}: Katalog '{karte.name}', "
                    f"geliefert '{record.map}'"
                )
            if modus is not None and modus.external_id == record.external_mode_id \
                    and karte.game_mode_id != modus.id:
                bericht.id_widersprueche.append(
                    f"Map-ID {record.external_map_id}: Katalog-Modus "
                    f"'{karte.game_mode.name}', geliefert '{record.mode}'"
                )
        # Der Modusname wird NICHT geprueft. Gemessen am 2026-09-16: dieselbe
        # modeId heisst je nach Endpoint anders (45 = "airHockey" in
        # /events/rotation, "brawlBall" im Battlelog), und derselbe Name steht
        # fuer mehrere IDs. Eine Namensabweichung bei bekannter ID ist damit
        # der Normalfall, keine Warnung - die ID entscheidet.

    def _patch_fuer(self, zeitpunkt):
        """Der Patch, der zum Spielzeitpunkt galt - der letzte davor."""
        stelle = bisect.bisect_right(self._patch_daten, zeitpunkt.date())
        return self._patches[stelle - 1] if stelle else None
