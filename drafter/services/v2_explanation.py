"""Structured explanations backed by V2 model facts only."""

from drafter.services.v2_model import _feature_counts


def contributions(model, row, limit=5):
    facts = []
    for name, amount in _feature_counts(row).items():
        index = model.manifest.get(name)
        if index is None:
            continue
        contribution = model.weights[index] * amount
        facts.append({
            "feature": name,
            "amount": amount,
            "weight": model.weights[index],
            "logit_contribution": contribution,
            "direction": "positive" if contribution > 0 else "negative" if contribution < 0 else "neutral",
            "provenance": "trained_model_feature",
        })
    facts.sort(key=lambda item: (-abs(item["logit_contribution"]), item["feature"]))
    return facts[:limit]


def explain(model, row, search=None, limit=5):
    result = {
        "model_version": "v2-composition-logit-1",
        "feature_version": model.feature_version,
        "p_win": model.predict(row),
        "contributions": contributions(model, row, limit=limit),
        "uncertainty": {
            "status": "model_probability",
            "sample_provenance": "training_data_required",
        },
    }
    if search is not None:
        result["search"] = {
            "candidate": search.get("candidate"),
            "responses": search.get("responses"),
            "population_assumption": "uniform_legal_responses",
            "search_p_win": search.get("p_win"),
        }
    return result