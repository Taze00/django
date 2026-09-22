"""Dependency-free, time-split evaluation primitives for Drafter V2.

This module deliberately does not train on the Legacy score or on synthetic
production rows. It consumes finished, deduplicated matches only.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from math import log, exp


EPSILON = 1e-6


@dataclass(frozen=True)
class EvaluationExample:
    fingerprint: str
    played_at: datetime
    mode: str
    map_name: str
    team_a: tuple
    team_b: tuple
    label: int


def sigmoid(value):
    if value >= 0:
        return 1.0 / (1.0 + exp(-min(value, 40.0)))
    positive = exp(max(value, -40.0))
    return positive / (1.0 + positive)


def examples_from_queryset(queryset):
    """Convert a Match queryset into valid finished-match examples.

    Rows with unknown players, winners, conflicts or non-3v3 teams are
    skipped and counted by the caller through the returned reasons.
    """
    examples = []
    skipped = defaultdict(int)
    rows = queryset.prefetch_related("players").order_by("played_at", "fingerprint")
    for match in rows.iterator(chunk_size=500):
        players = [player for player in match.players.all() if player.brawler_id]
        teams = {
            side: tuple(sorted(player.brawler_id for player in players if player.side == side))
            for side in ("a", "b")
        }
        if match.has_conflict or match.winner_side not in ("a", "b"):
            skipped["unknown_or_conflict_result"] += 1
            continue
        if len(teams["a"]) != 3 or len(teams["b"]) != 3:
            skipped["not_complete_3v3"] += 1
            continue
        examples.append(EvaluationExample(
            fingerprint=match.fingerprint,
            played_at=match.played_at,
            mode=match.mode_name or str(match.game_mode_id or ""),
            map_name=match.map_name or str(match.brawl_map_id or ""),
            team_a=teams["a"],
            team_b=teams["b"],
            label=int(match.winner_side == "a"),
        ))
    return examples, dict(skipped)


def time_split(examples, train_fraction=0.6, validation_fraction=0.2):
    """Return train/validation/holdout with no fingerprint crossing splits."""
    if not 0 <= train_fraction <= 1 or not 0 <= validation_fraction <= 1:
        raise ValueError("split fractions must be between 0 and 1")
    if train_fraction + validation_fraction > 1:
        raise ValueError("train and validation fractions exceed 1")
    ordered = sorted(examples, key=lambda row: (row.played_at, row.fingerprint))
    fingerprints = [row.fingerprint for row in ordered]
    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("duplicate fingerprint in evaluation input")
    train_end = int(len(ordered) * train_fraction)
    validation_end = train_end + int(len(ordered) * validation_fraction)
    if ordered and train_end == 0:
        train_end = 1
    if len(ordered) > 1 and validation_end <= train_end:
        validation_end = min(len(ordered) - 1, train_end + 1)
    return ordered[:train_end], ordered[train_end:validation_end], ordered[validation_end:]


def _feature_rates(train, context=None, smoothing=5.0):
    wins = defaultdict(float)
    games = defaultdict(float)
    for row in train:
        key = context(row) if context else "global"
        for brawler in row.team_a:
            games[(key, brawler)] += 1
            wins[(key, brawler)] += row.label
        for brawler in row.team_b:
            games[(key, brawler)] += 1
            wins[(key, brawler)] += 1 - row.label
    return {
        key: (wins[key] + smoothing * 0.5) / (games[key] + smoothing)
        for key in games
    }


def _predict_from_rates(row, rates, context=None):
    key = context(row) if context else "global"
    values = []
    for team in (row.team_a, row.team_b):
        score = 0.0
        for brawler in team:
            rate = rates.get((key, brawler), 0.5)
            score += log(max(EPSILON, rate) / max(EPSILON, 1.0 - rate))
        values.append(score)
    return sigmoid(values[0] - values[1])


def _pair_rates(train, smoothing=10.0):
    values = defaultdict(lambda: [0.0, 0.0])
    for row in train:
        for own in (row.team_a, row.team_b):
            for index, first in enumerate(own):
                for second in own[index + 1:]:
                    pair = tuple(sorted((first, second)))
                    values[pair][1] += 1
                    values[pair][0] += row.label if own is row.team_a else 1 - row.label
    return {
        pair: (wins + smoothing * 0.5) / (games + smoothing)
        for pair, (wins, games) in values.items()
    }


def predictors(train):
    """Return the baseline ladder B0-B5 as name -> predictor."""
    global_rates = _feature_rates(train)
    mode_rates = _feature_rates(train, lambda row: ("mode", row.mode))
    map_rates = _feature_rates(train, lambda row: ("map", row.map_name))
    pair_rates = _pair_rates(train)

    def b0(row):
        return 0.5

    def make_meta(rates, context=None):
        return lambda row: _predict_from_rates(row, rates, context)

    def b5(row):
        base = _predict_from_rates(row, global_rates)
        pair_scores = []
        for team, sign in ((row.team_a, 1), (row.team_b, -1)):
            for index, first in enumerate(team):
                for second in team[index + 1:]:
                    pair_scores.append(sign * (pair_rates.get(tuple(sorted((first, second))), 0.5) - 0.5))
        return sigmoid(log(max(EPSILON, base) / max(EPSILON, 1.0 - base)) + sum(pair_scores))

    return {
        "B0_50_50": b0,
        "B2_global_meta": make_meta(global_rates),
        "B3_meta_mode": make_meta(mode_rates, lambda row: ("mode", row.mode)),
        "B4_meta_map": make_meta(map_rates, lambda row: ("map", row.map_name)),
        "B5_meta_pair_synergy": b5,
    }


def metrics(predictor, examples):
    if not examples:
        return {"status": "DATA_UNAVAILABLE", "n": 0}
    probabilities = [min(1.0 - EPSILON, max(EPSILON, predictor(row))) for row in examples]
    labels = [row.label for row in examples]
    log_loss = -sum(label * log(probability) + (1 - label) * log(1 - probability)
                    for probability, label in zip(probabilities, labels)) / len(labels)
    brier = sum((probability - label) ** 2 for probability, label in zip(probabilities, labels)) / len(labels)
    calibration = []
    for lower in (0.0, 0.2, 0.4, 0.6, 0.8):
        bucket = [(p, y) for p, y in zip(probabilities, labels)
                  if lower <= p < lower + 0.2 or (lower == 0.8 and p <= 1.0)]
        if bucket:
            calibration.append({
                "lower": lower,
                "n": len(bucket),
                "mean_predicted": sum(p for p, _ in bucket) / len(bucket),
                "observed_rate": sum(y for _, y in bucket) / len(bucket),
            })
    return {"status": "ok", "n": len(examples), "log_loss": log_loss,
            "brier": brier, "calibration": calibration}


def evaluate(train, validation, holdout):
    models = predictors(train)
    return {
        name: {
            "validation": metrics(predictor, validation),
            "holdout": metrics(predictor, holdout),
        }
        for name, predictor in models.items()
    }