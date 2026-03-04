from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Q

from .models import Exercise, Progression, UserExerciseProgression, Workout, WorkoutSet
from .serializers import (
    ExerciseSerializer,
    UserExerciseProgressionSerializer,
    WorkoutDetailSerializer,
    WorkoutListSerializer,
    WorkoutSetSerializer,
)
from .utils import check_progression_upgrade, upgrade_progression, check_and_perform_downgrade, get_effective_target


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """Gibt alle Exercises mit Progressionen zurück."""
    queryset = Exercise.objects.prefetch_related('progressions').all()
    serializer_class = ExerciseSerializer
    permission_classes = [AllowAny]  # Keine Auth nötig


class UserProgressionViewSet(viewsets.ViewSet):
    """Gibt aktuelle Progressionen des Users zurück (String-Keys!)."""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user
        progressions = UserExerciseProgression.objects.filter(user=user).select_related(
            'exercise', 'current_progression'
        )

        # Normalisiere zu String-Keys!
        data = {}
        for prog in progressions:
            data[str(prog.exercise.id)] = UserExerciseProgressionSerializer(prog).data

        return Response(data)


class WorkoutViewSet(viewsets.ModelViewSet):
    """Workout CRUD + Complete Endpoint."""
    serializer_class = WorkoutDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user).prefetch_related('sets')

    def list(self, request):
        """Gib Liste der letzten 10 Workouts."""
        queryset = self.get_queryset().order_by('-created_at')[:10]
        serializer = WorkoutListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'post'])
    def current(self, request):
        """Hole aktives Workout oder erstelle eins."""
        if request.method == 'POST':
            # Erstelle neues Workout
            # Zuerst: stelle sicher dass User-Progressionen existieren
            exercises = Exercise.objects.all()
            for exercise in exercises:
                user_starts_prog = exercise.progressions.filter(user_starts_here=True).first()
                if user_starts_prog:
                    UserExerciseProgression.objects.get_or_create(
                        user=request.user,
                        exercise=exercise,
                        defaults={'current_progression': user_starts_prog},
                    )

            workout = Workout.objects.create(user=request.user)
            serializer = self.get_serializer(workout)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # GET: Hole aktives Workout (wo is_complete=False und heute erstellt)
        today = timezone.now().date()
        workout = Workout.objects.filter(
            user=request.user,
            is_complete=False,
            created_at__date=today,
        ).first()

        if not workout:
            return Response({'error': 'Kein aktives Workout'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(workout)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_set(self, request, pk=None):
        """Füge Set hinzu oder update existierendes (update_or_create)."""
        workout = self.get_object()

        exercise_id = request.data.get('exercise_id')
        progression_id = request.data.get('progression_id')
        set_number = request.data.get('set_number')
        reps = request.data.get('reps')
        seconds = request.data.get('seconds')
        is_drop_set = request.data.get('is_drop_set', False)

        try:
            exercise = Exercise.objects.get(id=exercise_id)
            progression = Progression.objects.get(id=progression_id)
        except (Exercise.DoesNotExist, Progression.DoesNotExist):
            return Response({'error': 'Exercise oder Progression nicht gefunden'}, status=status.HTTP_400_BAD_REQUEST)

        # Build defaults dict with only non-None values
        defaults = {
            'progression': progression,
            'is_drop_set': is_drop_set,
            'rest_time_seconds': 300 if set_number >= 3 else 180,
        }
        if reps is not None:
            defaults['reps'] = reps
        if seconds is not None:
            defaults['seconds'] = seconds

        # update_or_create: idempotent!
        workout_set, created = WorkoutSet.objects.update_or_create(
            workout=workout,
            exercise=exercise,
            set_number=set_number,
            defaults=defaults,
        )

        serializer = WorkoutSetSerializer(workout_set)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Workout abschließen + Upgrade/Downgrade Check."""
        workout = self.get_object()

        if workout.is_complete:
            return Response({'error': 'Workout ist bereits abgeschlossen'}, status=status.HTTP_400_BAD_REQUEST)

        workout.is_complete = True
        workout.completed_at = timezone.now()
        workout.save()

        upgrades = []
        downgrades = []

        # Für jede Übung: Upgrade/Downgrade Check
        exercises_in_workout = WorkoutSet.objects.filter(workout=workout).values('exercise').distinct()

        for exercise_data in exercises_in_workout:
            exercise_id = exercise_data['exercise']
            exercise = Exercise.objects.get(id=exercise_id)

            # Hole Set 1 und Set 2 (nicht Drop-Set!)
            set1 = WorkoutSet.objects.filter(workout=workout, exercise=exercise, set_number=1, is_drop_set=False).first()
            set2 = WorkoutSet.objects.filter(workout=workout, exercise=exercise, set_number=2, is_drop_set=False).first()

            if not (set1 and set2):
                continue  # Übung nicht komplett, überspringe

            # Get values for sets (handle None values)
            user_prog = UserExerciseProgression.objects.get(user=request.user, exercise=exercise)
            progression = user_prog.current_progression

            if progression.target_type == 'reps':
                set1_value = set1.reps or 0
                set2_value = set2.reps or 0
            else:  # time
                set1_value = set1.seconds or 0
                set2_value = set2.seconds or 0

            # Downgrade Check (nur wenn is_first_session=True)
            downgrade_result = check_and_perform_downgrade(
                request.user, exercise,
                set1_value,
                set2_value,
            )

            if downgrade_result['downgraded']:
                downgrades.append({
                    'exercise_id': exercise.id,
                    'exercise_name': exercise.name,
                    'progression_name': user_prog.current_progression.name,
                    'details': downgrade_result['details'],
                })
            else:
                # Upgrade Check (nur wenn kein Downgrade)
                effective_target = get_effective_target(user_prog)

                if set1_value >= effective_target and set2_value >= effective_target:
                    user_prog.sessions_at_target += 1
                    user_prog.save()

                    # Prüfe ob Upgrade bereit
                    upgrade_check = check_progression_upgrade(request.user, exercise)
                    if upgrade_check['ready']:
                        next_prog = upgrade_check['next_progression']
                        upgrade_progression(request.user, exercise, next_prog)
                        upgrades.append({
                            'exercise_id': exercise.id,
                            'exercise_name': exercise.name,
                            'from_progression': progression.name,
                            'to_progression': next_prog.name,
                            'new_progression_name': next_prog.name,
                            'sessions_at_target': user_prog.sessions_at_target,
                        })

        serializer = self.get_serializer(workout)
        return Response({
            'workout': serializer.data,
            'upgrades': upgrades,
            'downgrades': downgrades,
        })

    @action(detail=False, methods=['get'])
    def last_performance(self, request):
        """Gib letzte Performance pro Exercise/Progression/SetNumber zurück."""
        user = request.user

        # Finde letzte abgeschlossene Workouts pro Exercise
        last_sets = {}

        exercises = Exercise.objects.all()
        for exercise in exercises:
            user_prog = UserExerciseProgression.objects.filter(user=user, exercise=exercise).first()
            if not user_prog:
                continue

            for set_num in [1, 2, 3]:
                # Finde letztes WorkoutSet dieser Übung/SetNumber
                last_set = WorkoutSet.objects.filter(
                    exercise=exercise,
                    set_number=set_num,
                    workout__user=user,
                    workout__is_complete=True,
                ).order_by('-workout__completed_at').first()

                if last_set:
                    key = str(user_prog.current_progression.id)
                    if key not in last_sets:
                        last_sets[key] = {}
                    last_sets[key][f'set{set_num}'] = {
                        'reps': last_set.reps,
                        'seconds': last_set.seconds,
                        'is_drop_set': last_set.is_drop_set,
                    }

        return Response(last_sets)
