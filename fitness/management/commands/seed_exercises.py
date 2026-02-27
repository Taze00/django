from django.core.management.base import BaseCommand
from fitness.models import Exercise, Progression


class Command(BaseCommand):
    help = 'Seed the database with 6 calisthenics exercises for 5-day training plan'

    def handle(self, *args, **options):
        self.stdout.write('Seeding 6 exercises...')

        # 1. PUSH-UP (7 Progressionen, reps)
        pushup, _ = Exercise.objects.get_or_create(
            name='Push-up',
            defaults={'category': 'PUSH', 'description': 'Horizontal push', 'order': 1}
        )
        Progression.objects.filter(exercise=pushup).delete()
        Progression.objects.bulk_create([
            Progression(exercise=pushup, level=1, name='Wall Push-up', description='Push-ups gegen Wand', target_type='reps', target_value=20, sets_required=3, sessions_required=3),
            Progression(exercise=pushup, level=2, name='Incline Push-up', description='Schräge Push-ups', target_type='reps', target_value=15, sets_required=3, sessions_required=3),
            Progression(exercise=pushup, level=3, name='Knee Push-up', description='Push-ups auf Knien', target_type='reps', target_value=12, sets_required=3, sessions_required=3),
            Progression(exercise=pushup, level=4, name='Standard Push-up', description='Standard Push-up', target_type='reps', target_value=10, sets_required=3, sessions_required=3),
            Progression(exercise=pushup, level=5, name='Diamond Push-up', description='Diamond Hand Push-up', target_type='reps', target_value=8, sets_required=3, sessions_required=3),
            Progression(exercise=pushup, level=6, name='Decline Push-up', description='Push-up mit erhobenen Füßen', target_type='reps', target_value=8, sets_required=3, sessions_required=3),
            Progression(exercise=pushup, level=7, name='Pike Push-up', description='Pike Push-up für Schultern', target_type='reps', target_value=6, sets_required=3, sessions_required=3),
        ])
        self.stdout.write('✓ Push-up (7 progressions)')

        # 2. PULL-UP (7 Progressionen, mixed)
        pullup, _ = Exercise.objects.get_or_create(
            name='Pull-up',
            defaults={'category': 'PULL', 'description': 'Vertical pull', 'order': 2}
        )
        Progression.objects.filter(exercise=pullup).delete()
        Progression.objects.bulk_create([
            Progression(exercise=pullup, level=1, name='Dead Hang', description='Totes Hang 30s', target_type='hold', target_value=30, sets_required=3, sessions_required=3),
            Progression(exercise=pullup, level=2, name='Active Hang', description='Aktives Hang mit Schulterbewegung', target_type='hold', target_value=20, sets_required=3, sessions_required=3),
            Progression(exercise=pullup, level=3, name='Scap Pull-up', description='Scapula Pull-up', target_type='reps', target_value=8, sets_required=3, sessions_required=3),
            Progression(exercise=pullup, level=4, name='Negative Pull-up', description='Negative Pull-up 5s Abstieg', target_type='reps', target_value=5, sets_required=3, sessions_required=3),
            Progression(exercise=pullup, level=5, name='Band Pull-up', description='Band-unterstützte Pull-up', target_type='reps', target_value=5, sets_required=3, sessions_required=3),
            Progression(exercise=pullup, level=6, name='Jumping Pull-up', description='Sprung-Pull-up', target_type='reps', target_value=5, sets_required=3, sessions_required=3),
            Progression(exercise=pullup, level=7, name='Pull-up', description='Standard Pull-up', target_type='reps', target_value=5, sets_required=3, sessions_required=3),
        ])
        self.stdout.write('✓ Pull-up (7 progressions)')

        # 3. SQUAT (5 Progressionen, reps)
        squat, _ = Exercise.objects.get_or_create(
            name='Squat',
            defaults={'category': 'PUSH', 'description': 'Leg exercise', 'order': 3}
        )
        Progression.objects.filter(exercise=squat).delete()
        Progression.objects.bulk_create([
            Progression(exercise=squat, level=1, name='Assisted Squat', description='Mit Unterstützung', target_type='reps', target_value=15, sets_required=3, sessions_required=3),
            Progression(exercise=squat, level=2, name='Bodyweight Squat', description='Standard Bodyweight Squat', target_type='reps', target_value=15, sets_required=3, sessions_required=3),
            Progression(exercise=squat, level=3, name='Reverse Lunge Squat', description='Zurücklunges zum Squat', target_type='reps', target_value=12, sets_required=3, sessions_required=3),
            Progression(exercise=squat, level=4, name='Bulgarian Split Squat', description='Bulgarian Split Squat', target_type='reps', target_value=10, sets_required=3, sessions_required=3),
            Progression(exercise=squat, level=5, name='Pistol Squat', description='Einbeinen Pistol Squat', target_type='reps', target_value=5, sets_required=3, sessions_required=3),
        ])
        self.stdout.write('✓ Squat (5 progressions)')

        # 4. LUNGE (4 Progressionen, reps)
        lunge, _ = Exercise.objects.get_or_create(
            name='Lunge',
            defaults={'category': 'PUSH', 'description': 'Leg exercise', 'order': 4}
        )
        Progression.objects.filter(exercise=lunge).delete()
        Progression.objects.bulk_create([
            Progression(exercise=lunge, level=1, name='Forward Lunge', description='Vorne Ausfallschritt', target_type='reps', target_value=12, sets_required=3, sessions_required=3),
            Progression(exercise=lunge, level=2, name='Walking Lunge', description='Gehender Ausfallschritt', target_type='reps', target_value=10, sets_required=3, sessions_required=3),
            Progression(exercise=lunge, level=3, name='Reverse Lunge', description='Rückwärts Ausfallschritt', target_type='reps', target_value=10, sets_required=3, sessions_required=3),
            Progression(exercise=lunge, level=4, name='Bulgarian Split Squat', description='Bulgarian Split Squat Lunge', target_type='reps', target_value=8, sets_required=3, sessions_required=3),
        ])
        self.stdout.write('✓ Lunge (4 progressions)')

        # 5. HANGING KNEE RAISE (4 Progressionen, reps)
        hkr, _ = Exercise.objects.get_or_create(
            name='Hanging Knee Raise',
            defaults={'category': 'PULL', 'description': 'Core exercise', 'order': 5}
        )
        Progression.objects.filter(exercise=hkr).delete()
        Progression.objects.bulk_create([
            Progression(exercise=hkr, level=1, name='Tuck Hold', description='Tuck Hold Position 15s', target_type='hold', target_value=15, sets_required=3, sessions_required=3),
            Progression(exercise=hkr, level=2, name='Knee Raise', description='Hängende Knie heben', target_type='reps', target_value=10, sets_required=3, sessions_required=3),
            Progression(exercise=hkr, level=3, name='Alternating Knee Raise', description='Alternierend Knie heben', target_type='reps', target_value=8, sets_required=3, sessions_required=3),
            Progression(exercise=hkr, level=4, name='Double Knee Raise', description='Doppelte Knie heben', target_type='reps', target_value=8, sets_required=3, sessions_required=3),
        ])
        self.stdout.write('✓ Hanging Knee Raise (4 progressions)')

        # 6. HOLLOW HOLD (3 Progressionen, hold)
        hollow, _ = Exercise.objects.get_or_create(
            name='Hollow Hold',
            defaults={'category': 'PUSH', 'description': 'Core skill', 'order': 6}
        )
        Progression.objects.filter(exercise=hollow).delete()
        Progression.objects.bulk_create([
            Progression(exercise=hollow, level=1, name='Hollow Body Hold', description='Hollow Body 20s', target_type='hold', target_value=20, sets_required=3, sessions_required=3),
            Progression(exercise=hollow, level=2, name='Hollow Rock', description='Hollow Body Rock', target_type='reps', target_value=10, sets_required=3, sessions_required=3),
            Progression(exercise=hollow, level=3, name='Advanced Hollow Hold', description='Advanced Hollow Hold 30s', target_type='hold', target_value=30, sets_required=3, sessions_required=3),
        ])
        self.stdout.write('✓ Hollow Hold (3 progressions)')

        self.stdout.write(self.style.SUCCESS('✓ Successfully seeded 6 exercises!'))
