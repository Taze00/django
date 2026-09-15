# -*- coding: utf-8 -*-
"""Lieferungen in MatchRecords uebersetzen - nur fuer GEPRUEFTE Formate.

Registriert ist genau ein Format: `drafter.match.v1`, das eigene,
vollstaendig dokumentierte Austauschformat (siehe DRAFTER_DOKUMENTATION.md).

Das Format der offiziellen Brawl-Stars-API ist ABSICHTLICH NICHT
registriert. Dafuer braeuchte es Feldnamen und Bedeutungen, die erst
feststehen, wenn eine echte Antwort vorliegt und angesehen wurde. Bis
dahin werden solche Antworten unveraendert gespeichert und als "noch
nicht auswertbar" markiert - nichts wird aus erfundenen Feldern gelesen.

Einen neuen Parser einstecken:

    def parse_offizieller_battlelog(daten): ...  -> ParseErgebnis
    PARSER[FORMAT_OFFIZIELLER_BATTLELOG] = parse_offizieller_battlelog
"""

from dataclasses import dataclass, field
from datetime import datetime

from drafter import config
from drafter.models.base import Datenquelle
from drafter.services.providers.records import MatchRecord, SpielerRecord

FORMAT_NORMALISIERT = "drafter.match.v1"
FORMAT_OFFIZIELLER_BATTLELOG = "brawlstars.battlelog.raw"

# Pflichtangabe jeder Datei: woher die Partien stammen. Ohne sie koennte
# eine ausgedachte Testdatei als Messung in die Statistik gelangen.
HERKUENFTE = {
    "synthetisch": Datenquelle.SYNTHETIC,
    "api-mitschnitt": Datenquelle.FIXTURE,
    "manuell-erfasst": Datenquelle.FIXTURE,
}

SIEGER = {"a", "b", "draw", None}
SEITEN = {"a", "b", None}
BUILD_SCHLUESSEL = {"gadget", "star_power", "gears", "hypercharge"}


class ParserFehler(ValueError):
    """Die Lieferung als Ganzes ist nicht auswertbar."""


@dataclass
class ParseErgebnis:
    matches: list = field(default_factory=list)
    # Einzelne verworfene Partien. Eine fehlerhafte Partie verwirft nicht
    # die ganze Datei - aber sie wird benannt, nicht verschwiegen.
    fehler: list = field(default_factory=list)


def quelle_fuer(daten):
    """Datenquelle aus der Herkunftsangabe einer Lieferung."""
    herkunft = daten.get("herkunft") if isinstance(daten, dict) else None
    if herkunft not in HERKUENFTE:
        raise ParserFehler(
            f"'herkunft' fehlt oder ist unbekannt ({herkunft!r}). "
            f"Erlaubt: {', '.join(sorted(HERKUENFTE))}"
        )
    return HERKUENFTE[herkunft]


