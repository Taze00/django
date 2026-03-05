import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meinprojekt.settings')

import django
django.setup()

from django.contrib.auth.models import User
from fitness.models import Exercise, UserExerciseProgression

# Create test user
User.objects.filter(username='test').delete()
user = User.objects.create_user('test', 'test@test.com', 'test123')
print(f'✅ User created: {user.username}')

# Initialize progressions for both exercises
for exercise in Exercise.objects.all():
    start_prog = exercise.progressions.filter(user_starts_here=True).first()
    if start_prog:
        UserExerciseProgression.objects.get_or_create(
            user=user,
            exercise=exercise,
            defaults={'current_progression': start_prog}
        )
        print(f'✅ {exercise.name} → {start_prog.name}')
