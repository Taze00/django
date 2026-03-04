from django.db import models
from django.contrib.auth.models import User


class Exercise(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Progression(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='progressions')
    level = models.IntegerField()
    name = models.CharField(max_length=100)
    target_type = models.CharField(max_length=10, choices=[('reps', 'Reps'), ('time', 'Time')])
    target_value = models.IntegerField()
    sessions_required = models.IntegerField(default=3)
    user_starts_here = models.BooleanField(default=False)

    class Meta:
        unique_together = ['exercise', 'level']
        ordering = ['exercise', 'level']

    def __str__(self):
        return f"{self.name} (L{self.level})"


class UserExerciseProgression(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    current_progression = models.ForeignKey(Progression, on_delete=models.CASCADE)
    sessions_at_target = models.IntegerField(default=0)
    custom_target = models.IntegerField(null=True, blank=True)
    is_first_session = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'exercise']

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} ({self.current_progression.name})"


class Workout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class WorkoutSet(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='sets')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    progression = models.ForeignKey(Progression, on_delete=models.CASCADE)
    set_number = models.IntegerField()  # 1, 2, or 3
    reps = models.IntegerField(null=True, blank=True)
    seconds = models.IntegerField(null=True, blank=True)
    is_drop_set = models.BooleanField(default=False)
    rest_time_seconds = models.IntegerField(default=180)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['workout', 'exercise', 'set_number']

    def __str__(self):
        return f"Set {self.set_number} - {self.exercise.name}"
