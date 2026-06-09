"""
CORVIS Streak Calculation
=========================

Streak = consecutive *scheduled training days* completed, counting backwards
from today.

Rules (decided with user):
- Only days in the user's `training_days` (weekday numbers 1=Mon..7=Sun) count.
- A scheduled training day that was trained  -> streak continues (+1).
- A scheduled training day marked as RestDay ("Heute nicht") -> excused, skipped
  (neither breaks nor increments).
- A scheduled training day with neither workout nor rest day -> streak breaks.
- Non-training weekdays are ignored entirely (a planned rest day like Wednesday
  never breaks the streak).
- TODAY is special: if today is a scheduled training day and not yet trained,
  it does NOT break the streak (the day isn't over yet) — we just don't count
  it. The streak reflects the run up to and including the last resolved day.

`weekday()` in Python is 0=Mon..6=Sun, so we map to 1..7 via +1.
"""

import datetime


def _weekday_1_7(d):
    """Return ISO-style weekday: 1=Monday .. 7=Sunday."""
    return d.weekday() + 1


def calculate_streak(training_days, trained_dates, rest_dates, today=None,
                     max_lookback=400):
    """
    Args:
        training_days: list/set of weekday numbers (1=Mon..7=Sun) the user trains.
        trained_dates: set of datetime.date the user completed a workout.
        rest_dates:    set of datetime.date marked as "Heute nicht".
        today:         datetime.date (defaults to real today).
        max_lookback:  safety bound on how many days back to scan.

    Returns:
        dict:
          - current: int  (current streak in training-days)
          - last_trained: datetime.date | None
          - trained_today: bool
          - is_training_day_today: bool
          - rested_today: bool
    """
    if today is None:
        today = datetime.date.today()

    training_days = set(training_days or [])
    trained_dates = set(trained_dates or [])
    rest_dates = set(rest_dates or [])

    is_training_day_today = _weekday_1_7(today) in training_days
    trained_today = today in trained_dates
    rested_today = today in rest_dates

    streak = 0
    last_trained = None

    for i in range(max_lookback):
        day = today - datetime.timedelta(days=i)
        wd = _weekday_1_7(day)

        # Skip weekdays that aren't scheduled training days.
        if wd not in training_days:
            continue

        if day in trained_dates:
            streak += 1
            if last_trained is None:
                last_trained = day
            continue

        if day in rest_dates:
            # Excused — does not break, does not count.
            continue

        # Scheduled training day with nothing logged.
        if i == 0:
            # Today not done yet — the day isn't over, don't break.
            continue

        # A past scheduled day was missed -> streak ends here.
        break

    return {
        "current": streak,
        "last_trained": last_trained,
        "trained_today": trained_today,
        "is_training_day_today": is_training_day_today,
        "rested_today": rested_today,
    }


def longest_streak(training_days, trained_dates, rest_dates, today=None,
                   max_lookback=400):
    """
    Longest run of consecutive scheduled training days that were trained
    (rest days excused, non-training weekdays skipped). Scans backwards from
    today over `max_lookback` days.
    """
    if today is None:
        today = datetime.date.today()

    training_days = set(training_days or [])
    trained_dates = set(trained_dates or [])
    rest_dates = set(rest_dates or [])

    longest = 0
    run = 0

    # Walk from oldest to newest so runs accumulate naturally.
    for i in range(max_lookback, -1, -1):
        day = today - datetime.timedelta(days=i)
        wd = _weekday_1_7(day)

        if wd not in training_days:
            continue
        if day in trained_dates:
            run += 1
            longest = max(longest, run)
        elif day in rest_dates:
            continue  # excused, keep run
        else:
            if day == today:
                continue  # today not over yet
            run = 0

    return longest
