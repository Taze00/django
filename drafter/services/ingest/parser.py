# -*- coding: utf-8 -*-
"""Lieferungen in MatchRecords uebersetzen - nur fuer GEPRUEFTE Formate.

Registriert sind zwei Formate:

- `drafter.match.v1` - das eigene, vollstaendig dokumentierte Austauschformat.
- `brawlstars.battlelog.raw` - ein Mitschnitt von /players/{tag}/battlelog
  der offiziellen API. Der Parser dafuer ist auf Grundlage ECHTER
  Antworten geschrieben (Mitschnitt vom 2026-09-15, anonymisiert unter
  drafter/testdaten/offizieller_battlelog_anonymisiert.json) und liest nur
  Felder, die dort tatsaechlich vorkommen. Swagger-Modellnamen spielen
  keine Rolle - was nicht in der Antwort steht, wird nicht gelesen.

Spieler-, Brawler- und Ranglisten-Mitschnitte enthalten keine Partien und
bekommen keinen Parser; sie werden nur gespeichert.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from drafter import config
from drafter.models.base import Datenquelle
from drafter.services.providers.records import MatchRecord, SpielerRecord

FORMAT_NORMALISIERT = "drafter.match.v1"
FORMAT_OFFIZIELLER_BATTLELOG = "brawlstars.battlelog.raw"
# Weitere Mitschnitte der offiziellen API. Sie enthalten keine Partien und
# bekommen deshalb nie einen Match-Parser - sie werden gespeichert, damit
# ihre Struktur (etwa stabile Brawler-IDs) angesehen werden kann.
FORMAT_OFFIZIELLER_SPIELER = "brawlstars.player.raw"
FORMAT_OFFIZIELLE_BRAWLER = "brawlstars.brawlers.raw"
FORMAT_OFFIZIELLE_RANGLISTE = "brawlstars.rankings.raw"

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
    # Gueltige Partien, die nicht in dieses System gehoeren (z.B. Showdown).
    uebersprungen: list = field(default_factory=list)


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


def _kennung(wert, pfad):
    """Eine ID der Quelle - Text oder Ganzzahl, als Text gespeichert.

    Welchen Typ echte IDs haben, ist ungeprueft; beide sind erlaubt.
    """
    if wert is None:
        return None
    if isinstance(wert, bool) or not isinstance(wert, (str, int)) or str(wert).strip() == "":
        raise ValueError(f"{pfad} muss Text oder eine Ganzzahl sein")
    return str(wert).strip()


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
    # ID bevorzugt; der Name ist dann optional. Ohne ID ist er Pflicht.
    brawler_id = _kennung(eintrag.get("brawler_id"), f"{pfad}.brawler_id")
    return SpielerRecord(
        brawler=_text(eintrag.get("brawler"), f"{pfad}.brawler", pflicht=brawler_id is None) or "",
        player_tag=_text(eintrag.get("player_tag"), f"{pfad}.player_tag", pflicht=False) or "",
        pick_order=_ganzzahl(eintrag.get("pick_order"), f"{pfad}.pick_order"),
        build=_build(eintrag.get("build"), f"{pfad}.build"),
        external_brawler_id=brawler_id,
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
        ban_id = _kennung(ban.get("brawler_id"), f"{bpfad}.brawler_id")
        bans.append({
            "brawler": _text(ban.get("brawler"), f"{bpfad}.brawler", pflicht=ban_id is None) or "",
            "external_brawler_id": ban_id,
            "side": ban.get("side"),
            "order": _ganzzahl(ban.get("order"), f"{bpfad}.order"),
        })

    ranked = eintrag.get("ranked", True)
    if not isinstance(ranked, bool):
        raise ValueError(f"{pfad}.ranked muss true oder false sein")

    mode_id = _kennung(eintrag.get("mode_id"), f"{pfad}.mode_id")
    map_id = _kennung(eintrag.get("map_id"), f"{pfad}.map_id")
    return MatchRecord(
        played_at=_zeitpunkt(eintrag.get("played_at"), pfad),
        mode=_text(eintrag.get("mode"), f"{pfad}.mode", pflicht=mode_id is None and map_id is None) or "",
        map=_text(eintrag.get("map"), f"{pfad}.map", pflicht=map_id is None) or "",
        external_mode_id=mode_id,
        external_map_id=map_id,
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


# =========================================================================
# Offizieller Battlelog (/players/{tag}/battlelog)
# =========================================================================
# Beobachtete Struktur eines Eintrags (25 Eintraege, 2026-09-15):
#
#   battleTime            "20260914T184146.000Z"
#   event                 {id, mode, modeId, map}
#   battle.mode           == event.mode
#   battle.type           "ranked" | "soloRanked"
#   battle.result         "victory" | "defeat"   - nur bei zwei Teams
#   battle.duration       21..150                - nur bei zwei Teams
#   battle.trophyChange   nur bei "ranked"
#   battle.starPlayer     {tag, name, brawler}   - nur bei zwei Teams
#   battle.teams          [[{tag, name, brawler{id, name, power, trophies}}]x3]x2
#   battle.players        [...]x10 + battle.rank - Showdown statt teams
#
# NICHT vorhanden: Partie-ID, Bans, Pick-Reihenfolge, Gadgets, Star Powers,
# Gears, Hypercharges, Elo. Sie bleiben im MatchRecord leer.

BATTLE_TIME_FORMAT = "%Y%m%dT%H%M%S.%fZ"

# "soloRanked" ist der Ranked-Modus: keine trophyChange, und brawler.trophies
# ist bei allen sechs Spielern gleich und entspricht dem rankedRank des
# Profils. "ranked" ist - trotz des Namens - die Trophaeen-Rangliste (mit
# trophyChange, Trophaeen bis 2188, auch Showdown). Beleg: 4 bzw. 21
# Eintraege eines Spielers; bei neuen Typen oder Gegenbelegen hier anpassen.
RANKED_DRAFT_TYPEN = frozenset({"soloRanked"})

# Beobachtete Werte von battle.result. Andere Werte (etwa ein Unentschieden,
# das in den Daten nicht vorkam) ergeben KEIN Ergebnis statt eines geratenen.
ERGEBNIS_EIGENES_TEAM = {"victory": True, "defeat": False}


def _api_tag(wert):
    text = str(wert or "").strip().upper().lstrip("#")
    return f"#{text}" if text else None


def _api_ganzzahl(wert):
    return wert if isinstance(wert, int) and not isinstance(wert, bool) else None


def _api_text(wert):
    return wert if isinstance(wert, str) else ""


def _api_id(wert):
    """IDs kommen als Ganzzahl; gespeichert wird Text."""
    return str(wert) if _api_ganzzahl(wert) is not None else None


def _api_spieler(eintrag, pfad):
    if not isinstance(eintrag, dict):
        raise ValueError(f"{pfad} ist kein Objekt")
    brawler = eintrag.get("brawler") if isinstance(eintrag.get("brawler"), dict) else {}
    brawler_id = _api_id(brawler.get("id"))
    name = _api_text(brawler.get("name"))
    if brawler_id is None and not name:
        raise ValueError(f"{pfad}.brawler hat weder id noch name")
    return SpielerRecord(
        brawler=name,
        player_tag=_api_text(eintrag.get("tag")),
        external_brawler_id=brawler_id,
        power=_api_ganzzahl(brawler.get("power")),
        trophies=_api_ganzzahl(brawler.get("trophies")),
    )


def _api_partie(eintrag, pfad, perspektive):
    """(MatchRecord, None) - oder (None, Grund), wenn es keine Draft-Partie ist."""
    if not isinstance(eintrag, dict):
        raise ValueError(f"{pfad} ist kein Objekt")
    battle = eintrag.get("battle")
    if not isinstance(battle, dict):
        raise ValueError(f"{pfad}.battle fehlt")
    event = eintrag.get("event") if isinstance(eintrag.get("event"), dict) else {}
    modus = _api_text(battle.get("mode")) or _api_text(event.get("mode"))

    teams = battle.get("teams")
    if not (isinstance(teams, list) and len(teams) == 2
            and all(isinstance(t, list) and t for t in teams)):
        form = "Spielerliste statt Teams" if "players" in battle else "keine zwei Teams"
        return None, f"{pfad}: {modus or 'unbekannter Modus'} - {form}, keine Draft-Partie"

    zeitpunkt_text = eintrag.get("battleTime")
    try:
        zeitpunkt = datetime.strptime(str(zeitpunkt_text), BATTLE_TIME_FORMAT).replace(
            tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(f"{pfad}.battleTime hat ein unbekanntes Format: {zeitpunkt_text!r}")

    seiten = {
        seite: [_api_spieler(s, f"{pfad}.battle.teams[{i}][{j}]") for j, s in enumerate(team)]
        for i, (seite, team) in enumerate(zip(("a", "b"), teams))
    }

    # `result` gilt aus Sicht des abgefragten Spielers - und der steht nicht
    # immer im ersten Team (beobachtet: 11x teams[0], 6x teams[1]). Ohne
    # Umrechnung waere jedes dritte Ergebnis vertauscht.
    sieger = None
    eigenes_team_gewinnt = ERGEBNIS_EIGENES_TEAM.get(battle.get("result"))
    if perspektive and eigenes_team_gewinnt is not None:
        eigene = [
            seite for seite, spieler in seiten.items()
            if any(_api_tag(s.player_tag) == perspektive for s in spieler)
        ]
        if len(eigene) == 1:
            sieger = eigene[0] if eigenes_team_gewinnt else ("b" if eigene[0] == "a" else "a")

    typ = _api_text(battle.get("type"))
    return MatchRecord(
        played_at=zeitpunkt,
        mode=modus,
        map=_api_text(event.get("map")),
        teams=seiten,
        winner=sieger,
        # Der Battlelog nennt keinen Rangbereich der Partie. Ob sich einer
        # aus dem Rang-Wert der Spieler ableiten laesst, ist offen.
        rank_pool="alle",
        ranked=typ in RANKED_DRAFT_TYPEN,
        duration_seconds=_api_ganzzahl(battle.get("duration")),
        # Keine Partie-ID in der Antwort - die Wiedererkennung laeuft ueber
        # den rekonstruierten Fingerabdruck.
        external_id=None,
        external_mode_id=_api_id(event.get("modeId")),
        external_map_id=_api_id(event.get("id")),
        battle_type=typ or None,
    ), None


def parse_offizieller_battlelog(daten):
    """Mitschnitt von /players/{tag}/battlelog lesen.

    Erwartet die eigene Huelle (siehe providers/official_api.py) mit der
    unveraenderten Antwort unter "antwort" und dem abgefragten Spieler-Tag
    unter "referenz" - ohne ihn laesst sich `result` keiner Seite zuordnen.
    Unbekannte Felder werden ignoriert, fehlende optionale bleiben leer.
    """
    if not isinstance(daten, dict):
        raise ParserFehler("Die Datei muss ein JSON-Objekt sein")
    if daten.get("format") != FORMAT_OFFIZIELLER_BATTLELOG:
        raise ParserFehler(f"Falsches Format: {daten.get('format')!r}")
    quelle_fuer(daten)
    antwort = daten.get("antwort")
    if not isinstance(antwort, dict) or not isinstance(antwort.get("items"), list):
        raise ParserFehler("Die Antwort enthält keine Liste 'items' - kein Battlelog")

    perspektive = _api_tag(daten.get("referenz"))
    ergebnis = ParseErgebnis()
    for i, eintrag in enumerate(antwort["items"]):
        pfad = f"antwort.items[{i}]"
        try:
            record, grund = _api_partie(eintrag, pfad, perspektive)
        except ValueError as fehler:
            ergebnis.fehler.append(str(fehler))
            continue
        if record is None:
            ergebnis.uebersprungen.append(grund)
        else:
            ergebnis.matches.append(record)
    return ergebnis


PARSER = {
    FORMAT_NORMALISIERT: parse_normalisiert_v1,
    FORMAT_OFFIZIELLER_BATTLELOG: parse_offizieller_battlelog,
}


def parser_fuer(format_name):
    return PARSER.get(format_name)
