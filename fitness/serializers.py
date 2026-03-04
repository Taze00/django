from rest_framework import serializers
from fitness.models import Exercise, Progression, UserExerciseProgression, Workout, WorkoutSet, WarmupChecklist


class ProgressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progression
        fields = ['id', 'level', 'name', 'target_type', 'target_value', 'user_starts_here']


class ExerciseSerializer(serializers.ModelSerializer):
    progressions = ProgressionSerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'category', 'progressions']


class UserProgressionSerializer(serializers.ModelSerializer):
    current_progression = ProgressionSerializer(read_only=True)
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    effective_target = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserExerciseProgression
        fields = ['id', 'exercise', 'exercise_name', 'current_progression', 'sessions_at_target', 
                  'custom_target', 'is_first_session', 'effective_target']


class WorkoutSetSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    progression_name = serializers.CharField(source='progression.name', read_only=True)

    class Meta:
        model = WorkoutSet
        fields = ['id', 'exercise', 'exercise_name', 'progression', 'progression_name', 
                  'set_number', 'reps', 'seconds', 'is_drop_set', 'rest_time_seconds']


class WarmupChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarmupChecklist
        fields = ['wrists', 'shoulders', 'elbows', 'back', 'legs']


class WorkoutSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, read_only=True)
    warmup_checklist = WarmupChecklistSerializer(read_only=True)

    class Meta:
        model = Workout
        fields = ['id', 'date', 'completed', 'completed_at', 'duration_seconds', 'sets', 'warmup_checklist']
