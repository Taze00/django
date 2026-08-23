"""Setzt die Startlevel (`user_starts_here`).

Frueher suchte diese Migration die drei Progressionen ueber feste
Primaerschluessel:

    push  = Progression.objects.get(id=4)
    pull  = Progression.objects.get(id=8)
    plank = Progression.objects.get(id=17)

Das setzte voraus, dass die Stammdaten schon existieren UND genau diese
IDs tragen. Auf einer frischen Datenbank war beides nicht der Fall und
`migrate` brach mit `Progression.DoesNotExist` ab.

Jetzt laeuft die Auswahl ueber (Uebung, Level) und mit
`filter().update()` statt `get()`. Fehlen die Zeilen - wie auf einer
frischen Datenbank, wo die Stammdaten erst in 0009 entstehen -, trifft
das Update null Zeilen und die Migration laeuft folgenlos durch, statt
abzubrechen.

Die eigentliche Arbeit macht auf einer frischen Datenbank deshalb
`0009_seed_exercises_and_progressions`: sie legt die Stammdaten an und
setzt danach dieselben Startlevel. Auf der Produktionsdatenbank, wo 0006
schon angewendet ist, bleibt es beim hier gesetzten Stand. Warum die
Reihenfolge so und nicht umgekehrt ist, steht ausfuehrlich in 0009.
"""

from django.db import migrations

# (Uebung, Level) der Progression, auf der ein neuer Nutzer startet.
STARTLEVEL = [
    ("Push-ups", 4),   # Standard Push-ups
    ("Pull-ups", 1),   # Dead Hang
    ("Planks", 3),     # Standard Plank
]

# Der Stand davor - Ziel der Rueckwaertsmigration.
STARTLEVEL_ALT = [
    ("Push-ups", 3),   # Knee Push-ups
    ("Pull-ups", 1),   # Dead Hang
    ("Planks", 1),     # Knee Plank
]


def _startlevel_setzen(apps, auswahl):
    """Setzt genau die Progressionen aus `auswahl` auf user_starts_here.

    `filter().update()` statt `get()`: fehlt eine Zeile, passiert nichts,
    statt die ganze Migration abzubrechen.
    """
    Progression = apps.get_model("fitness", "Progression")

    Progression.objects.all().update(user_starts_here=False)

    for uebung_name, level in auswahl:
        Progression.objects.filter(
            exercise__name=uebung_name, level=level
        ).update(user_starts_here=True)


def startlevel_setzen(apps, schema_editor):
    _startlevel_setzen(apps, STARTLEVEL)


def startlevel_zurueckdrehen(apps, schema_editor):
    _startlevel_setzen(apps, STARTLEVEL_ALT)


class Migration(migrations.Migration):

    dependencies = [
        ("fitness", "0005_userprofile_onboarding_completed_and_more"),
    ]

    operations = [
        migrations.RunPython(
            code=startlevel_setzen,
            reverse_code=startlevel_zurueckdrehen,
        ),
    ]
