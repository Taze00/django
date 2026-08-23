"""Legt die drei Uebungen, ihre 21 Progressionen und die Startlevel an.

Warum es diese Migration gibt
-----------------------------
Die Stammdaten wurden urspruenglich von Hand in die Produktions-
datenbank eingespielt, nie per Migration. `0006_update_default_
progressions` setzte anschliessend die Startlevel ueber feste
Primaerschluessel (`Progression.objects.get(id=4)`). Auf einer frischen
Datenbank existierten diese Zeilen nicht und `migrate` brach mit
`Progression.DoesNotExist` ab - die Migrationskette war also nicht von
null reproduzierbar.

Diese Migration schliesst die Luecke: sie legt die Stammdaten selbst an,
und zwar ueber (Uebung, Level) statt ueber IDs. Welche Primaerschluessel
die Datenbank vergibt, spielt keine Rolle mehr.

Warum sie am Ende steht und nicht vor 0006
------------------------------------------
Naheliegend waere gewesen, sie als Abhaengigkeit VOR 0006 einzuhaengen.
Das geht nicht: auf der Produktionsdatenbank ist 0006 laengst angewendet.
Django prueft in `check_consistent_history()`, ob eine angewendete
Migration vor ihren Abhaengigkeiten liegt, und bricht sonst mit
`InconsistentMigrationHistory` ab - auch bei `--fake`. Die Variante
"vorher" waere nur noch mit einem haendischen INSERT in
`django_migrations` zu retten gewesen, also mit genau der Handarbeit, die
das Problem verursacht hat.

Deshalb: 0006 wurde tolerant gemacht (`filter().update()` statt `get()`,
laeuft auf leerer Tabelle folgenlos durch), und diese Migration setzt am
Ende sowohl die Stammdaten als auch die Startlevel. Das Endergebnis ist
auf beiden Wegen dasselbe.

Idempotenz
----------
`get_or_create` auf dem Paar (exercise, level) - genau das
`unique_together` des Modells. Auf der Produktionsdatenbank, wo alle 21
Zeilen existieren, wird nichts angelegt und kein bestehender Wert
ueberschrieben. Die Startlevel werden auf denselben Stand gesetzt, den
0006 dort bereits hergestellt hat.
"""

from django.db import migrations

# (Uebung, Kategorie, Sortierung)
UEBUNGEN = [
    ("Push-ups", "PUSH", 1),
    ("Pull-ups", "PULL", 2),
    ("Planks", "CORE", 3),
]

# (Uebung, Level, Name, Zieltyp, Zielwert, Saetze, Sitzungen)
PROGRESSIONEN = [
    ("Push-ups", 1, "Wall Push-ups", "reps", 8, 2, 3),
    ("Push-ups", 2, "Incline Push-ups", "reps", 8, 2, 3),
    ("Push-ups", 3, "Knee Push-ups", "reps", 8, 2, 3),
    ("Push-ups", 4, "Standard Push-ups", "reps", 8, 2, 3),
    ("Push-ups", 5, "Diamond Push-ups", "reps", 6, 2, 3),
    ("Push-ups", 6, "Decline Push-ups", "reps", 6, 2, 3),
    ("Push-ups", 7, "Pseudo Planche Push-ups", "reps", 5, 2, 3),
    ("Pull-ups", 1, "Dead Hang", "time", 30, 2, 3),
    ("Pull-ups", 2, "Scapular Shrugs", "reps", 10, 2, 3),
    ("Pull-ups", 3, "Active Hang", "time", 20, 2, 3),
    ("Pull-ups", 4, "Pull-up Negatives", "reps", 5, 2, 3),
    ("Pull-ups", 5, "Band-Assisted Pull-ups", "reps", 8, 2, 3),
    ("Pull-ups", 6, "Standard Pull-ups", "reps", 5, 2, 3),
    ("Pull-ups", 7, "Chest-to-Bar", "reps", 5, 2, 3),
    ("Planks", 1, "Knee Plank", "time", 30, 2, 3),
    ("Planks", 2, "Incline Plank", "time", 45, 2, 3),
    ("Planks", 3, "Standard Plank", "time", 60, 2, 3),
    ("Planks", 4, "Feet-Elevated Plank", "time", 60, 2, 3),
    ("Planks", 5, "Extended Plank", "time", 45, 2, 3),
    ("Planks", 6, "RKC Plank", "time", 30, 2, 3),
    ("Planks", 7, "One-Arm Plank", "time", 20, 2, 3),
]

# (Uebung, Level) der Progression, auf der ein neuer Nutzer startet -
# derselbe Stand, den 0006 setzt.
STARTLEVEL = [
    ("Push-ups", 4),   # Standard Push-ups
    ("Pull-ups", 1),   # Dead Hang
    ("Planks", 3),     # Standard Plank
]


def stammdaten_anlegen(apps, schema_editor):
    Exercise = apps.get_model("fitness", "Exercise")
    Progression = apps.get_model("fitness", "Progression")

    uebungen = {}
    for name, kategorie, sortierung in UEBUNGEN:
        uebung, _ = Exercise.objects.get_or_create(
            name=name,
            defaults={"category": kategorie, "order": sortierung},
        )
        uebungen[name] = uebung

    for (uebung_name, level, name, zieltyp, zielwert,
         saetze, sitzungen) in PROGRESSIONEN:
        Progression.objects.get_or_create(
            exercise=uebungen[uebung_name],
            level=level,
            defaults={
                "name": name,
                "target_type": zieltyp,
                "target_value": zielwert,
                "sets_required": saetze,
                "sessions_required": sitzungen,
            },
        )

    # Startlevel setzen. Auf der Produktionsdatenbank aendert das nichts,
    # dort steht derselbe Stand schon seit 0006.
    Progression.objects.all().update(user_starts_here=False)
    for uebung_name, level in STARTLEVEL:
        Progression.objects.filter(
            exercise__name=uebung_name, level=level
        ).update(user_starts_here=True)


def stammdaten_entfernen(apps, schema_editor):
    """Rueckwaerts: entfernt die angelegten Zeilen wieder.

    Progressionen haengen an `UserExerciseProgression.current_progression`
    und `WorkoutSet.progression`, beide mit `on_delete=PROTECT`. Was noch
    benutzt wird, bleibt deshalb stehen, statt die Migration mit einem
    ProtectedError abzubrechen: auf einer leeren Datenbank raeumt sie
    vollstaendig auf, auf einer benutzten laesst sie die Nutzerdaten
    unangetastet.
    """
    Exercise = apps.get_model("fitness", "Exercise")
    Progression = apps.get_model("fitness", "Progression")
    UserExerciseProgression = apps.get_model(
        "fitness", "UserExerciseProgression"
    )
    WorkoutSet = apps.get_model("fitness", "WorkoutSet")

    benutzt = set(
        UserExerciseProgression.objects.values_list(
            "current_progression_id", flat=True
        )
    ) | set(WorkoutSet.objects.values_list("progression_id", flat=True))

    for uebung_name, level, *_ in PROGRESSIONEN:
        Progression.objects.filter(
            exercise__name=uebung_name, level=level
        ).exclude(id__in=benutzt).delete()

    for name, _kategorie, _sortierung in UEBUNGEN:
        Exercise.objects.filter(name=name, progressions__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("fitness", "0008_levelevent"),
    ]

    operations = [
        migrations.RunPython(
            code=stammdaten_anlegen,
            reverse_code=stammdaten_entfernen,
        ),
    ]
