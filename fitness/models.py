from django.db import models
from django.contrib.auth.models import User


class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ("PUSH", "Push"),
        ("PULL", "Pull"),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Progression(models.Model):
    TYPE_CHOICES = [
        ("reps", "Reps"),
        ("time", "Time (seconds)"),
    ]

    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="progressions")
    level = models.IntegerField()
    name = models.CharField(max_length=100)
    target_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="reps")
    target_value = models.IntegerField(default=8)
    sets_required = models.IntegerField(default=2)
    sessions_required = models.IntegerField(default=3)
    user_starts_here = models.BooleanField(default=False)

    class Meta:
        ordering = ["exercise", "level"]
        unique_together = ["exercise", "level"]

    def __str__(self):
        return f"{self.exercise.name} - Level {self.level}: {self.name}"


class UserExerciseProgression(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="exercise_progressions")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    current_progression = models.ForeignKey(Progression, on_delete=models.PROTECT)
    sessions_at_target = models.IntegerField(default=0)
    custom_target = models.IntegerField(null=True, blank=True)
    is_first_session = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "exercise"]

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} ({self.current_progression.name})"

    @property
    def effective_target(self):
        if self.custom_target is not None:
            return self.custom_target
        return self.current_progression.target_value


class Workout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workouts")
    date = models.DateField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ["user", "date"]

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class WarmupChecklist(models.Model):
    workout = models.OneToOneField(Workout, on_delete=models.CASCADE, related_name="warmup_checklist")
    wrists = models.BooleanField(default=False)
    shoulders = models.BooleanField(default=False)
    elbows = models.BooleanField(default=False)
    back = models.BooleanField(default=False)
    legs = models.BooleanField(default=False)

    def __str__(self):
        return f"Warmup for {self.workout}"


class WorkoutSet(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="sets")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    progression = models.ForeignKey(Progression, on_delete=models.PROTECT)
    set_number = models.IntegerField()
    reps = models.IntegerField(null=True, blank=True)
    seconds = models.IntegerField(null=True, blank=True)
    is_drop_set = models.BooleanField(default=False)
    rest_time_seconds = models.IntegerField(default=180)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = ["workout", "exercise", "set_number", "is_drop_set"]

    def __str__(self):
        return f"{self.workout} - {self.exercise.name} Set {self.set_number}"
