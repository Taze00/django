from django.core.management.base import BaseCommand
from fitness.models import Exercise, Progression


class Command(BaseCommand):
    help = "Seed the database with Push-up and Pull-up exercises only (minimal & effective training)"

    def handle(self, *args, **options):
        self.stdout.write("Cleaning up old exercises (Squat, Lunge, Hanging Knee Raise, Hollow Hold)...")

        # Delete unwanted exercises
        for name in ["Squat", "Lunge", "Hanging Knee Raise", "Hollow Hold"]:
            Exercise.objects.filter(name=name).delete()

        self.stdout.write("✓ Cleanup complete")

        self.stdout.write("Seeding 2 exercises (Push-up + Pull-up)...")

        # 1. PUSH-UP (7 Progressionen, reps-based)
        pushup, _ = Exercise.objects.get_or_create(
            name="Push-up",
            defaults={"category": "PUSH", "description": "Horizontal push", "order": 1}
        )
        Progression.objects.filter(exercise=pushup).delete()
        Progression.objects.bulk_create([
            Progression(exercise=pushup, level=1, name="Wall Push-up", description="Push-ups gegen Wand", target_type="reps", target_value=8, sets_required=2, sessions_required=3, user_starts_here=True),
            Progression(exercise=pushup, level=2, name="Incline Push-up", description="Schräge Push-ups", target_type="reps", target_value=8, sets_required=2, sessions_required=3),
            Progression(exercise=pushup, level=3, name="Knee Push-up", description="Push-ups auf Knien", target_type="reps", target_value=8, sets_required=2, sessions_required=3),
            Progression(exercise=pushup, level=4, name="Standard Push-up", description="Standard Push-up", target_type="reps", target_value=8, sets_required=2, sessions_required=3),
            Progression(exercise=pushup, level=5, name="Diamond Push-up", description="Diamond Hand Push-up", target_type="reps", target_value=6, sets_required=2, sessions_required=3),
            Progression(exercise=pushup, level=6, name="Decline Push-up", description="Push-up mit erhobenen Füßen", target_type="reps", target_value=6, sets_required=2, sessions_required=3),
            Progression(exercise=pushup, level=7, name="Pseudo Planche Push-up", description="Pseudo Planche Push-up", target_type="reps", target_value=5, sets_required=2, sessions_required=3),
        ])
        self.stdout.write("✓ Push-up (7 progressions)")

        # 2. PULL-UP (7 Progressionen, mixed time + reps)
        pullup, _ = Exercise.objects.get_or_create(
            name="Pull-up",
            defaults={"category": "PULL", "description": "Vertical pull", "order": 2}
        )
        Progression.objects.filter(exercise=pullup).delete()
        Progression.objects.bulk_create([
            Progression(exercise=pullup, level=1, name="Dead Hang", description="Totes Hang für Zeit", target_type="time", target_value=30, sets_required=2, sessions_required=3, user_starts_here=True),
            Progression(exercise=pullup, level=2, name="Active Hang", description="Aktives Hang mit Schulterbewegung", target_type="time", target_value=20, sets_required=2, sessions_required=3),
            Progression(exercise=pullup, level=3, name="Scapular Shrug", description="Scapular Shoulder Shrug", target_type="reps", target_value=10, sets_required=2, sessions_required=3),
            Progression(exercise=pullup, level=4, name="Pull-up Negatives", description="Negative Pull-ups (Abstieg)", target_type="reps", target_value=5, sets_required=2, sessions_required=3),
            Progression(exercise=pullup, level=5, name="Band-Assisted Pull-up", description="Band-unterstützte Pull-ups", target_type="reps", target_value=8, sets_required=2, sessions_required=3),
            Progression(exercise=pullup, level=6, name="Standard Pull-up", description="Standard Pull-up", target_type="reps", target_value=5, sets_required=2, sessions_required=3),
            Progression(exercise=pullup, level=7, name="Chest-to-Bar Pull-up", description="Chest-to-Bar Pull-up (Advanced)", target_type="reps", target_value=5, sets_required=2, sessions_required=3),
        ])
        self.stdout.write("✓ Pull-up (7 progressions)")

        # Fix any existing records with target_type="hold" to "time"
        Progression.objects.filter(target_type="hold").update(target_type="time")
        self.stdout.write("✓ Fixed legacy hold→time conversions")

        self.stdout.write(self.style.SUCCESS("✓ Successfully seeded 2 exercises (Push-up + Pull-up)!"))
