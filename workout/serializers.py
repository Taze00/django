from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Exercise, Progression, UserExerciseProgression, Workout, WorkoutSet


class ProgressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progression
        fields = ['id', 'level', 'name', 'target_type', 'target_value', 'sessions_required', 'user_starts_here']


class ExerciseSerializer(serializers.ModelSerializer):
    progressions = ProgressionSerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'description', 'progressions']


class UserExerciseProgressionSerializer(serializers.ModelSerializer):
    exercise_id = serializers.IntegerField(source='exercise.id', read_only=True)
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    current_progression = ProgressionSerializer(read_only=True)
    current_progression_id = serializers.IntegerField(source='current_progression.id', read_only=True)

    class Meta:
        model = UserExerciseProgression
        fields = [
            'exercise_id',
            'exercise_name',
            'current_progression',
            'current_progression_id',
            'sessions_at_target',
            'custom_target',
            'is_first_session',
        ]


class WorkoutSetSerializer(serializers.ModelSerializer):
    exercise_id = serializers.IntegerField(source='exercise.id', read_only=True)
    progression_id = serializers.IntegerField(source='progression.id', read_only=True)

    class Meta:
        model = WorkoutSet
        fields = ['id', 'exercise_id', 'progression_id', 'set_number', 'reps', 'seconds', 'is_drop_set', 'rest_time_seconds']


class WorkoutDetailSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, read_only=True)

    class Meta:
        model = Workout
        fields = ['id', 'user', 'created_at', 'completed_at', 'is_complete', 'sets']


class WorkoutListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['id', 'created_at', 'completed_at', 'is_complete']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
