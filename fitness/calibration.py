"""
CORVIS Onboarding Calibration
==============================

Hybrid calibration: the user self-assesses a level, performs ONE max test set,
and CORVIS adjusts the starting level up or down based on how the test result
compares to that level's own target value.

Design principles (researched, multi-source):
- A single max test set is a stronger signal than the first of 3 training
  sessions, so we measure against the app's OWN target values (no foreign
  numbers like "12 reps") to stay consistent with the training logic.
- Hold exercises (plank/hang, seconds) use the same ratio logic as rep
  exercises — confirmed consistent with Cali Move benchmarks (30s beginner,
  60s intermediate).
- We bias slightly conservative: you must MEET the target to stay on the
  self-assessed level; falling short drops you down so nobody starts too high
  and gets frustrated.

The ratio = test_result / target_value drives the adjustment:

    ratio < 0.5    -> 2 levels down   (far below target)
    0.5 <= r < 1.0 -> 1 level down    (just short)
    1.0 <= r < 2.0 -> stay            (target met)
    2.0 <= r < 3.0 -> 1 level up       (well above)
    ratio >= 3.0   -> 2 levels up      (far above)

The result is always clamped to the exercise's available level range (1..max).
"""

# Adjustment thresholds as (ratio_lower_bound, level_delta), checked top-down.
# ratio = test_result / target_value
_ADJUSTMENT_BANDS = [
    (3.0, +2),
    (2.0, +1),
    (1.0, 0),
    (0.5, -1),
    (0.0, -2),
]


def _level_delta_for_ratio(ratio):
    """Return how many levels to shift based on the performance ratio."""
    for lower_bound, delta in _ADJUSTMENT_BANDS:
        if ratio >= lower_bound:
            return delta
    return -2


def calibrate_level(progressions, self_assessed_level, test_result):
    """
    Compute the calibrated starting level for one exercise.

    Args:
        progressions: iterable of Progression objects for ONE exercise.
                      Each must have `.level` and `.target_value`.
        self_assessed_level: int — the level the user picked for themselves.
        test_result: int — reps or seconds the user achieved in the test set.

    Returns:
        dict with:
          - calibrated_level: int (clamped to available range)
          - self_assessed_level: int (echoed back, clamped)
          - delta: int (levels moved: negative=down, positive=up)
          - target_value: int (the target of the self-assessed level)
          - test_result: int (echoed back)
          - reason: str — short human explanation key
    """
    progs = sorted(progressions, key=lambda p: p.level)
    if not progs:
        raise ValueError("No progressions provided for calibration")

    levels = [p.level for p in progs]
    min_level, max_level = levels[0], levels[-1]

    # Clamp self-assessment into the valid range first.
    assessed = max(min_level, min(self_assessed_level, max_level))

    # Find the target value for the self-assessed level.
    target_prog = next((p for p in progs if p.level == assessed), None)
    if target_prog is None:
        # Fallback: nearest available level.
        target_prog = min(progs, key=lambda p: abs(p.level - assessed))
        assessed = target_prog.level

    target_value = target_prog.target_value or 1
    result = max(0, int(test_result))

    ratio = result / target_value if target_value else 0
    delta = _level_delta_for_ratio(ratio)

    calibrated = max(min_level, min(assessed + delta, max_level))
    actual_delta = calibrated - assessed

    if actual_delta < 0:
        reason = "down"
    elif actual_delta > 0:
        reason = "up"
    else:
        reason = "stay"

    return {
        "calibrated_level": calibrated,
        "self_assessed_level": assessed,
        "delta": actual_delta,
        "target_value": target_value,
        "test_result": result,
        "reason": reason,
    }
