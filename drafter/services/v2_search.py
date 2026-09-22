"""Legal draft search over an explicitly supplied V model."""

from drafter.services.evaluation import EvaluationExample


def legal_candidates(pool, own, enemy, bans):
    blocked = set(own) | set(enemy) | set(bans)
    return sorted((candidate for candidate in pool if candidate not in blocked), key=str)


def _row(own, enemy, mode, map_name):
    return EvaluationExample(
        fingerprint="search",
        played_at=None,
        mode=mode,
        map_name=map_name,
        team_a=tuple(sorted(own)),
        team_b=tuple(sorted(enemy)),
        label=0,
    )


def last_pick(model, pool, own, enemy, bans, mode="", map_name=""):
    """Rank legal own picks by V after completing own team."""
    candidates = legal_candidates(pool, own, enemy, bans)
    return [
        {"candidate": candidate, "p_win": model.predict(_row(own + (candidate,), enemy, mode, map_name))}
        for candidate in candidates
    ]


def expectimax_pick(model, pool, own, enemy, bans, mode="", map_name="", response_depth=1):
    """Population-aware search with uniform legal opponent responses.

    The uniform response population is an explicit approximation, not a
    claim about historical pick frequencies. Depth one is the first useful
    mid-pick layer; deeper search grows combinatorially.
    """
    candidates = legal_candidates(pool, own, enemy, bans)
    result = []
    for candidate in candidates:
        own_after = own + (candidate,)
        responses = legal_candidates(pool, own_after, enemy, bans)
        if response_depth <= 0 or not responses:
            value = model.predict(_row(own_after, enemy, mode, map_name))
        else:
            value = sum(
                model.predict(_row(own_after, enemy + (response,), mode, map_name))
                for response in responses
            ) / len(responses)
        result.append({"candidate": candidate, "p_win": value, "responses": len(responses)})
    return sorted(result, key=lambda item: (-item["p_win"], str(item["candidate"])))