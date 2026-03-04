from .models import UserExerciseProgression, Progression


def get_effective_target(user_prog):
    """Gibt das effektive Target zurück (custom_target oder default)."""
    return user_prog.custom_target or user_prog.current_progression.target_value


def check_progression_upgrade(user, exercise):
    """
    Prüft ob ein Upgrade verfügbar ist.
    Returns: {'ready': bool, 'next_progression': Progression or None}
    """
    try:
        user_prog = UserExerciseProgression.objects.get(user=user, exercise=exercise)
    except UserExerciseProgression.DoesNotExist:
        return {'ready': False, 'next_progression': None}

    if user_prog.sessions_at_target >= user_prog.current_progression.sessions_required:
        # Versuche nächste Progression zu finden
        next_prog = Progression.objects.filter(
            exercise=exercise, level=user_prog.current_progression.level + 1
        ).first()
        if next_prog:
            return {'ready': True, 'next_progression': next_prog}

    return {'ready': False, 'next_progression': None}


def upgrade_progression(user, exercise, next_progression):
    """
    Führt ein Upgrade durch.
    Setzt: current_progression, sessions_at_target=0, custom_target=None, is_first_session=True
    """
    user_prog = UserExerciseProgression.objects.get(user=user, exercise=exercise)
    user_prog.current_progression = next_progression
    user_prog.sessions_at_target = 0
    user_prog.custom_target = None
    user_prog.is_first_session = True  # Ermöglicht Downgrade-Check in der nächsten Session!
    user_prog.save()


def check_and_perform_downgrade(user, exercise, set1_value, set2_value):
    """
    Prüft ob ein Downgrade nötig ist und führt ihn durch (nur wenn is_first_session=True).
    Returns: {'downgraded': bool, 'details': {...}}
    """
    try:
        user_prog = UserExerciseProgression.objects.get(user=user, exercise=exercise)
    except UserExerciseProgression.DoesNotExist:
        return {'downgraded': False, 'details': {}}

    # Downgrade nur möglich wenn is_first_session=True und level > 1
    if not user_prog.is_first_session or user_prog.current_progression.level == 1:
        user_prog.is_first_session = False
        user_prog.save()
        return {'downgraded': False, 'details': {}}

    progression = user_prog.current_progression
    target_type = progression.target_type
    effective_target = get_effective_target(user_prog)

    should_downgrade = False

    if target_type == 'reps':
        # Downgrade wenn: set1 < 3 OR (set1 + set2) < 5
        if set1_value < 3 or (set1_value + set2_value) < 5:
            should_downgrade = True
    else:  # time
        # Downgrade wenn: set1 < target/3 OR (set1 + set2) < target/2
        if set1_value < (effective_target / 3) or (set1_value + set2_value) < (effective_target / 2):
            should_downgrade = True

    if should_downgrade:
        # Downgrade durchführen
        prev_progression = Progression.objects.filter(
            exercise=exercise, level=progression.level - 1
        ).first()

        if prev_progression:
            # Berechne new_custom_target basierend auf set1_value
            if set1_value == 0:
                adjustment = 6
            elif set1_value == 1:
                adjustment = 4
            elif set1_value == 2:
                adjustment = 2
            else:
                adjustment = 0  # Sollte nicht vorkommen wenn should_downgrade=True

            new_custom_target = min(effective_target + adjustment, 20)

            user_prog.current_progression = prev_progression
            user_prog.custom_target = new_custom_target
            user_prog.sessions_at_target = 0
            user_prog.is_first_session = False  # WICHTIG: Verhindert mehrfache Downgrades!
            user_prog.save()

            return {
                'downgraded': True,
                'details': {
                    'from_progression': progression.name,
                    'to_progression': prev_progression.name,
                    'new_custom_target': new_custom_target,
                }
            }

    # Kein Downgrade, aber is_first_session zurücksetzen
    user_prog.is_first_session = False
    user_prog.save()

    return {'downgraded': False, 'details': {}}
