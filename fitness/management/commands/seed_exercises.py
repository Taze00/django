from django.core.management.base import BaseCommand
from fitness.models import Exercise, Progression


class Command(BaseCommand):
    help = "Seed Push-ups and Pull-ups exercises with progressions"

    def handle(self, *args, **options):
        pushup, _ = Exercise.objects.get_or_create(
            name="Push-ups",
            defaults={"category": "PUSH", "order": 1}
        )
        
        pullup, _ = Exercise.objects.get_or_create(
            name="Pull-ups",
            defaults={"category": "PULL", "order": 2}
        )

        pushup_progressions = [
            (1, "Wall Push-ups", "reps", 8, False),
            (2, "Incline Push-ups", "reps", 8, False),
            (3, "Knee Push-ups", "reps", 8, True),
            (4, "Standard Push-ups", "reps", 8, False),
            (5, "Diamond Push-ups", "reps", 6, False),
            (6, "Decline Push-ups", "reps", 6, False),
            (7, "Pseudo Planche Push-ups", "reps", 5, False),
        ]

        for level, name, target_type, target_value, user_starts in pushup_progressions:
            Progression.objects.get_or_create(
                exercise=pushup,
                level=level,
                defaults={
                    "name": name,
                    "target_type": target_type,
                    "target_value": target_value,
                    "user_starts_here": user_starts,
                    "sessions_required": 3,
                }
            )

        pullup_progressions = [
            (1, "Dead Hang", "time", 30, True),
            (2, "Scapular Shrugs", "reps", 10, False),
            (3, "Active Hang", "time", 20, False),
            (4, "Pull-up Negatives", "reps", 5, False),
            (5, "Band-Assisted Pull-ups", "reps", 8, False),
            (6, "Standard Pull-ups", "reps", 5, False),
            (7, "Chest-to-Bar", "reps", 5, False),
        ]

        for level, name, target_type, target_value, user_starts in pullup_progressions:
            Progression.objects.get_or_create(
                exercise=pullup,
                level=level,
                defaults={
                    "name": name,
                    "target_type": target_type,
                    "target_value": target_value,
                    "user_starts_here": user_starts,
                    "sessions_required": 3,
                }
            )


        planks, _ = Exercise.objects.get_or_create(
            name="Planks",
            defaults={"category": "CORE", "order": 3}
        )

        planks_progressions = [
            (1, "Knee Plank", "time", 30, True),
            (2, "Incline Plank", "time", 45, False),
            (3, "Standard Plank", "time", 60, False),
            (4, "Feet-Elevated Plank", "time", 60, False),
            (5, "Extended Plank", "time", 45, False),
            (6, "RKC Plank", "time", 30, False),
            (7, "One-Arm Plank", "time", 20, False),
        ]

        for level, name, target_type, target_value, user_starts in planks_progressions:
            Progression.objects.get_or_create(
                exercise=planks,
                level=level,
                defaults={
                    "name": name,
                    "target_type": target_type,
                    "target_value": target_value,
                    "user_starts_here": user_starts,
                    "sessions_required": 3,
                }
            )

        # UserExerciseProgression für alle bestehenden User anlegen
        from django.contrib.auth.models import User as DjangoUser
        from fitness.models import UserExerciseProgression
        
        for user in DjangoUser.objects.all():
            for exercise in Exercise.objects.all():
                starts_here = exercise.progressions.filter(user_starts_here=True).first()
                if starts_here:
                    UserExerciseProgression.objects.get_or_create(
                        user=user,
                        exercise=exercise,
                        defaults={"current_progression": starts_here}
                    )

        self.stdout.write(
            self.style.SUCCESS("✅ Successfully seeded exercises!")
        )
