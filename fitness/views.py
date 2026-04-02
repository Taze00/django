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


class UserProgressionViewSet(viewsets.ModelViewSet):
    """User's current progression levels"""
    serializer_class = UserProgressionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserExerciseProgression.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """Update current progression level and training days"""
        progression = self.get_object()
        print(f"DEBUG UPDATE: request.data = {request.data}")

        # Update progression if provided
        if 'current_progression' in request.data:
            try:
                prog_id = request.data['current_progression']
                progression_obj = Progression.objects.get(id=prog_id)
                progression.current_progression = progression_obj
                print(f"DEBUG: Updated {progression.exercise.name} to progression {prog_id}")
            except Progression.DoesNotExist:
                return Response({'error': 'Invalid progression'}, status=status.HTTP_400_BAD_REQUEST)

        # Update training days if provided
        if 'training_days' in request.data:
            progression.training_days = request.data['training_days']
            print(f"DEBUG: Updated training days to {request.data['training_days']}")
        else:
            print(f"DEBUG: No training_days in request.data!")

        progression.save()
        print(f"DEBUG: After save - training_days = {progression.training_days}")
        return Response(UserProgressionSerializer(progression).data)


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
        drop_set_completed = request.data.get('drop_set_completed', False)
        print(f'DEBUG: drop_set_completed={drop_set_completed}, is_drop_set={is_drop_set}')

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
                'drop_set_completed': drop_set_completed,
            }
        )

        serializer = WorkoutSetSerializer(workout_set)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        """Reset today's workout - delete entire workout"""
        workout = self.get_object()
        workout.delete()
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
        'onboarding_completed': profile.onboarding_completed if profile else False,
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_onboarding(request):
    """Mark onboarding as complete and ensure all progressions exist"""
    print(f"DEBUG: complete_onboarding called for user {request.user.username}")
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    # Get training days from existing progressions (set during onboarding)
    first_progression = UserExerciseProgression.objects.filter(user=request.user).first()
    training_days = first_progression.training_days if first_progression else [1, 2, 3, 4, 5]
    print(f"DEBUG: Training days found: {training_days}")

    # Ensure all exercise progressions exist for the user (but don't overwrite existing ones)
    for exercise in Exercise.objects.all():
        start_progression = exercise.progressions.filter(user_starts_here=True).first()
        if start_progression:
            UserExerciseProgression.objects.get_or_create(
                user=request.user,
                exercise=exercise,
                defaults={
                    'current_progression': start_progression,
                    'training_days': training_days,
                }
            )

    # Update profile with training days from progressions
    profile.training_days = training_days
    profile.onboarding_completed = True
    profile.save()
    print(f"DEBUG: Profile saved. training_days={profile.training_days}, onboarding_completed={profile.onboarding_completed}")

    serializer = UserProfileSerializer(profile)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_onboarding(request):
    """Reset onboarding and all user progress for the current user"""
    user = request.user

    try:
        # Mark onboarding as incomplete and reset training days
        profile = UserProfile.objects.get(user=user)
        profile.onboarding_completed = False
        profile.training_days = []
        profile.save()

        # Reset all exercise progressions to starting level
        for exercise in Exercise.objects.all():
            start_progression = exercise.progressions.filter(user_starts_here=True).first()
            if start_progression:
                user_prog, created = UserExerciseProgression.objects.get_or_create(
                    user=user,
                    exercise=exercise,
                    defaults={
                        'current_progression': start_progression,
                        'training_days': [1, 2, 3, 4, 5],
                    }
                )
                if not created:
                    user_prog.current_progression = start_progression
                    user_prog.sessions_at_target = 0
                    user_prog.custom_target = None
                    user_prog.is_first_session = True
                    user_prog.training_days = []
                    user_prog.save()

        # Delete all workouts
        Workout.objects.filter(user=user).delete()

        return Response({'status': 'onboarding_reset'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Failed to reset onboarding: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([])
def register(request):
    """
    Register a new user with a secret registration key.

    Request body:
    {
        "username": "newuser",
        "password": "secure_password",
        "email": "user@example.com",
        "registration_key": "your_secret_key"
    }
    """
    from django.conf import settings

    # Get the secret key from request
    provided_key = request.data.get('registration_key', '')
    secret_key = settings.REGISTRATION_SECRET_KEY

    # Check if registration key is correct
    if provided_key != secret_key:
        return Response(
            {'error': 'Invalid registration key'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get user data
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    email = request.data.get('email', '').strip()

    # Validation
    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(username) < 3:
        return Response(
            {'error': 'Username must be at least 3 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if user already exists
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already taken'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if email and User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already registered'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        # Create UserProfile for fitness app
        UserProfile.objects.create(user=user)

        # Initialize exercise progressions for new user
        for exercise in Exercise.objects.all():
            start_progression = exercise.progressions.filter(user_starts_here=True).first()
            if start_progression:
                UserExerciseProgression.objects.create(
                    user=user,
                    exercise=exercise,
                    current_progression=start_progression,
                    training_days=[1, 2, 3, 4, 5]  # Mon-Fri default
                )

        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'message': 'User created successfully! You can now login.'
            },
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {'error': f'Registration failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
