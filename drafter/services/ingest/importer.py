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
from dataclasses import dataclass, field

from django.db import DatabaseError, transaction

from drafter.models import Brawler, BrawlMap, GameMode, Patch
from drafter.models.matches import Match, MatchBan, MatchPlayer, RawPayload
from drafter.services.ingest.fingerprint import (
    fingerprint, ist_spiegel, kandidaten, kanonisiere, katalog_schluessel,
)


@dataclass
class ImportBericht:
    lieferungen: int = 0
    bereits_importiert: int = 0
    nicht_unterstuetzt: int = 0
    fehlerhaft: int = 0
    matches_gelesen: int = 0
    ungueltig: int = 0
    neu: int = 0
    duplikate: int = 0
    konflikte: int = 0
    unbekannte_brawler: set = field(default_factory=set)
    unbekannte_maps: set = field(default_factory=set)
    meldungen: list = field(default_factory=list)

    def zeilen(self):
        zeilen = [
            f"Lieferungen:          {self.lieferungen}"
            f" (bereits importiert {self.bereits_importiert},"
            f" nicht auswertbar {self.nicht_unterstuetzt}, fehlerhaft {self.fehlerhaft})",
            f"Partien gelesen:      {self.matches_gelesen} (ungültig verworfen {self.ungueltig})",
            f"  neu gespeichert:    {self.neu}",
            f"  Duplikate:          {self.duplikate}",
            f"  Konflikte:          {self.konflikte}",
        ]
        if self.unbekannte_brawler:
            zeilen.append(f"Unbekannte Brawler:   {', '.join(sorted(self.unbekannte_brawler))}")
        if self.unbekannte_maps:
            zeilen.append(f"Unbekannte Maps:      {', '.join(sorted(self.unbekannte_maps))}")
        return zeilen + [f"  - {m}" for m in self.meldungen]


def inhalts_hash(rohdaten):
    """Stabiler Hash ueber den INHALT, unabhaengig von Schluesselreihenfolge."""
    text = json.dumps(rohdaten, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class MatchImporter:
    def __init__(self, provider, trockenlauf=False):
        self.provider = provider
        self.trockenlauf = trockenlauf
        # Kataloge einmal laden - eine Abfrage je Partie waere bei
        # grossen Importen der teuerste Teil.
        self._brawler = {b.slug: b for b in Brawler.objects.all()}
        self._modi = {m.slug: m for m in GameMode.objects.all()}
        self._maps = {k.slug: k for k in BrawlMap.objects.select_related("game_mode")}
        self._patches = list(Patch.objects.order_by("released_on"))
        self._patch_daten = [p.released_on for p in self._patches]

    # --- Ablauf ---------------------------------------------------------
    def ausfuehren(self):
        bericht = ImportBericht()
        with transaction.atomic():
            for lieferung in self.provider.lieferungen():
                self._lieferung(lieferung, bericht)
            if self.trockenlauf:
                transaction.set_rollback(True)
                bericht.meldungen.append("Trockenlauf - nichts wurde gespeichert")
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
        if RawPayload.objects.filter(content_hash=hash_wert).exists():
            bericht.bereits_importiert += 1
            bericht.meldungen.append(f"{lieferung.referenz}: bereits importiert - übersprungen")
            return

        status = {
            "ausgewertet": RawPayload.ParseStatus.PARSED,
            "nicht_unterstuetzt": RawPayload.ParseStatus.UNSUPPORTED,
        }.get(lieferung.status, RawPayload.ParseStatus.ERROR)

        try:
            # Eigener Sicherungspunkt je Lieferung: eine kaputte Datei
            # soll nicht den ganzen Import zuruecknehmen.
            with transaction.atomic():
                payload = RawPayload.objects.create(
                    source=lieferung.source,
                    format=lieferung.format[:60],
                    reference=lieferung.referenz[:300],
                    content_hash=hash_wert,
                    payload=lieferung.rohdaten,
                    parse_status=status,
                    parse_message=lieferung.meldung,
                )
                if lieferung.matches is None:
                    if status == RawPayload.ParseStatus.UNSUPPORTED:
                        bericht.nicht_unterstuetzt += 1
                    else:
                        bericht.fehlerhaft += 1
                    bericht.meldungen.append(f"{lieferung.referenz}: {lieferung.meldung}")
                    return

                neu_vorher = bericht.neu
                for record in lieferung.matches:
                    bericht.matches_gelesen += 1
                    self._match(record, payload, lieferung.source, bericht)

                bericht.ungueltig += len(lieferung.fehler)
                for fehler in lieferung.fehler[:5]:
                    bericht.meldungen.append(f"{lieferung.referenz}: {fehler}")

                payload.match_count = len(lieferung.matches)
                payload.new_match_count = bericht.neu - neu_vorher
                if lieferung.fehler:
                    payload.parse_message = "\n".join(lieferung.fehler)
                payload.save(update_fields=["match_count", "new_match_count", "parse_message"])
        except (DatabaseError, ValueError, TypeError) as fehler:
            bericht.fehlerhaft += 1
            bericht.meldungen.append(f"{lieferung.referenz}: Import abgebrochen - {fehler}")

    # --- Eine Partie ----------------------------------------------------
    def _match(self, record, payload, quelle, bericht):
        record, _ = kanonisiere(record)
        # Bei spiegelgleichen Teams ist nicht feststellbar, welche Seite
        # gewonnen hat - das Ergebnis bleibt dann unbekannt.
        sieger = "" if ist_spiegel(record) else (record.winner or "")

        vorhanden = Match.objects.filter(fingerprint__in=kandidaten(record)).first()
        if vorhanden is not None:
            self._zusammenfuehren(vorhanden, record, sieger, payload, bericht)
            return

        modus = self._modi.get(katalog_schluessel(record.mode))
        karte = self._maps.get(katalog_schluessel(record.map))
        if karte is None:
            bericht.unbekannte_maps.add(record.map)
        elif modus is None:
            modus = karte.game_mode

        match = Match.objects.create(
            fingerprint=fingerprint(record),
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
        )
        match.payloads.add(payload)

        spieler = []
        for seite in ("a", "b"):
            for s in record.teams[seite]:
                brawler = self._brawler.get(katalog_schluessel(s.brawler))
                if brawler is None:
                    bericht.unbekannte_brawler.add(s.brawler)
                spieler.append(MatchPlayer(
                    match=match, side=seite, brawler=brawler,
                    brawler_name=s.brawler[:80], player_tag=(s.player_tag or "")[:20],
                    pick_order=s.pick_order, build=s.build,
                ))
        MatchPlayer.objects.bulk_create(spieler)

        MatchBan.objects.bulk_create([
            MatchBan(
                match=match, side=ban.get("side") or "",
                brawler=self._brawler.get(katalog_schluessel(ban["brawler"])),
                brawler_name=ban["brawler"][:80], order=ban.get("order"),
            )
            for ban in record.bans
        ])
        bericht.neu += 1

    def _zusammenfuehren(self, vorhanden, record, sieger, payload, bericht):
        """Eine erneute Sichtung einer bekannten Partie."""
        bericht.duplikate += 1
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

    def _patch_fuer(self, zeitpunkt):
        """Der Patch, der zum Spielzeitpunkt galt - der letzte davor."""
        stelle = bisect.bisect_right(self._patch_daten, zeitpunkt.date())
        return self._patches[stelle - 1] if stelle else None
