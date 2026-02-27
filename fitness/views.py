from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Exercise, Progression, UserProfile, UserExerciseProgression,
    Workout, WarmupChecklist, WorkoutSet
)
from .serializers import (
    ExerciseSerializer, ProgressionSerializer,
    UserProfileSerializer, UserExerciseProgressionSerializer,
    WorkoutDetailSerializer, WorkoutListSerializer, WorkoutCreateSerializer,
    WarmupChecklistSerializer, WorkoutSetSerializer
)
from .utils import check_progression_upgrade, upgrade_progression


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve exercises with their progressions"""
    queryset = Exercise.objects.prefetch_related('progressions')
    serializer_class = ExerciseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        category = self.request.query_params.get('category')
        if category:
            return self.queryset.filter(category=category)
        return self.queryset


class ProgressionViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve exercise progressions"""
    queryset = Progression.objects.all()
    serializer_class = ProgressionSerializer
    permission_classes = [AllowAny]


class UserProfileViewSet(viewsets.GenericViewSet):
    """User profile management"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get', 'put'])
    def profile(self, request):
        """Get or update user profile"""
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        if request.method == 'PUT':
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get or update current user profile info"""
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        if request.method == 'PUT':
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def progressions(self, request):
        """Get all exercise progressions for current user"""
        progressions = UserExerciseProgression.objects.filter(
            user=request.user
        ).select_related('exercise', 'current_progression')
        serializer = UserExerciseProgressionSerializer(progressions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def check_upgrades(self, request):
        """Check all exercises for progression upgrades"""
        exercises = Exercise.objects.all()
        upgrades = []

        for exercise in exercises:
            result = check_progression_upgrade(request.user, exercise)
            if result['ready']:
                upgrades.append({
                    'exercise_id': exercise.id,
                    'exercise_name': exercise.name,
                    'current_progression': UserExerciseProgression.objects.get(
                        user=request.user,
                        exercise=exercise
                    ).current_progression.id,
                    'next_progression': result['next_progression'].id,
                    'next_progression_name': result['next_progression'].name,
                })

        return Response({'upgrades': upgrades})

    @action(detail=False, methods=['post'])
    def upgrade_progression(self, request):
        """Manually upgrade progression"""
        exercise_id = request.data.get('exercise_id')
        progression_id = request.data.get('progression_id')

        try:
            exercise = Exercise.objects.get(id=exercise_id)
            new_progression = Progression.objects.get(id=progression_id)

            if upgrade_progression(request.user, exercise, new_progression):
                return Response({
                    'success': True,
                    'message': f'Upgraded to {new_progression.name}'
                })
        except (Exercise.DoesNotExist, Progression.DoesNotExist):
            return Response(
                {'error': 'Exercise or progression not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {'error': 'Failed to upgrade progression'},
            status=status.HTTP_400_BAD_REQUEST
        )


class WorkoutViewSet(viewsets.ModelViewSet):
    """Manage workouts"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user).prefetch_related('sets', 'warmup')

    def get_serializer_class(self):
        if self.action == 'list':
            return WorkoutListSerializer
        elif self.action == 'create':
            return WorkoutCreateSerializer
        return WorkoutDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get or create today's workout"""
        today = timezone.now().date()
        today_day = today.weekday()  # 0=Monday, 1=Tuesday, etc.

        # 2-Exercise Schedule: Mo/We/Fr = Push-up+Pull-up, Tu/Th = Pull-up, Sa/Su = Rest
        schedule = {
            0: ['Push-up', 'Pull-up'],     # Monday
            1: ['Pull-up'],                 # Tuesday
            2: ['Push-up', 'Pull-up'],     # Wednesday
            3: ['Pull-up'],                 # Thursday
            4: ['Push-up', 'Pull-up'],     # Friday
            5: [],                          # Saturday - no workout
            6: [],                          # Sunday - no workout
        }

        scheduled_exercise_names = schedule.get(today_day, [])

        if not scheduled_exercise_names:
            return Response(
                {'error': 'No workout scheduled for today'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create workout
        workout, created = Workout.objects.get_or_create(
            user=request.user,
            date=today
        )

        # Create warmup if not exists
        if not hasattr(workout, 'warmup'):
            WarmupChecklist.objects.create(workout=workout)

        # Initialize UserExerciseProgressions for new users
        # Start with user_starts_here=True progressions only
        exercises = Exercise.objects.all().prefetch_related('progressions')
        for exercise in exercises:
            # Find the starting progression first
            start_progression = exercise.progressions.filter(
                user_starts_here=True
            ).first()

            if not start_progression:
                # Fallback to first progression if no user_starts_here marked
                start_progression = exercise.progressions.order_by('level').first()

            if start_progression:
                # Create or get with the starting progression
                uep, created = UserExerciseProgression.objects.get_or_create(
                    user=request.user,
                    exercise=exercise,
                    defaults={
                        'current_progression': start_progression,
                        'sessions_at_target': 0
                    }
                )

        serializer = WorkoutDetailSerializer(workout)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def last_performance(self, request):
        """Get last set values for each exercise/progression"""
        user_progressions = UserExerciseProgression.objects.filter(
            user=request.user
        ).select_related('exercise', 'current_progression')

        last_performances = {}

        for uep in user_progressions:
            # Get last set for this progression
            last_set = WorkoutSet.objects.filter(
                exercise=uep.exercise,
                progression=uep.current_progression,
                is_drop_set=False
            ).order_by('-created_at').first()

            if last_set:
                last_performances[uep.current_progression.id] = {
                    'exercise_id': uep.exercise.id,
                    'progression_id': uep.current_progression.id,
                    'last_reps': last_set.reps,
                    'last_seconds': last_set.seconds,
                    'created_at': last_set.created_at,
                }

        return Response(last_performances)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark workout as completed"""
        workout = self.get_object()
        workout.completed = True
        workout.completed_at = timezone.now()

        if workout.sets.exists():
            duration = (workout.completed_at - workout.created_at).total_seconds()
            workout.duration_seconds = int(duration)

        workout.save()

        # Check progression qualifying for each exercise in this workout
        exercises_in_workout = Exercise.objects.filter(
            workoutset__workout=workout
        ).distinct()

        upgrades = []
        downgrades = []

        for exercise in exercises_in_workout:
            # Get Set 1 and Set 2 (non-drop-sets only)
            sets_1_2 = workout.sets.filter(
                exercise=exercise,
                is_drop_set=False
            ).order_by('set_number')[:2]

            # Only process if we have both sets
            if sets_1_2.count() == 2:
                set1, set2 = sets_1_2[0], sets_1_2[1]

                try:
                    user_prog = UserExerciseProgression.objects.get(
                        user=request.user,
                        exercise=exercise
                    )
                except UserExerciseProgression.DoesNotExist:
                    continue

                progression = user_prog.current_progression
                effective_target = user_prog.custom_target or progression.target_value
                target_type = progression.target_type

                # Get values for Set 1 and Set 2
                if target_type == 'time':
                    set1_value = set1.seconds or 0
                    set2_value = set2.seconds or 0
                else:  # 'reps'
                    set1_value = set1.reps or 0
                    set2_value = set2.reps or 0

                # Check if BOTH Set 1 AND Set 2 meet or exceed effective target
                if set1_value >= effective_target and set2_value >= effective_target:
                    # Qualifies! Increment sessions_at_target
                    user_prog.sessions_at_target += 1
                    user_prog.save()

                    # Check if ready for upgrade
                    result = check_progression_upgrade(request.user, exercise)
                    if result['ready']:
                        next_prog = result['next_progression']
                        upgrades.append({
                            'exercise_id': exercise.id,
                            'exercise_name': exercise.name,
                            'old_progression': {
                                'id': progression.id,
                                'level': progression.level,
                                'name': progression.name,
                                'description': progression.description,
                            },
                            'new_progression': {
                                'id': next_prog.id,
                                'level': next_prog.level,
                                'name': next_prog.name,
                                'description': next_prog.description,
                            },
                            'sessions_at_target': user_prog.sessions_at_target,
                            'sessions_required': progression.sessions_required,
                        })
                else:
                    # Failed to meet target on first session after upgrade
                    if user_prog.is_first_session and progression.level > 1:
                        # Perform downgrade check
                        downgrade_result = self._check_and_perform_downgrade(
                            user_prog, set1_value, set2_value, target_type
                        )
                        if downgrade_result:
                            downgrades.append(downgrade_result)

        return Response({
            'success': True,
            'workout': WorkoutDetailSerializer(workout).data,
            'upgrades': upgrades,
            'downgrades': downgrades
        })

    def _check_and_perform_downgrade(self, user_prog, set1_value, set2_value, target_type):
        """
        Check if downgrade is needed based on first session performance.

        Reps-based downgrade:
        - set1 < 3 OR (set1 + set2) < 5

        Time-based downgrade:
        - set1 < target/3 OR total < target/2

        Adjustment:
        - 0 reps: +6, 1 rep: +4, 2 reps: +2 (capped at 20)
        - Time follows same relative logic
        """
        progression = user_prog.current_progression
        target_value = progression.target_value

        should_downgrade = False

        if target_type == 'reps':
            # Check reps-based conditions
            if set1_value < 3 or (set1_value + set2_value) < 5:
                should_downgrade = True
                # Calculate custom target adjustment
                if set1_value == 0:
                    adjustment = 6
                elif set1_value == 1:
                    adjustment = 4
                elif set1_value == 2:
                    adjustment = 2
                else:
                    adjustment = 0

                new_target = min(target_value - adjustment, 20)
        else:  # time
            # Check time-based conditions
            total_seconds = set1_value + set2_value
            if set1_value < (target_value / 3) or total_seconds < (target_value / 2):
                should_downgrade = True
                # Similar adjustment logic
                if set1_value == 0:
                    adjustment = target_value // 3
                elif set1_value < (target_value / 6):
                    adjustment = target_value // 6
                else:
                    adjustment = 0

                new_target = max(target_value - adjustment, 5)

        if should_downgrade:
            user_prog.custom_target = new_target
            user_prog.is_first_session = False
            user_prog.save()

            return {
                'exercise_id': user_prog.exercise.id,
                'exercise_name': user_prog.exercise.name,
                'progression_id': progression.id,
                'progression_name': progression.name,
                'old_target': target_value,
                'new_target': new_target,
                'reason': 'adaptive_downgrade'
            }
        else:
            # Met target or beyond on first session - mark as no longer first session
            user_prog.is_first_session = False
            user_prog.save()

        return None

    @action(detail=True, methods=['get', 'put'])
    def warmup(self, request, pk=None):
        """Get or update warmup checklist"""
        workout = self.get_object()

        try:
            warmup = workout.warmup
        except WarmupChecklist.DoesNotExist:
            warmup = WarmupChecklist.objects.create(workout=workout)

        if request.method == 'PUT':
            serializer = WarmupChecklistSerializer(warmup, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = WarmupChecklistSerializer(warmup)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_set(self, request, pk=None):
        """Add a set to the workout"""
        workout = self.get_object()

        exercise_id = request.data.get('exercise')
        progression_id = request.data.get('progression')
        set_number = request.data.get('set_number')
        reps = request.data.get('reps')
        seconds = request.data.get('seconds')
        is_drop_set = request.data.get('is_drop_set', False)
        drop_set_data = request.data.get('drop_set_data')

        try:
            exercise = Exercise.objects.get(id=exercise_id)
            progression = Progression.objects.get(id=progression_id)
        except (Exercise.DoesNotExist, Progression.DoesNotExist):
            return Response(
                {'error': 'Exercise or progression not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create or update the set
        workout_set, created = WorkoutSet.objects.update_or_create(
            workout=workout,
            exercise=exercise,
            set_number=set_number,
            is_drop_set=is_drop_set,
            defaults={
                'progression': progression,
                'reps': reps,
                'seconds': seconds,
                'drop_set_data': drop_set_data,
            }
        )

        serializer = WorkoutSetSerializer(workout_set)
        return Response(serializer.data)

class UserExerciseProgressionViewSet(viewsets.ModelViewSet):
    """User exercise progression management"""
    queryset = UserExerciseProgression.objects.all()
    serializer_class = UserExerciseProgressionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only show progressions for the current user"""
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_progression(self, request, pk=None):
        """Manually set user to a specific progression level"""
        user_prog = self.get_object()
        
        # Check that the progression belongs to the same exercise
        progression_id = request.data.get('progression_id')
        
        try:
            progression = Progression.objects.get(
                id=progression_id,
                exercise=user_prog.exercise
            )
        except Progression.DoesNotExist:
            return Response(
                {'error': 'Invalid progression for this exercise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the user progression
        user_prog.current_progression = progression
        user_prog.sessions_at_target = 0  # Reset progress to new level
        user_prog.custom_target = None
        user_prog.is_first_session = True
        user_prog.save()
        
        serializer = UserExerciseProgressionSerializer(user_prog)
        return Response(serializer.data)
