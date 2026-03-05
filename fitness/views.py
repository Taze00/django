from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from fitness.models import Exercise, Progression, UserExerciseProgression, Workout, WorkoutSet, WarmupChecklist
from fitness.serializers import (
    ExerciseSerializer, UserProgressionSerializer, WorkoutSerializer, 
    WorkoutSetSerializer, WarmupChecklistSerializer
)


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """List all exercises with progressions (public endpoint)"""
    queryset = Exercise.objects.prefetch_related('progressions')
    serializer_class = ExerciseSerializer
    permission_classes = []


class UserProgressionViewSet(viewsets.ReadOnlyModelViewSet):
    """User's current progression levels"""
    serializer_class = UserProgressionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserExerciseProgression.objects.filter(user=self.request.user)


class WorkoutViewSet(viewsets.ModelViewSet):
    """Workout management - create, track sets, complete workout"""
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get or create today's workout"""
        today = timezone.now().date()
        workout, created = Workout.objects.get_or_create(
            user=request.user,
            date=today
        )
        serializer = self.get_serializer(workout)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_set(self, request, pk=None):
        """Add or update a set in the workout"""
        workout = self.get_object()
        
        exercise_id = request.data.get('exercise')
        progression_id = request.data.get('progression')
        set_number = request.data.get('set_number')
        reps = request.data.get('reps')
        seconds = request.data.get('seconds')
        rest_time_seconds = request.data.get('rest_time_seconds', 180)
        is_drop_set = request.data.get('is_drop_set', False)

        try:
            exercise = Exercise.objects.get(id=exercise_id)
            progression = Progression.objects.get(id=progression_id)
        except (Exercise.DoesNotExist, Progression.DoesNotExist):
            return Response({'error': 'Invalid exercise or progression'}, status=status.HTTP_400_BAD_REQUEST)

        workout_set, created = WorkoutSet.objects.update_or_create(
            workout=workout,
            exercise=exercise,
            set_number=set_number,
            is_drop_set=is_drop_set,
            defaults={
                'progression': progression,
                'reps': reps,
                'seconds': seconds,
                'rest_time_seconds': rest_time_seconds,
            }
        )

        serializer = WorkoutSetSerializer(workout_set)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete workout and check for upgrades/downgrades"""
        workout = self.get_object()
        workout.completed = True
        workout.completed_at = timezone.now()
        workout.save()

        upgrades = []
        downgrades = []

        # Check each exercise for upgrades/downgrades
        for exercise in Exercise.objects.all():
            user_prog = UserExerciseProgression.objects.filter(
                user=request.user,
                exercise=exercise
            ).first()

            if not user_prog:
                continue

            # Get Set 1 and Set 2 (not Set 3 Drop-Set)
            set1 = WorkoutSet.objects.filter(
                workout=workout,
                exercise=exercise,
                set_number=1,
                is_drop_set=False
            ).first()

            set2 = WorkoutSet.objects.filter(
                workout=workout,
                exercise=exercise,
                set_number=2,
                is_drop_set=False
            ).first()

            if not set1 or not set2:
                continue

            # Get values based on progression type
            if user_prog.current_progression.target_type == 'reps':
                val1 = set1.reps or 0
                val2 = set2.reps or 0
            else:
                val1 = set1.seconds or 0
                val2 = set2.seconds or 0

            effective_target = user_prog.effective_target

            # CHECK DOWNGRADE (only if first session at this level)
            if user_prog.is_first_session and user_prog.current_progression.level > 1:
                if user_prog.current_progression.target_type == 'reps':
                    should_downgrade = val1 < 3 or (val1 + val2) < 5
                else:
                    should_downgrade = val1 < (effective_target // 3) or (val1 + val2) < (effective_target // 2)

                if should_downgrade:
                    prev_progression = Progression.objects.filter(
                        exercise=exercise,
                        level=user_prog.current_progression.level - 1
                    ).first()

                    if prev_progression:
                        adjustment = 0
                        if user_prog.current_progression.target_type == 'reps':
                            if val1 == 0:
                                adjustment = 6
                            elif val1 == 1:
                                adjustment = 4
                            elif val1 == 2:
                                adjustment = 2
                        else:
                            if val1 == 0:
                                adjustment = 15
                            elif val1 < 6:
                                adjustment = 10
                            elif val1 < 11:
                                adjustment = 5

                        user_prog.current_progression = prev_progression
                        user_prog.custom_target = prev_progression.target_value + adjustment
                        user_prog.sessions_at_target = 0
                        user_prog.is_first_session = False
                        user_prog.save()

                        downgrades.append({
                            'exercise': exercise.name,
                            'from_level': user_prog.current_progression.level + 1,
                            'to_level': prev_progression.level,
                            'to_progression': prev_progression.name,
                        })
                        continue

            # CHECK UPGRADE (if target reached)
            if val1 >= effective_target and val2 >= effective_target:
                user_prog.sessions_at_target += 1

                if user_prog.sessions_at_target >= user_prog.current_progression.sessions_required:
                    # Only upgrade if not at max level (7)
                    if user_prog.current_progression.level < 7:
                        next_progression = Progression.objects.filter(
                            exercise=exercise,
                            level=user_prog.current_progression.level + 1
                        ).first()

                        if next_progression:
                            user_prog.current_progression = next_progression
                            user_prog.sessions_at_target = 0
                            user_prog.custom_target = None
                            user_prog.is_first_session = True
                            user_prog.save()

                            upgrades.append({
                                'exercise': exercise.name,
                                'from_level': user_prog.current_progression.level - 1,
                                'to_level': next_progression.level,
                                'to_progression': next_progression.name,
                            })
                    else:
                        # Already at max level
                        user_prog.sessions_at_target = 0  # Reset but stay at level
                        user_prog.save()
                        upgrades.append({
                            'exercise': exercise.name,
                            'is_max_level': True,
                            'message': f'You've reached the maximum level for {exercise.name}! Keep crushing it! 💪',
                        })
                else:
                    user_prog.save()
            else:
                # Did not reach target, but mark first session as done
                user_prog.is_first_session = False
                user_prog.save()

        return Response({
            'status': 'completed',
            'upgrades': upgrades,
            'downgrades': downgrades,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def last_performance(self, request):
        """Get last recorded values for each exercise"""
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)

        last_workout = Workout.objects.filter(
            user=request.user,
            date__lt=today
        ).order_by('-date').first()

        if not last_workout:
            return Response({}, status=status.HTTP_200_OK)

        last_sets = {}
        for exercise in Exercise.objects.all():
            set1 = WorkoutSet.objects.filter(
                workout=last_workout,
                exercise=exercise,
                set_number=1,
                is_drop_set=False
            ).first()

            if set1:
                last_sets[str(exercise.id)] = {
                    'exercise_id': exercise.id,
                    'exercise_name': exercise.name,
                    'set1_reps': set1.reps,
                    'set1_seconds': set1.seconds,
                }

        return Response(last_sets, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'])
    def warmup(self, request, pk=None):
        """Update warmup checklist"""
        workout = self.get_object()

        warmup, created = WarmupChecklist.objects.get_or_create(workout=workout)
        serializer = WarmupChecklistSerializer(warmup, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
