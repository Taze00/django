from django.core.management.base import BaseCommand
from fitness.models import Exercise, Progression


class Command(BaseCommand):
    help = 'Seed the database with calisthenics exercises and progressions'

    def handle(self, *args, **options):
        self.stdout.write('Seeding exercises and progressions...')

        # PUSH EXERCISES
        # 1. Push-ups
        pushups, created = Exercise.objects.get_or_create(
            name='Push-ups',
            defaults={
                'category': 'PUSH',
                'description': 'Horizontal pushing exercise',
                'order': 1,
            }
        )
        if created:
            self.stdout.write(f'Created exercise: {pushups.name}')
            Progression.objects.bulk_create([
                Progression(exercise=pushups, level=1, name='Wall Push-ups', description='Push-ups against a wall'),
                Progression(exercise=pushups, level=2, name='Knie Push-ups', description='Push-ups on knees'),
                Progression(exercise=pushups, level=3, name='Incline Push-ups', description='Push-ups on elevated surface'),
                Progression(exercise=pushups, level=4, name='Standard Push-ups', description='Regular push-ups'),
                Progression(exercise=pushups, level=5, name='Decline Push-ups', description='Push-ups with feet elevated'),
                Progression(exercise=pushups, level=6, name='Pseudo Planche Push-ups', description='Advanced horizontal push'),
            ])

        # 2. Pike Push-ups
        pike, created = Exercise.objects.get_or_create(
            name='Pike Push-ups',
            defaults={
                'category': 'PUSH',
                'description': 'Shoulder focusing vertical push',
                'order': 2,
            }
        )
        if created:
            self.stdout.write(f'Created exercise: {pike.name}')
            Progression.objects.bulk_create([
                Progression(exercise=pike, level=1, name='Pike Hold', description='Static hold in pike position (30s)'),
                Progression(exercise=pike, level=2, name='Pike Push-ups (wide)', description='Pike push-ups with wider stance'),
                Progression(exercise=pike, level=3, name='Pike Push-ups (narrow)', description='Pike push-ups with narrow stance'),
                Progression(exercise=pike, level=4, name='Elevated Pike Push-ups', description='Pike push-ups with feet elevated'),
                Progression(exercise=pike, level=5, name='Box Pike Push-ups', description='Pike push-ups with hands elevated'),
            ])

        # 3. Planche Lean
        planche, created = Exercise.objects.get_or_create(
            name='Planche Lean',
            defaults={
                'category': 'PUSH',
                'description': 'Advanced strength skill work for planche',
                'order': 3,
            }
        )
        if created:
            self.stdout.write(f'Created exercise: {planche.name}')
            Progression.objects.bulk_create([
                Progression(exercise=planche, level=1, name='Plank with Protraction', description='Plank with shoulder blade protraction (30s)'),
                Progression(exercise=planche, level=2, name='Planche Lean (light)', description='Light planche lean hold'),
                Progression(exercise=planche, level=3, name='Planche Lean (advanced)', description='Advanced planche lean hold'),
                Progression(exercise=planche, level=4, name='Straddle Planche Lean', description='Planche lean with straddle legs'),
            ])

        # PULL EXERCISES
        # 4. Pull-ups
        pullups, created = Exercise.objects.get_or_create(
            name='Pull-ups',
            defaults={
                'category': 'PULL',
                'description': 'Vertical pulling exercise',
                'order': 4,
            }
        )
        if created:
            self.stdout.write(f'Created exercise: {pullups.name}')
            Progression.objects.bulk_create([
                Progression(exercise=pullups, level=1, name='Dead Hangs', description='Hang from bar (30s)'),
                Progression(exercise=pullups, level=2, name='Scapular Shrugs', description='Shoulder shrugs on bar'),
                Progression(exercise=pullups, level=3, name='Active Hangs', description='Engaged hanging position'),
                Progression(exercise=pullups, level=4, name='Pull-up Negatives', description='Negative pull-ups (5s descent)'),
                Progression(exercise=pullups, level=5, name='Band-Assisted Pull-ups', description='Pull-ups with resistance band assistance'),
                Progression(exercise=pullups, level=6, name='Jumping Pull-ups', description='Explosive pull-ups with jump'),
                Progression(exercise=pullups, level=7, name='Standard Pull-ups', description='Unassisted pull-ups'),
            ])

        # 5. Rows
        rows, created = Exercise.objects.get_or_create(
            name='Rows',
            defaults={
                'category': 'PULL',
                'description': 'Horizontal pulling exercise',
                'order': 5,
            }
        )
        if created:
            self.stdout.write(f'Created exercise: {rows.name}')
            Progression.objects.bulk_create([
                Progression(exercise=rows, level=1, name='Table Rows (bent)', description='Rows under table with bent knees'),
                Progression(exercise=rows, level=2, name='Table Rows (straight)', description='Rows under table with straight legs'),
                Progression(exercise=rows, level=3, name='Elevated Rows', description='Rows with feet elevated'),
                Progression(exercise=rows, level=4, name='Band-Assisted Rows', description='Rows with band assistance'),
            ])

        # 6. Hanging Leg Raises
        leg_raises, created = Exercise.objects.get_or_create(
            name='Hanging Leg Raises',
            defaults={
                'category': 'PULL',
                'description': 'Core and hip flexor exercise',
                'order': 6,
            }
        )
        if created:
            self.stdout.write(f'Created exercise: {leg_raises.name}')
            Progression.objects.bulk_create([
                Progression(exercise=leg_raises, level=1, name='Knee Raises (single)', description='Single leg knee raises'),
                Progression(exercise=leg_raises, level=2, name='Knee Raises (both)', description='Both legs knee raises'),
                Progression(exercise=leg_raises, level=3, name='Leg Raises (bent)', description='Leg raises with bent knees'),
                Progression(exercise=leg_raises, level=4, name='Leg Raises (straight)', description='Straight leg raises'),
                Progression(exercise=leg_raises, level=5, name='L-Sit Hold', description='L-sit hold position'),
            ])

        self.stdout.write(self.style.SUCCESS('Successfully seeded exercises and progressions'))
