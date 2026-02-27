from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


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
    is_timed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'order']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Progression(models.Model):
    """Different progression levels for each exercise"""
    TARGET_TYPE_CHOICES = [
        ('reps', 'Reps'),
        ('time', 'Time (Seconds)'),
    ]

    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='progressions')
    level = models.IntegerField()
    order = models.IntegerField(default=0)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)

    form_cues = models.JSONField(default=list)
    common_mistakes = models.JSONField(default=list)
    tips = models.TextField(blank=True)

    target_type = models.CharField(max_length=10, choices=TARGET_TYPE_CHOICES, default='reps')
    target_value = models.IntegerField(default=10)
    sets_required = models.IntegerField(default=2)
    sessions_required = models.IntegerField(default=3)

    user_starts_here = models.BooleanField(default=False)

    class Meta:
        ordering = ['exercise', 'order']
        unique_together = ['exercise', 'level']

    def __str__(self):
        return f"{self.exercise.name} - {self.name}"


class UserProfile(models.Model):
    """Extended user profile for fitness app"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fitness_profile')
    current_week = models.IntegerField(default=1)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Fitness Profile: {self.user.username}"

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_profile = UserProfile.objects.get(pk=self.pk)
                if old_profile.avatar and old_profile.avatar != self.avatar:
                    if os.path.isfile(old_profile.avatar.path):
                        os.remove(old_profile.avatar.path)
            except UserProfile.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class UserExerciseProgression(models.Model):
    """Track current progression level for each user/exercise"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_progressions')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    current_progression = models.ForeignKey(Progression, on_delete=models.CASCADE)
    sessions_at_target = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'exercise']

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name}: {self.current_progression.name}"


class Workout(models.Model):
    """Workout session"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workouts')
    date = models.DateField(default=timezone.now)
    completed = models.BooleanField(default=False)
    duration_seconds = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date}"


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
    set_number = models.IntegerField()
    reps = models.IntegerField(null=True, blank=True)
    seconds = models.IntegerField(null=True, blank=True)
    is_drop_set = models.BooleanField(default=False)
    drop_set_data = models.JSONField(null=True, blank=True)
    rest_time_seconds = models.IntegerField(default=180)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['set_number']

    def __str__(self):
        if self.seconds is not None:
            mins = self.seconds // 60
            secs = self.seconds % 60
            return f"{self.workout} - {self.exercise.name} Set {self.set_number}: {mins}:{secs:02d}"
        return f"{self.workout} - {self.exercise.name} Set {self.set_number}: {self.reps} reps"
