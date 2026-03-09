from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver
from PIL import Image, ImageOps
import os
import io
from django.core.files.base import ContentFile
from django.db.models import JSONField


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
    training_days = JSONField(default=list, help_text="Days to train: [1,2,3,4,5] = Mon-Fri")
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
    training_days = JSONField(default=list, help_text="Days to train: [1,2,3,4,5] = Mon-Fri")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = ["workout", "exercise", "set_number", "is_drop_set"]

    def __str__(self):
        return f"{self.workout} - {self.exercise.name} Set {self.set_number}"


class UserProfile(models.Model):
    """User profile with optional profile picture"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        null=True,
        blank=True
    )
    training_days = JSONField(default=list, help_text="Days to train: [1,2,3,4,5] = Mon-Fri")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

    def save(self, *args, **kwargs):
        # Delete old image if new one is uploaded
        if self.pk:
            try:
                old = UserProfile.objects.get(pk=self.pk)
                if old.profile_picture and old.profile_picture != self.profile_picture:
                    if os.path.exists(old.profile_picture.path):
                        os.remove(old.profile_picture.path)
            except UserProfile.DoesNotExist:
                pass

        # Compress and resize image if uploaded
        if self.profile_picture and (not self.pk or self.profile_picture.name != UserProfile.objects.get(pk=self.pk).profile_picture.name):
            img = Image.open(self.profile_picture)
            
            # Convert RGBA to RGB
            if img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = rgb_img

            # Resize to 400x400
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Save to bytes buffer instead of file
            img_io = io.BytesIO()
            img.save(img_io, format="JPEG", quality=85, optimize=True)
            img_io.seek(0)
            
            # Save bytes to field - use only filename to prevent duplication
            import os
            filename = os.path.basename(self.profile_picture.name)
            self.profile_picture.save(
                filename,
                ContentFile(img_io.getvalue()),
                save=False
            )

        super().save(*args, **kwargs)


@receiver(post_delete, sender=UserProfile)
def delete_profile_picture(sender, instance, **kwargs):
    """Delete profile picture file when UserProfile is deleted"""
    if instance.profile_picture:
        if os.path.exists(instance.profile_picture.path):
            os.remove(instance.profile_picture.path)
