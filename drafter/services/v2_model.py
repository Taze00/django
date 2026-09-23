"""Small, symmetric and dependency-free V model for complete teams."""

import json
from collections import defaultdict
from dataclasses import dataclass

from drafter.services.evaluation import EPSILON, EvaluationExample, metrics, sigmoid


FEATURE_VERSION = "v2-composition-logit-1"
OPPONENT_VERSION = "v2-composition-opponent-2"
FEATURE_VERSIONS = (FEATURE_VERSION, OPPONENT_VERSION)


def _feature_counts(row, feature_version=FEATURE_VERSION):
    if feature_version not in FEATURE_VERSIONS:
        raise ValueError("Unknown feature version")
    counts = defaultdict(float)
    for brawler in row.team_a:
        counts[f"brawler:{brawler}"] += 1.0
        counts[f"brawler_context:{row.mode}:{brawler}"] += 1.0
        counts[f"brawler_map:{row.map_name}:{brawler}"] += 1.0
    for brawler in row.team_b:
        counts[f"brawler:{brawler}"] -= 1.0
        counts[f"brawler_context:{row.mode}:{brawler}"] -= 1.0
        counts[f"brawler_map:{row.map_name}:{brawler}"] -= 1.0
    for team, sign in ((row.team_a, 1.0), (row.team_b, -1.0)):
        for index, first in enumerate(team):
            for second in team[index + 1:]:
                counts[f"pair:{min(first, second)}:{max(first, second)}"] += sign
    if feature_version == OPPONENT_VERSION:
        for first in row.team_a:
            for second in row.team_b:
                if first != second:
                    counts[f"opponent:{min(first, second)}:{max(first, second)}"] += 1.0 if first < second else -1.0
    return dict(counts)


def feature_manifest(examples, feature_version=FEATURE_VERSION):
    names = sorted({name for row in examples for name in _feature_counts(row, feature_version)})
    return {name: index for index, name in enumerate(names)}


def _vector(row, manifest, feature_version=FEATURE_VERSION):
    return {manifest[name]: value for name, value in _feature_counts(row, feature_version).items()
            if name in manifest}


@dataclass(frozen=True)
class CompositionLogitModel:
    feature_version: str
    manifest: dict
    weights: tuple
    regularization: float
    epochs: int

    def predict(self, row):
        value = sum(self.weights[index] * amount
                    for index, amount in _vector(row, self.manifest, self.feature_version).items())
        return min(1.0 - EPSILON, max(EPSILON, sigmoid(value)))

    def as_dict(self):
        return {
            "model_version": self.feature_version,
            "feature_version": self.feature_version,
            "manifest": self.manifest,
            "weights": list(self.weights),
            "regularization": self.regularization,
            "epochs": self.epochs,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            feature_version=data["feature_version"],
            manifest=data["manifest"],
            weights=tuple(data["weights"]),
            regularization=data["regularization"],
            epochs=data["epochs"],
        )


def train_model(examples, regularization=1.0, epochs=500, learning_rate=0.05, feature_version=FEATURE_VERSION):
    if not examples:
        return None
    manifest = feature_manifest(examples, feature_version)
    weights = [0.0] * len(manifest)
    vectors = [(_vector(row, manifest, feature_version), row.label) for row in examples]
    for _ in range(epochs):
        gradient = [regularization * weight for weight in weights]
        for vector, label in vectors:
            probability = sigmoid(sum(weights[index] * value
                                       for index, value in vector.items()))
            for index, value in vector.items():
                gradient[index] += (probability - label) * value
        scale = 1.0 / len(vectors)
        for index in range(len(weights)):
            weights[index] -= learning_rate * gradient[index] * scale
    return CompositionLogitModel(
        feature_version=feature_version,
        manifest=manifest,
        weights=tuple(weights),
        regularization=regularization,
        epochs=epochs,
    )


def evaluate_model(model, examples):
    if model is None:
        return {"status": "DATA_UNAVAILABLE", "n": 0}
    return metrics(model.predict, examples)


def dump_model(model, path):
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(model.as_dict(), stream, indent=2, sort_keys=True)