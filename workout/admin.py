from django.contrib import admin
from .models import Exercise, Progression, UserExerciseProgression, Workout, WorkoutSet

admin.site.register(Exercise)
admin.site.register(Progression)
admin.site.register(UserExerciseProgression)
admin.site.register(Workout)
admin.site.register(WorkoutSet)
