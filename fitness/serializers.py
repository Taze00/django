from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Exercise, Progression, UserProfile, UserExerciseProgression,
    Workout, WarmupChecklist, WorkoutSet
)


class UserProfileMinimalSerializer(serializers.ModelSerializer):
    """Minimal profile serializer to avoid circular references"""
    class Meta:
        model = UserProfile
        fields = ['id', 'current_week', 'avatar', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined', 'profile']

    def get_profile(self, obj):
        try:
            profile = UserProfile.objects.get(user=obj)
            return UserProfileMinimalSerializer(profile).data
        except UserProfile.DoesNotExist:
            return None


class ProgressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progression
        fields = ['id', 'exercise', 'level', 'name', 'description', 'video_url', 'target_seconds']
        read_only_fields = ['id']


class ExerciseSerializer(serializers.ModelSerializer):
    progressions = ProgressionSerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'category', 'description', 'video_url', 'is_timed', 'order', 'progressions']
        read_only_fields = ['id']


class UserExerciseProgressionSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    progression_name = serializers.CharField(source='current_progression.name', read_only=True)
    progression_level = serializers.IntegerField(source='current_progression.level', read_only=True)

    class Meta:
        model = UserExerciseProgression
        fields = ['id', 'user', 'exercise', 'exercise_name', 'current_progression', 'progression_name', 'progression_level', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    exercise_progressions = UserExerciseProgressionSerializer(many=True, read_only=True, source='user.exercise_progressions')

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'current_week', 'avatar', 'exercise_progressions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class WarmupChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarmupChecklist
        fields = ['id', 'workout', 'wrists', 'shoulders', 'elbows', 'back', 'legs', 'completed_at']
        read_only_fields = ['id']


class WorkoutSetSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    progression_name = serializers.CharField(source='progression.name', read_only=True)
    drop_set_progression_name = serializers.CharField(source='drop_set_progression.name', read_only=True, allow_null=True)

    class Meta:
        model = WorkoutSet
        fields = [
            'id', 'workout', 'exercise', 'exercise_name', 'progression', 'progression_name',
            'set_number', 'reps', 'seconds', 'is_drop_set', 'drop_set_progression', 'drop_set_progression_name',
            'drop_set_reps', 'drop_set_seconds', 'rest_time_seconds', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WorkoutDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    sets = WorkoutSetSerializer(many=True, read_only=True)
    warmup = WarmupChecklistSerializer(read_only=True)

    class Meta:
        model = Workout
        fields = [
            'id', 'user', 'date', 'workout_type', 'week_number', 'completed',
            'duration_seconds', 'notes', 'sets', 'warmup', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'completed_at']


class WorkoutListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = [
            'id', 'date', 'workout_type', 'week_number', 'completed',
            'duration_seconds', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']


class WorkoutCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['date', 'workout_type', 'week_number']
