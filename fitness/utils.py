from django.db.models import Q
from .models import UserExerciseProgression, WorkoutSet, Progression


def check_progression_upgrade(user, exercise):
    """
    Check if user should upgrade to next progression level.
    Rule: 3 workouts with 16+ reps on sets 1+2 combined (not including drop sets)

    Returns:
        dict: {
            'ready': bool,
            'next_progression': Progression or None,
            'message': str
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
            'message': 'No progression found for this exercise'
        }

    # Get last 3 completed workouts for this exercise
    # Only look at non-drop-set sets (is_drop_set=False)
    last_workouts = []
    from django.db.models import Sum

    # Get distinct workouts with this exercise
    workouts = user.workouts.filter(
        sets__exercise=exercise,
        completed=True
    ).distinct().order_by('-date')[:5]  # Get last 5 to be safe

    # For each workout, sum the reps from set 1 and 2 (non-drop-set)
    for workout in workouts:
        sets = workout.sets.filter(
            exercise=exercise,
            is_drop_set=False
        ).order_by('set_number')[:2]  # Only get first 2 sets

        total_reps = sum(s.reps for s in sets)

        if len(sets) == 2 and total_reps >= 16:
            last_workouts.append({
                'workout': workout,
                'reps': total_reps
            })

    # Check if we have 3 qualifying workouts
    if len(last_workouts) >= 3:
        # Get next progression
        next_level = current_prog.current_progression.level + 1
        try:
            next_progression = Progression.objects.get(
                exercise=exercise,
                level=next_level
            )
            return {
                'ready': True,
                'next_progression': next_progression,
                'message': f'Ready to upgrade to {next_progression.name}!'
            }
        except Progression.DoesNotExist:
            return {
                'ready': False,
                'next_progression': None,
                'message': 'Already at maximum progression level'
            }

    return {
        'ready': False,
        'next_progression': None,
        'message': f'Need {3 - len(last_workouts)} more qualifying workouts'
    }


def upgrade_progression(user, exercise, new_progression):
    """
    Upgrade user's progression for an exercise
    """
    try:
        user_prog = UserExerciseProgression.objects.get(
            user=user,
            exercise=exercise
        )
        user_prog.current_progression = new_progression
        user_prog.save()
        return True
    except UserExerciseProgression.DoesNotExist:
        return False
