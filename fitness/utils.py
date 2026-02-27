from django.db.models import Q
from .models import UserExerciseProgression, WorkoutSet, Progression


def check_progression_upgrade(user, exercise):
    """
    Check if user should upgrade to next progression level.

    Rules for Progressive Overload:
    - User needs sessions_required (3) consecutive workouts where:
      * Set 1 >= effective_target AND Set 2 >= effective_target (BOTH must meet target individually)
      * Effective target = custom_target OR progression.target_value
      * Only non-drop-sets count (is_drop_set=False)
    - This is tracked in UserExerciseProgression.sessions_at_target counter
    - After completing a qualifying workout, sessions_at_target increments
    - When sessions_at_target >= sessions_required, user is ready to upgrade
    - After upgrade: is_first_session = True (enables downgrade check on next progression)

    Returns:
        dict: {
            'ready': bool,
            'next_progression': Progression or None,
            'message': str,
            'sessions_at_target': int,
            'sessions_required': int
        }
    """
    try:
        current_prog = UserExerciseProgression.objects.get(
            user=user,
            exercise=exercise
        )
    except UserExerciseProgression.DoesNotExist:
        return {
            'ready': False,
            'next_progression': None,
            'message': 'No progression found for this exercise',
            'sessions_at_target': 0,
            'sessions_required': 3
        }

    current_progression = current_prog.current_progression
    target_value = current_progression.target_value
    sessions_required = current_progression.sessions_required
    sessions_at_target = current_prog.sessions_at_target

    # Check if already ready for upgrade
    if sessions_at_target >= sessions_required:
        next_level = current_progression.level + 1
        try:
            next_progression = Progression.objects.get(
                exercise=exercise,
                level=next_level
            )
            return {
                'ready': True,
                'next_progression': next_progression,
                'message': f'Ready to upgrade to {next_progression.name}!',
                'sessions_at_target': sessions_at_target,
                'sessions_required': sessions_required
            }
        except Progression.DoesNotExist:
            return {
                'ready': False,
                'next_progression': None,
                'message': 'Already at maximum progression level',
                'sessions_at_target': sessions_at_target,
                'sessions_required': sessions_required
            }

    return {
        'ready': False,
        'next_progression': None,
        'message': f'Progress: {sessions_at_target}/{sessions_required} sessions at target',
        'sessions_at_target': sessions_at_target,
        'sessions_required': sessions_required
    }


def upgrade_progression(user, exercise, new_progression):
    """
    Upgrade user's progression for an exercise and reset sessions_at_target counter.
    Also set is_first_session = True to enable downgrade check on first session with new progression.
    """
    try:
        user_prog = UserExerciseProgression.objects.get(
            user=user,
            exercise=exercise
        )
        user_prog.current_progression = new_progression
        user_prog.sessions_at_target = 0  # Reset counter for new progression
        user_prog.custom_target = None  # Clear any previous custom target
        user_prog.is_first_session = True  # Enable downgrade check on first session
        user_prog.save()
        return True
    except UserExerciseProgression.DoesNotExist:
        return False
