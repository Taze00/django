# -*- coding: utf-8 -*-
"""Wann zwei Sichtungen dieselbe Partie sind.

Dieselbe Partie erscheint in bis zu sechs Battlelogs - einmal je
Spieler, und jedes Mal aus dessen Blickwinkel: das eigene Team heisst
dort "a", das andere "b". Ein naiver Fingerabdruck aus "Team a, Team b"
wuerde dieselbe Partie deshalb zweimal zaehlen.

Die Loesung hat zwei Schritte:

1. **Kanonisieren.** Die Seiten werden nach einem festen Kriterium
   geordnet (sortierte Brawler-Liste), Sieger, First Pick und Bans
   wandern mit. Danach sieht die Partie aus jedem Blickwinkel gleich aus.
2. **Zeitfenster.** Zeitstempel koennen je Quelle leicht abweichen. Der
   Fingerabdruck benutzt einen Zeit-Eimer, und beim Nachschlagen werden
   auch die beiden Nachbar-Eimer geprueft - sonst truege eine Abweichung
   von wenigen Sekunden ueber eine Minutengrenze zwei Partien ein.

Bewusst NICHT im Fingerabdruck: das Ergebnis. Zwei Sichtungen mit
widerspruechlichem Ergebnis sollen als dieselbe Partie erkannt und als
Konflikt markiert werden - nicht als zwei verschiedene Partien durchgehen.

Auch nicht enthalten: Spieler-Tags. Liefert eine Quelle sie und eine
andere nicht, haette dieselbe Partie sonst zwei Fingerabdruecke.
"""

import hashlib
import json
from dataclasses import replace

from django.utils.text import slugify

from drafter import config

GEGENSEITE = {"a": "b", "b": "a"}


def katalog_schluessel(name):
    """Name wie geliefert -> Schluessel wie im Katalog ("EL PRIMO" -> "el-primo")."""
    return slugify(str(name or ""))


def _tausche(seite):
    return GEGENSEITE.get(seite, seite)


def _team_schluessel(spieler):
    return tuple(sorted(katalog_schluessel(s.brawler) for s in spieler))


def _tag_schluessel(spieler):
    return tuple(sorted((s.player_tag or "").upper() for s in spieler))


def ist_spiegel(record):
    """Stehen auf beiden Seiten dieselben Brawler - und ohne Tags zur Unterscheidung?

    Im Ranked-Draft unmoeglich (jeder Brawler nur einmal), in anderen
    Modi nicht. Dann laesst sich nicht feststellen, welche Seite aus
    welchem Blickwinkel welche ist - und damit auch nicht, wer gewonnen
    hat. Der Import speichert solche Partien ohne Ergebnis.
    """
    a, b = record.teams.get("a") or [], record.teams.get("b") or []
    return _team_schluessel(a) == _team_schluessel(b) and _tag_schluessel(a) == _tag_schluessel(b)


def kanonisiere(record):
    """Die Seiten in eine feste Reihenfolge bringen.

    Gibt (kanonischer Record, wurden die Seiten getauscht) zurueck.
    """
    a, b = record.teams.get("a") or [], record.teams.get("b") or []
    schluessel_a = (_team_schluessel(a), _tag_schluessel(a))
    schluessel_b = (_team_schluessel(b), _tag_schluessel(b))
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


def zeit_eimer(played_at, toleranz=None):
    toleranz = toleranz or config.MATCH_ZEITTOLERANZ_SEKUNDEN
    return int(played_at.timestamp() // toleranz)


def _hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fingerprint(record, eimer=None):
    """Fingerabdruck eines KANONISCHEN Records.

    Liefert die Quelle eine eigene Partie-ID, gewinnt diese - sie ist
    verlaesslicher als jede Rekonstruktion. Ob die offizielle API eine
    solche ID hat, ist ungeprueft.
    """
    if record.external_id:
        return _hash(f"ext|{record.external_id}")
    if eimer is None:
        eimer = zeit_eimer(record.played_at)
    inhalt = {
        "t": eimer,
        "modus": katalog_schluessel(record.mode),
        "map": katalog_schluessel(record.map),
        "a": list(_team_schluessel(record.teams.get("a") or [])),
        "b": list(_team_schluessel(record.teams.get("b") or [])),
    }
    return _hash(json.dumps(inhalt, sort_keys=True))


def kandidaten(record):
    """Alle Fingerabdruecke, unter denen diese Partie schon gespeichert sein koennte."""
    if record.external_id:
        return [fingerprint(record)]
    eimer = zeit_eimer(record.played_at)
    return [fingerprint(record, e) for e in (eimer, eimer - 1, eimer + 1)]
