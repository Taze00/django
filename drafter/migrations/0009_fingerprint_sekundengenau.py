from django.db import migrations
import hashlib
import json
import re

from django.utils.text import slugify

# Stand der Regel beim Anlegen dieser Migration. Bewusst ausgeschrieben:
# Migrationen duerfen nicht von Code abhaengen, der sich spaeter aendert.
#
# 0 = sekundengenau. Bis 0006 galten 60 Sekunden Toleranz; das war eine
# Schaetzung. Gemessen am 2026-09-16 tragen beide Battlelogs derselben
# Partie exakt denselben Zeitstempel, waehrend dieselben sechs Spieler
# Serien auf derselben Map spielen - oft nur 100-160 s auseinander. Die
# Toleranz hat deshalb echte Partien verschmolzen statt Dubletten erkannt.
TOLERANZ_SEKUNDEN = 0


def _schluessel(name):
    """Wie drafter.services.ingest.fingerprint.katalog_schluessel - eingefroren."""
    return slugify(re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(name or "")))


def _zeit(played_at):
    if TOLERANZ_SEKUNDEN <= 0:
        return int(played_at.timestamp())
    return int(played_at.timestamp() // TOLERANZ_SEKUNDEN)


def neu_berechnen(apps, schema_editor):
    """Rekonstruierte Fingerabdruecke nach der neuen Regel nachrechnen.

    Ohne diesen Schritt wuerde eine neue Sichtung eine bereits
    gespeicherte Partie nicht wiedererkennen: der Importer rechnet ab
    jetzt sekundengenau, die gespeicherten Werte stammen aus 60-s-Eimern.
    Bei Partien ohne Quellen-ID ist derselbe Wert auch der eindeutige
    Schluessel `fingerprint`.
    """
    Match = apps.get_model("drafter", "Match")
    MatchPlayer = apps.get_model("drafter", "MatchPlayer")
    geaendert = []
    for match in Match.objects.all():
        teams = {"a": [], "b": []}
        for spieler in MatchPlayer.objects.filter(match_id=match.id):
            if spieler.brawler_id:
                identitaet = f"brawler:{spieler.brawler_id}"
            elif spieler.external_brawler_id:
                identitaet = f"quelle:{spieler.external_brawler_id}"
            else:
                identitaet = f"name:{_schluessel(spieler.brawler_name)}"
            teams.setdefault(spieler.side, []).append(identitaet)
        a, b = sorted([sorted(teams.get("a", [])), sorted(teams.get("b", []))])
        if match.brawl_map_id:
            ort = f"karte:{match.brawl_map_id}"
        elif match.external_map_id:
            ort = f"quelle:{match.external_map_id}"
        else:
            ort = f"name:{_schluessel(match.mode_name)}|{_schluessel(match.map_name)}"

        inhalt = {"t": _zeit(match.played_at), "ort": ort, "a": a, "b": b}
        neu = hashlib.sha256(
            json.dumps(inhalt, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if neu == match.reconstructed_fingerprint:
            continue
        match.reconstructed_fingerprint = neu
        if not match.external_id:
            match.fingerprint = neu
        geaendert.append(match)
    Match.objects.bulk_update(
        geaendert, ["fingerprint", "reconstructed_fingerprint"], batch_size=500
    )


class Migration(migrations.Migration):

    dependencies = [
        ('drafter', '0008_collector_und_katalog'),
    ]

    operations = [
        migrations.RunPython(neu_berechnen, migrations.RunPython.noop),
    ]
