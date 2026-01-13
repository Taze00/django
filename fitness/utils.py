from django.db.models import Q
from .models import UserExerciseProgression, WorkoutSet, Progression


def check_progression_upgrade(user, exercise):
    """
    Check if user should upgrade to next progression level.

    Rules:
    - Rep-based exercises: 3 workouts with 16+ reps on sets 1+2 combined (not including drop sets)
    - Time-based exercises: 3 workouts with target_seconds+ on sets 1+2 combined (not including drop sets)

    Returns:
        dict: {
            'ready': bool,
            'next_progression': Progression or None,
            'message': str,
            'qualifying_workouts': int,
            'average_reps_or_seconds': float
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
            'qualifying_workouts': 0,
            'average_reps_or_seconds': 0
        }

    # Determine target based on exercise type
    is_timed = exercise.is_timed
    target_value = current_prog.current_progression.target_seconds or 30 if is_timed else 8

    # Get last 3 completed workouts for this exercise
    # Only look at non-drop-set sets (is_drop_set=False)
    last_workouts = []

    # Get distinct workouts with this exercise
    workouts = user.workouts.filter(
        sets__exercise=exercise,
        completed=True
    ).distinct().order_by('-date')[:5]  # Get last 5 to be safe

    # For each workout, check if it qualifies based on exercise type
    for workout in workouts:
        sets = workout.sets.filter(
            exercise=exercise,
            is_drop_set=False
        ).order_by('set_number')[:2]  # Only get first 2 sets

        if is_timed:
            # For time-based exercises: sum the seconds from set 1 and 2
            total_value = sum(s.seconds or 0 for s in sets)
        else:
            # For rep-based exercises: sum the reps from set 1 and 2
            total_value = sum(s.reps or 0 for s in sets)

        # Check if it qualifies
        if len(sets) == 2 and total_value >= target_value * 2:  # Need 2x target for both sets
            last_workouts.append({
                'workout': workout,
                'value': total_value
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
            avg_value = sum(w['value'] for w in last_workouts) / len(last_workouts)
            return {
                'ready': True,
                'next_progression': next_progression,
                'message': f'Ready to upgrade to {next_progression.name}!',
                'qualifying_workouts': len(last_workouts),
                'average_reps_or_seconds': round(avg_value, 1)
            }
        except Progression.DoesNotExist:
            return {
                'ready': False,
                'next_progression': None,
                'message': 'Already at maximum progression level',
                'qualifying_workouts': len(last_workouts),
                'average_reps_or_seconds': 0
            }

    avg_value = sum(w['value'] for w in last_workouts) / len(last_workouts) if last_workouts else 0
    return {
        'ready': False,
        'next_progression': None,
        'message': f'Need {3 - len(last_workouts)} more qualifying workouts',
        'qualifying_workouts': len(last_workouts),
        'average_reps_or_seconds': round(avg_value, 1)
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
