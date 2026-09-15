# -*- coding: utf-8 -*-
"""Wann zwei Sichtungen dieselbe Partie sind.

Dieselbe Partie erscheint in bis zu sechs Battlelogs - einmal je
Spieler, jedes Mal aus dessen Blickwinkel: das eigene Team heisst dort
"a", das andere "b". Die Wiedererkennung hat deshalb eine feste
Rangfolge:

**1. Partie-ID der Quelle - exakt.**
Liefert die Quelle eine eigene ID, entscheidet sie allein. Keine
Zeittoleranz, keine Rekonstruktion. Zwei Sichtungen mit verschiedenen
IDs sind zwei Partien, auch wenn Zeit, Map und Teams zusammenpassen.
Ob die offizielle API eine solche ID hat, ist ungeprueft.

**2. Rekonstruierter Fingerabdruck - nur der Fallback.**
Ohne ID wird die Partie aus drei Dingen wiedererkannt:
- **Ort**: Map-ID aus dem Katalog, sonst Modus- und Map-Name
- **Teams**: Brawler-IDs aus dem Katalog, sonst Namen - vorher
  kanonisiert, damit beide Blickwinkel gleich aussehen (Sieger, First
  Pick und Bans wandern mit)
- **Zeit**: ein Eimer von `MATCH_ZEITTOLERANZ_SEKUNDEN`, beim Nachschlagen
  plus beide Nachbar-Eimer, damit wenige Sekunden Abweichung ueber eine
  Eimergrenze nicht zwei Partien ergeben.

Die 60-Sekunden-Toleranz existiert NUR in Stufe 2. Sie ist eine
Schaetzung, und je mehr Quellen IDs liefern, desto seltener wird sie
ueberhaupt gebraucht.

**Warum IDs vor Namen:** Namen aendern Schreibweise, Uebersetzung und
Gross-/Kleinschreibung ("EL PRIMO", "El Primo"); IDs nicht. Und liefert
eine Quelle IDs, eine andere Namen, muessen beide auf DENSELBEN
Fingerabdruck fuehren - deshalb geht der Fingerabdruck ueber die
Katalog-Identitaet, auf die beide aufgeloest werden, nicht ueber das
Gelieferte. Diese Aufloesung macht der Importer und reicht sie als
`identitaet` und `ort` hierher.

Bewusst NICHT im Fingerabdruck:
- das Ergebnis - widerspruechliche Sichtungen sollen als Konflikt
  auffallen, nicht als zwei Partien durchgehen
- Spieler-Tags - liefert eine Quelle sie und eine andere nicht, haette
  dieselbe Partie sonst zwei Fingerabdruecke
"""

import hashlib
import json
import re
from dataclasses import replace

from django.utils.text import slugify

from drafter import config

GEGENSEITE = {"a": "b", "b": "a"}


def katalog_schluessel(name):
    """Name wie geliefert -> Schluessel wie im Katalog.

        "EL PRIMO" -> "el-primo"      "brawlBall" -> "brawl-ball"

    camelCase wird an Uebergaengen klein->gross getrennt: die offizielle
    API liefert Modi als "brawlBall", "gemGrab", "hotZone" - ohne Trennung
    wuerde daraus "brawlball" und selbst die Namens-Rueckfallsuche faende den
    Modus nicht. Grossgeschriebene Namen ("GALE", "MR. P") bleiben unberuehrt.
    """
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(name or ""))
    return slugify(text)


# --- Identitaeten ohne Katalog (Rueckfall und fuer Tests) -----------------

def standard_identitaet(spieler):
    """Identitaet eines Spielers, wenn niemand gegen den Katalog aufgeloest hat."""
    if spieler.external_brawler_id:
        return f"quelle:{spieler.external_brawler_id}"
    return f"name:{katalog_schluessel(spieler.brawler)}"


def standard_ort(record):
    if record.external_map_id:
        return f"quelle:{record.external_map_id}"
    return f"name:{katalog_schluessel(record.mode)}|{katalog_schluessel(record.map)}"


# --- Kanonisieren ---------------------------------------------------------

def _tausche(seite):
    return GEGENSEITE.get(seite, seite)


def _team_schluessel(spieler, identitaet):
    return tuple(sorted(identitaet(s) for s in spieler))


def _tag_schluessel(spieler):
    return tuple(sorted((s.player_tag or "").upper() for s in spieler))


def ist_spiegel(record, identitaet=standard_identitaet):
    """Beide Seiten gleich - und ohne Tags zur Unterscheidung?

    Im Ranked-Draft unmoeglich (jeder Brawler nur einmal), in anderen
    Modi nicht. Dann ist nicht feststellbar, welche Seite gewonnen hat;
    der Import speichert solche Partien ohne Ergebnis.
    """
    a, b = record.teams.get("a") or [], record.teams.get("b") or []
    return (_team_schluessel(a, identitaet) == _team_schluessel(b, identitaet)
            and _tag_schluessel(a) == _tag_schluessel(b))


def kanonisiere(record, identitaet=standard_identitaet):
    """Die Seiten in eine feste Reihenfolge bringen.

    Gibt (kanonischer Record, wurden die Seiten getauscht) zurueck.
    """
    a, b = record.teams.get("a") or [], record.teams.get("b") or []
    schluessel_a = (_team_schluessel(a, identitaet), _tag_schluessel(a))
    schluessel_b = (_team_schluessel(b, identitaet), _tag_schluessel(b))
    if schluessel_b >= schluessel_a:
        return record, False

    getauscht = replace(
        record,
        teams={"a": b, "b": a},
        winner=_tausche(record.winner),
        first_pick=_tausche(record.first_pick),
        bans=[{**ban, "side": _tausche(ban.get("side"))} for ban in (record.bans or [])],
    )
    return getauscht, True


# --- Fingerabdruecke --------------------------------------------------------

def zeit_eimer(played_at, toleranz=None):
    toleranz = toleranz or config.MATCH_ZEITTOLERANZ_SEKUNDEN
    return int(played_at.timestamp() // toleranz)


def _hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rekonstruierter_fingerprint(record, identitaet=standard_identitaet, ort=None, eimer=None):
    """Stufe 2: Fingerabdruck aus Ort, Teams und Zeit-Eimer eines KANONISCHEN Records."""
    if eimer is None:
        eimer = zeit_eimer(record.played_at)
    inhalt = {
        "t": eimer,
        "ort": ort or standard_ort(record),
        "a": list(_team_schluessel(record.teams.get("a") or [], identitaet)),
        "b": list(_team_schluessel(record.teams.get("b") or [], identitaet)),
    }
    return _hash(json.dumps(inhalt, sort_keys=True))


def eindeutiger_fingerprint(record, identitaet=standard_identitaet, ort=None):
    """Der gespeicherte, eindeutige Schluessel: Partie-ID, sonst rekonstruiert."""
    if record.external_id:
        return _hash(f"ext|{record.external_id}")
    return rekonstruierter_fingerprint(record, identitaet, ort)


def kandidaten(record, identitaet=standard_identitaet, ort=None):
    """Stufe 2: alle rekonstruierten Fingerabdruecke innerhalb der Toleranz."""
    eimer = zeit_eimer(record.played_at)
    return [
        rekonstruierter_fingerprint(record, identitaet, ort, e)
        for e in (eimer, eimer - 1, eimer + 1)
    ]
