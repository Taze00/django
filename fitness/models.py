from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Exercise(models.Model):
    """Base exercises (Push-ups, Pull-ups, etc.)"""
    CATEGORY_CHOICES = [
        ('PUSH', 'Push'),
        ('PULL', 'Pull'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0)  # Display order
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'order']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Progression(models.Model):
    """Different progression levels for each exercise"""
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='progressions')
    level = models.IntegerField()  # 1, 2, 3, etc.
    name = models.CharField(max_length=100)  # "Wall Push-ups", "Regular Push-ups", etc.
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['exercise', 'level']
        unique_together = ['exercise', 'level']

    def __str__(self):
        return f"{self.exercise.name} - Level {self.level}: {self.name}"


class UserProfile(models.Model):
    """Extended user profile for fitness app"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fitness_profile')
    current_week = models.IntegerField(default=1)  # Training week number
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Fitness Profile: {self.user.username}"


class UserExerciseProgression(models.Model):
    """Track current progression level for each user/exercise"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_progressions')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    current_progression = models.ForeignKey(Progression, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'exercise']

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name}: {self.current_progression.name}"


class Workout(models.Model):
    """Workout session"""
    WORKOUT_TYPE_CHOICES = [
        ('PUSH', 'Push'),
        ('PULL', 'Pull'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workouts')
    date = models.DateField(default=timezone.now)
    workout_type = models.CharField(max_length=20, choices=WORKOUT_TYPE_CHOICES)
    week_number = models.IntegerField()
    completed = models.BooleanField(default=False)
    duration_seconds = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['user', 'workout_type', '-date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_workout_type_display()} ({self.date})"


class WarmupChecklist(models.Model):
    """Warm-up completion tracking"""
    workout = models.OneToOneField(Workout, on_delete=models.CASCADE, related_name='warmup')
    wrists = models.BooleanField(default=False)
    shoulders = models.BooleanField(default=False)
    elbows = models.BooleanField(default=False)
    back = models.BooleanField(default=False)
    legs = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Warmup for {self.workout}"


class WorkoutSet(models.Model):
    """Individual sets within a workout"""
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='sets')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    progression = models.ForeignKey(Progression, on_delete=models.CASCADE)
    set_number = models.IntegerField()  # 1, 2, 3
    reps = models.IntegerField()
    is_drop_set = models.BooleanField(default=False)
    drop_set_progression = models.ForeignKey(
        Progression,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='drop_sets'
    )
    drop_set_reps = models.IntegerField(null=True, blank=True)
    rest_time_seconds = models.IntegerField(default=90)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['set_number']

    def __str__(self):
        return f"{self.workout} - {self.exercise.name} Set {self.set_number}: {self.reps} reps"
