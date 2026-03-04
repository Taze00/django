from django.core.management.base import BaseCommand
from workout.models import Exercise, Progression


class Command(BaseCommand):
    help = 'Seed exercises and progressions into the database'

    def handle(self, *args, **options):
        self.stdout.write('Seeding exercises...')

        # Lösche bestehende Daten (optional)
        # Exercise.objects.all().delete()

        # ============ PUSH-UPS ============
        pushup, _ = Exercise.objects.get_or_create(
            name='Push-ups',
            defaults={'description': 'Upper body pushing movement'},
        )

        pushup_progressions = [
            {'level': 1, 'name': 'Wall Push-ups', 'target_type': 'reps', 'target_value': 8, 'user_starts_here': False},
            {'level': 2, 'name': 'Incline Push-ups', 'target_type': 'reps', 'target_value': 8, 'user_starts_here': False},
            {'level': 3, 'name': 'Knee Push-ups', 'target_type': 'reps', 'target_value': 8, 'user_starts_here': True},
            {'level': 4, 'name': 'Standard Push-ups', 'target_type': 'reps', 'target_value': 8, 'user_starts_here': False},
            {'level': 5, 'name': 'Diamond Push-ups', 'target_type': 'reps', 'target_value': 6, 'user_starts_here': False},
            {'level': 6, 'name': 'Decline Push-ups', 'target_type': 'reps', 'target_value': 6, 'user_starts_here': False},
            {'level': 7, 'name': 'Pseudo Planche Push-ups', 'target_type': 'reps', 'target_value': 5, 'user_starts_here': False},
        ]

        for prog_data in pushup_progressions:
            Progression.objects.update_or_create(
                exercise=pushup,
                level=prog_data['level'],
                defaults={
                    'name': prog_data['name'],
                    'target_type': prog_data['target_type'],
                    'target_value': prog_data['target_value'],
                    'sessions_required': 3,
                    'user_starts_here': prog_data['user_starts_here'],
                },
            )

        # ============ PULL-UPS ============
        pullup, _ = Exercise.objects.get_or_create(
            name='Pull-ups',
            defaults={'description': 'Upper body pulling movement'},
        )

        pullup_progressions = [
            {'level': 1, 'name': 'Dead Hang', 'target_type': 'time', 'target_value': 30, 'user_starts_here': True},
            {'level': 2, 'name': 'Scapular Shrugs', 'target_type': 'reps', 'target_value': 10, 'user_starts_here': False},
            {'level': 3, 'name': 'Active Hang', 'target_type': 'time', 'target_value': 20, 'user_starts_here': False},
            {'level': 4, 'name': 'Pull-up Negatives', 'target_type': 'reps', 'target_value': 5, 'user_starts_here': False},
            {'level': 5, 'name': 'Band-Assisted Pull-ups', 'target_type': 'reps', 'target_value': 8, 'user_starts_here': False},
            {'level': 6, 'name': 'Standard Pull-ups', 'target_type': 'reps', 'target_value': 5, 'user_starts_here': False},
            {'level': 7, 'name': 'Chest-to-Bar', 'target_type': 'reps', 'target_value': 5, 'user_starts_here': False},
        ]

        for prog_data in pullup_progressions:
            Progression.objects.update_or_create(
                exercise=pullup,
                level=prog_data['level'],
                defaults={
                    'name': prog_data['name'],
                    'target_type': prog_data['target_type'],
                    'target_value': prog_data['target_value'],
                    'sessions_required': 3,
                    'user_starts_here': prog_data['user_starts_here'],
                },
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded exercises!'))
