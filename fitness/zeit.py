"""Was CORVIS unter "heute" versteht.

Django rechnet projektweit in UTC (TIME_ZONE = 'UTC', USE_TZ = True). Fuer
Zeitstempel ist das richtig, fuer Kalendertage nicht: ein Training um 00:30
deutscher Zeit ist um 22:30 UTC des Vortages passiert und landete damit auf
gestern. Zusammen mit unique_together (user, date) auf Workout hiess das, dass
Sonntagabend und Montag nach Mitternacht um dieselbe Zeile konkurrieren.

Deshalb gibt es hier eine einzige Quelle fuer den CORVIS-Kalendertag. Sie wird
ueber CORVIS_TIME_ZONE eingestellt und beruehrt den Rest des Projekts nicht.

Vorher lagen zwei Quellen nebeneinander: die Views nahmen
timezone.now().date() (Django, UTC), streak.py nahm datetime.date.today()
(Betriebssystem). Solange der Container auf UTC laeuft, stimmen beide zufaellig
ueberein - eine Zeitzonenaenderung im Container haette sie lautlos getrennt.
"""

from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone


def zeitzone():
    """Die fuer CORVIS eingestellte Zeitzone."""
    return ZoneInfo(settings.CORVIS_TIME_ZONE)


def jetzt():
    """Aktueller Zeitpunkt in CORVIS-Zeit (zeitzonenbewusst)."""
    return timezone.now().astimezone(zeitzone())


def heute():
    """Der laufende Kalendertag in CORVIS-Zeit."""
    return jetzt().date()