def _zeitpunkt(wert, pfad):
    if not isinstance(wert, str):
        raise ValueError(f"{pfad}.played_at fehlt")
    try:
        zeitpunkt = datetime.fromisoformat(wert.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{pfad}.played_at ist kein ISO-Zeitpunkt: {wert!r}")
    if zeitpunkt.tzinfo is None:
        # Ohne Zeitzone ist ein Zeitpunkt mehrdeutig - und die
        # Deduplizierung vergleicht Zeitpunkte.
        raise ValueError(f"{pfad}.played_at hat keine Zeitzone: {wert!r}")
    return zeitpunkt


def _text(wert, pfad, pflicht=True):
    if wert is None and not pflicht:
        return None
    if not isinstance(wert, str) or not wert.strip():
        raise ValueError(f"{pfad} muss ein nichtleerer Text sein")
    return wert.strip()


def _ganzzahl(wert, pfad):
    if wert is None:
        return None
    if isinstance(wert, bool) or not isinstance(wert, int) or wert < 0:
        raise ValueError(f"{pfad} muss eine nichtnegative Ganzzahl sein")
    return wert


def _build(wert, pfad):
    if wert is None:
        return None
    if not isinstance(wert, dict):
        raise ValueError(f"{pfad} muss ein Objekt sein")
    unbekannt = set(wert) - BUILD_SCHLUESSEL
    if unbekannt:
        raise ValueError(f"{pfad}: unbekannte Schluessel {sorted(unbekannt)}")
    gears = wert.get("gears")
    if gears is not None and (
        not isinstance(gears, list) or not all(isinstance(g, str) for g in gears)
    ):
        raise ValueError(f"{pfad}.gears muss eine Liste von Texten sein")
    return dict(wert)


def _spieler(eintrag, pfad):
    if not isinstance(eintrag, dict):
        raise ValueError(f"{pfad} muss ein Objekt sein")
    return SpielerRecord(
        brawler=_text(eintrag.get("brawler"), f"{pfad}.brawler"),
        player_tag=_text(eintrag.get("player_tag"), f"{pfad}.player_tag", pflicht=False) or "",
        pick_order=_ganzzahl(eintrag.get("pick_order"), f"{pfad}.pick_order"),
        build=_build(eintrag.get("build"), f"{pfad}.build"),
    )


def _match(eintrag, pfad):
    if not isinstance(eintrag, dict):
        raise ValueError(f"{pfad} muss ein Objekt sein")

    teams = eintrag.get("teams")
    if not isinstance(teams, dict) or set(teams) != {"a", "b"}:
        raise ValueError(f"{pfad}.teams braucht genau die Seiten 'a' und 'b'")
    spieler = {}
    for seite in ("a", "b"):
        liste = teams[seite]
        if not isinstance(liste, list) or not liste:
            raise ValueError(f"{pfad}.teams.{seite} muss eine nichtleere Liste sein")
        spieler[seite] = [_spieler(s, f"{pfad}.teams.{seite}[{i}]") for i, s in enumerate(liste)]

    winner = eintrag.get("winner")
    if winner not in SIEGER:
        raise ValueError(f"{pfad}.winner muss a, b, draw oder null sein")
    first_pick = eintrag.get("first_pick")
    if first_pick not in SEITEN:
        raise ValueError(f"{pfad}.first_pick muss a, b oder null sein")

    rank_pool = eintrag.get("rank_pool", "alle")
    if rank_pool not in dict(config.RANG_POOLS):
        raise ValueError(f"{pfad}.rank_pool unbekannt: {rank_pool!r}")

    bans = []
    for i, ban in enumerate(eintrag.get("bans") or []):
        bpfad = f"{pfad}.bans[{i}]"
        if not isinstance(ban, dict):
            raise ValueError(f"{bpfad} muss ein Objekt sein")
        if ban.get("side") not in SEITEN:
            raise ValueError(f"{bpfad}.side muss a, b oder null sein")
        bans.append({
            "brawler": _text(ban.get("brawler"), f"{bpfad}.brawler"),
            "side": ban.get("side"),
            "order": _ganzzahl(ban.get("order"), f"{bpfad}.order"),
        })

    ranked = eintrag.get("ranked", True)
    if not isinstance(ranked, bool):
        raise ValueError(f"{pfad}.ranked muss true oder false sein")

    return MatchRecord(
        played_at=_zeitpunkt(eintrag.get("played_at"), pfad),
        mode=_text(eintrag.get("mode"), f"{pfad}.mode"),
        map=_text(eintrag.get("map"), f"{pfad}.map"),
        teams=spieler,
        winner=winner,
        rank_pool=rank_pool,
        ranked=ranked,
        first_pick=first_pick,
        bans=bans,
        duration_seconds=_ganzzahl(eintrag.get("duration_seconds"), f"{pfad}.duration_seconds"),
        external_id=_text(eintrag.get("external_id"), f"{pfad}.external_id", pflicht=False),
    )


def parse_normalisiert_v1(daten):
    """Das eigene Austauschformat lesen."""
    if not isinstance(daten, dict):
        raise ParserFehler("Die Datei muss ein JSON-Objekt sein")
    if daten.get("format") != FORMAT_NORMALISIERT:
        raise ParserFehler(f"Falsches Format: {daten.get('format')!r}")
    quelle_fuer(daten)   # Herkunft ist Pflicht
    eintraege = daten.get("matches")
    if not isinstance(eintraege, list):
        raise ParserFehler("'matches' muss eine Liste sein")

    ergebnis = ParseErgebnis()
    for i, eintrag in enumerate(eintraege):
        try:
            ergebnis.matches.append(_match(eintrag, f"matches[{i}]"))
        except ValueError as fehler:
            ergebnis.fehler.append(str(fehler))
    return ergebnis


PARSER = {
    FORMAT_NORMALISIERT: parse_normalisiert_v1,
    # FORMAT_OFFIZIELLER_BATTLELOG: bewusst nicht registriert - siehe oben.
}


def parser_fuer(format_name):
    return PARSER.get(format_name)
