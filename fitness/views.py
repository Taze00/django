from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from fitness.models import Exercise, Progression, UserExerciseProgression, Workout, WorkoutSet, WarmupChecklist, UserProfile
from fitness.serializers import (
    ExerciseSerializer, UserProgressionSerializer, WorkoutSerializer,
    WorkoutSetSerializer, WarmupChecklistSerializer, UserProfileSerializer
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
    def reset(self, request, pk=None):
        """Reset today's workout - delete all sets and reset status"""
        workout = self.get_object()
        workout.sets.all().delete()
        workout.completed = False
        workout.completed_at = None
        workout.save()
        return Response({'status': 'reset'}, status=status.HTTP_200_OK)

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
                            'message': f'You have reached the maximum level for {exercise.name}! Keep crushing it!',
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request):
    """Get current user details"""
    user = request.user
    profile = UserProfile.objects.filter(user=user).first()
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'profile_picture': profile.profile_picture.url if profile and profile.profile_picture else None,
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def upload_profile_picture(request):
    """Upload/update user profile picture - max 2MB"""
    if 'profile_picture' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['profile_picture']

    # Check file size (max 2MB)
    if file.size > 2 * 1024 * 1024:
        return Response({'error': 'File size exceeds 2MB limit'}, status=status.HTTP_400_BAD_REQUEST)

    # Check file type
    if not file.content_type.startswith('image/'):
        return Response({'error': 'File must be an image'}, status=status.HTTP_400_BAD_REQUEST)

    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Delete old picture explicitly if it exists
    if profile.profile_picture:
        profile.profile_picture.delete()

    # Save new picture
    profile.profile_picture = file
    profile.save()

    serializer = UserProfileSerializer(profile)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_profile_picture(request):
    """Delete user profile picture"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.profile_picture:
            profile.profile_picture.delete()
        profile.profile_picture = None
        profile.save()
        return Response({'status': 'deleted', 'profile_picture': None}, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_settings(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
