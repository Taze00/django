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
    UserSerializer, ExerciseSerializer, ProgressionSerializer,
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
    filterset_fields = ['date', 'workout_type', 'completed']

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

        # Determine workout type based on day
        # Mo=PUSH, Tu=PULL, We=PUSH, Th=PULL, Fr=PUSH, Sa/Su=REST
        workout_types = {
            0: 'PUSH',  # Monday
            1: 'PULL',  # Tuesday
            2: 'PUSH',  # Wednesday
            3: 'PULL',  # Thursday
            4: 'PUSH',  # Friday
            5: None,    # Saturday - no workout
            6: None,    # Sunday - no workout
        }

        workout_type = workout_types.get(today_day)

        if not workout_type:
            return Response(
                {'error': 'No workout scheduled for today'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create workout
        workout, created = Workout.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={
                'workout_type': workout_type,
                'week_number': 1,  # TODO: Calculate actual week number
            }
        )

        # Create warmup if not exists
        if not hasattr(workout, 'warmup'):
            WarmupChecklist.objects.create(workout=workout)

        serializer = WorkoutDetailSerializer(workout)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark workout as completed"""
        from django.db.models import Sum, Count

        workout = self.get_object()
        workout.completed = True
        workout.completed_at = timezone.now()

        # Calculate duration if we have set times
        if workout.sets.exists():
            duration = (workout.completed_at - workout.created_at).total_seconds()
            workout.duration_seconds = int(duration)

        workout.save()

        # Check for progression upgrades
        exercises = Exercise.objects.all()
        upgrades = []
        for exercise in exercises:
            result = check_progression_upgrade(request.user, exercise)
            if result['ready']:
                # Get current progression
                user_prog = UserExerciseProgression.objects.get(
                    user=request.user,
                    exercise=exercise
                )
                current_prog = user_prog.current_progression
                next_prog = result['next_progression']

                # Calculate average reps from last qualifying workouts
                last_3_workouts = request.user.workouts.filter(
                    sets__exercise=exercise,
                    completed=True
                ).distinct().order_by('-date')[:3]

                total_reps = 0
                set_count = 0
                for w in last_3_workouts:
                    sets = w.sets.filter(
                        exercise=exercise,
                        is_drop_set=False
                    ).order_by('set_number')[:2]
                    for s in sets:
                        total_reps += s.reps
                        set_count += 1

                avg_reps = total_reps / set_count if set_count > 0 else 0

                upgrades.append({
                    'exercise_id': exercise.id,
                    'exercise_name': exercise.name,
                    'old_progression': {
                        'id': current_prog.id,
                        'level': current_prog.level,
                        'name': current_prog.name,
                        'description': current_prog.description,
                    },
                    'new_progression': {
                        'id': next_prog.id,
                        'level': next_prog.level,
                        'name': next_prog.name,
                        'description': next_prog.description,
                    },
                    'qualifying_workouts': 3,
                    'average_reps': avg_reps,
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


class WorkoutSetViewSet(viewsets.ModelViewSet):
    """Manage workout sets"""
    serializer_class = WorkoutSetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkoutSet.objects.filter(workout__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class UserViewSet(viewsets.GenericViewSet):
    """User management"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user info"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class StatsViewSet(viewsets.GenericViewSet):
    """Statistics and analytics"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get overall statistics"""
        from django.db.models import Sum, Count, Q

        user_workouts = request.user.workouts.all()
        completed_workouts = user_workouts.filter(completed=True)

        # Total workouts
        total_workouts = completed_workouts.count()

        # Total time (sum of duration_seconds)
        total_time_result = completed_workouts.aggregate(Sum('duration_seconds'))
        total_time_seconds = total_time_result['duration_seconds__sum'] or 0

        # Total reps (sum of all reps)
        total_reps_result = WorkoutSet.objects.filter(
            workout__user=request.user,
            workout__completed=True
        ).aggregate(Sum('reps'))
        total_reps = total_reps_result['reps__sum'] or 0

        # Current streak (consecutive days with completed workouts)
        current_streak = 0
        if completed_workouts.exists():
            today = timezone.now().date()
            check_date = today

            while True:
                if not completed_workouts.filter(date=check_date).exists():
                    break
                current_streak += 1
                check_date -= timedelta(days=1)

        # Count push vs pull workouts
        push_workouts = completed_workouts.filter(workout_type='PUSH').count()
        pull_workouts = completed_workouts.filter(workout_type='PULL').count()

        return Response({
            'total_workouts': total_workouts,
            'total_time_seconds': int(total_time_seconds),
            'total_reps': total_reps,
            'current_streak': current_streak,
            'push_workouts': push_workouts,
            'pull_workouts': pull_workouts,
        })

    @action(detail=False, methods=['get'])
    def exercise_progress(self, request):
        """Get time-series data for exercise progress"""
        exercise_id = request.query_params.get('exercise_id')
        days = int(request.query_params.get('days', 30))

        if not exercise_id:
            return Response(
                {'error': 'exercise_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            exercise = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
            return Response(
                {'error': 'Exercise not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get user's current progression for this exercise
        try:
            user_progression = UserExerciseProgression.objects.get(
                user=request.user,
                exercise=exercise
            )
            current_progression_name = user_progression.current_progression.name
        except UserExerciseProgression.DoesNotExist:
            current_progression_name = 'Unknown'

        # Get data points from last N days
        start_date = timezone.now().date() - timedelta(days=days)
        workouts = request.user.workouts.filter(
            date__gte=start_date,
            completed=True,
            sets__exercise=exercise
        ).distinct().order_by('date')

        data_points = []
        for workout in workouts:
            sets = workout.sets.filter(
                exercise=exercise,
                is_drop_set=False
            ).order_by('set_number')[:2]

            if sets.count() == 2:
                set1_reps = sets[0].reps
                set2_reps = sets[1].reps
                total_reps = set1_reps + set2_reps

                data_points.append({
                    'date': workout.date.isoformat(),
                    'set1_reps': set1_reps,
                    'set2_reps': set2_reps,
                    'total_reps': total_reps,
                })

        return Response({
            'exercise_name': exercise.name,
            'current_progression': current_progression_name,
            'data_points': data_points,
        })

    @action(detail=False, methods=['get'])
    def progression_history(self, request):
        """Get progression upgrade history for an exercise"""
        exercise_id = request.query_params.get('exercise_id')

        if not exercise_id:
            return Response(
                {'error': 'exercise_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            exercise = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
            return Response(
                {'error': 'Exercise not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            user_progression = UserExerciseProgression.objects.get(
                user=request.user,
                exercise=exercise
            )
        except UserExerciseProgression.DoesNotExist:
            return Response(
                {'exercise_name': exercise.name, 'progressions': []}
            )

        # Get all progressions for this exercise (ordered by level)
        all_progressions = Progression.objects.filter(
            exercise=exercise
        ).order_by('level')

        progressions_data = []
        current_progression_level = user_progression.current_progression.level

        for progression in all_progressions:
            # Find workouts where this was the user's progression
            # (based on dates and progression levels)
            workouts_at_level = request.user.workouts.filter(
                completed=True,
                sets__exercise=exercise,
            ).distinct()

            # Count workouts at this progression
            workout_count = 0
            first_date = None
            last_date = None

            for workout in workouts_at_level:
                # Check if this workout had this progression
                sets = workout.sets.filter(exercise=exercise)
                if sets.exists():
                    # Simple heuristic: if current progression matches, count it
                    if progression.level <= current_progression_level:
                        if first_date is None:
                            first_date = workout.date
                        last_date = workout.date
                        workout_count += 1

            if progression.level == current_progression_level:
                # Current progression - no end date
                progressions_data.append({
                    'progression_name': progression.name,
                    'level': progression.level,
                    'started_at': first_date.isoformat() if first_date else None,
                    'ended_at': None,
                    'total_workouts': workout_count,
                })
            elif progression.level < current_progression_level:
                # Past progression
                progressions_data.append({
                    'progression_name': progression.name,
                    'level': progression.level,
                    'started_at': first_date.isoformat() if first_date else None,
                    'ended_at': last_date.isoformat() if last_date else None,
                    'total_workouts': workout_count,
                })

        return Response({
            'exercise_name': exercise.name,
            'progressions': progressions_data,
        })
