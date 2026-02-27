from rest_framework import serializers
from .models import (
    UserProfile, Exercise, Progression, UserExerciseProgression,
    Workout, WarmupChecklist, WorkoutSet
)


class UserProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        """Return full absolute URL for avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    class Meta:
        model = UserProfile
        fields = ['id', 'user_id', 'username', 'avatar', 'current_week', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'username', 'created_at', 'updated_at']


class WarmupChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarmupChecklist
        fields = ['id', 'workout', 'wrists', 'shoulders', 'elbows', 'back', 'legs', 'completed_at']
        read_only_fields = ['id']


class ProgressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progression
        fields = ['id', 'exercise', 'level', 'name', 'description', 'target_type', 'target_value', 'sets_required', 'sessions_required', 'form_cues', 'common_mistakes', 'tips']
        read_only_fields = ['id']


class ExerciseSerializer(serializers.ModelSerializer):
    progressions = ProgressionSerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'category', 'description', 'order', 'progressions']
        read_only_fields = ['id']


class UserExerciseProgressionSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    current_progression_details = ProgressionSerializer(source='current_progression', read_only=True)

    class Meta:
        model = UserExerciseProgression
        fields = ['id', 'user', 'exercise', 'exercise_name', 'current_progression', 'current_progression_details', 'sessions_at_target']
        read_only_fields = ['id', 'user', 'exercise_name', 'current_progression_details']


class WorkoutSetSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    progression_name = serializers.CharField(source='progression.name', read_only=True)

    class Meta:
        model = WorkoutSet
        fields = ['id', 'workout', 'exercise', 'exercise_name', 'progression', 'progression_name', 'set_number', 'reps', 'seconds', 'is_drop_set', 'drop_set_data', 'rest_time_seconds', 'notes']
        read_only_fields = ['id']


class WorkoutListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['id', 'user', 'date', 'completed', 'completed_at', 'duration_seconds']
        read_only_fields = ['id', 'user']


class WorkoutDetailSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, read_only=True)
    warmup = WarmupChecklistSerializer(read_only=True)

    class Meta:
        model = Workout
        fields = ['id', 'user', 'date', 'completed', 'completed_at', 'duration_seconds', 'notes', 'sets', 'warmup']
        read_only_fields = ['id', 'user', 'created_at']


class WorkoutCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['user', 'date', 'notes']
        read_only_fields = ['user']
