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

        # 2-Exercise Schedule: Mo/We/Fr = Push-ups+Pull-ups, Tu/Th = Pull-ups, Sa/Su = Rest
        schedule = {
            0: ['Push-ups', 'Pull-ups'],     # Monday
            1: ['Pull-ups'],                 # Tuesday
            2: ['Push-ups', 'Pull-ups'],     # Wednesday
            3: ['Pull-ups'],                 # Thursday
            4: ['Push-ups', 'Pull-ups'],     # Friday
            5: [],                           # Saturday - no workout
            6: [],                           # Sunday - no workout
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
            sets__workout=workout
        ).distinct()

        upgrades = []

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
                target_value = progression.target_value
                target_type = progression.target_type

                # Get values for Set 1 and Set 2
                if target_type == 'time':
                    set1_value = set1.seconds or 0
                    set2_value = set2.seconds or 0
                else:  # 'reps'
                    set1_value = set1.reps or 0
                    set2_value = set2.reps or 0

                # Check if BOTH Set 1 AND Set 2 meet or exceed target
                if set1_value >= target_value and set2_value >= target_value:
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

        return Response({
            'success': True,
            'workout': WorkoutDetailSerializer(workout).data,
            'upgrades': upgrades
        })

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
        
        exercise_id = request.data.get('exercise_id')
        progression_id = request.data.get('progression_id')
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
            defaults={
                'progression': progression,
                'reps': reps,
                'seconds': seconds,
                'is_drop_set': is_drop_set,
                'drop_set_data': drop_set_data,
            }
        )

        serializer = WorkoutSetSerializer(workout_set)
        return Response(serializer.data)
