"""Bounded deterministic minimax over complete 3v3 compositions only.

All legal supported root candidates are considered. Later moves use an explicitly
approximate shortlist ordered by TRAIN appearance support, not inferred pick order
or opponent policy. Worst reply is worst within that shortlist, not a guarantee.
"""
from functools import lru_cache
from drafter.services.context import PICK_REIHENFOLGE
from drafter.services.v2_search import _row, legal_candidates


class PlanningError(ValueError):
    pass


def schedule(own, enemy, own_first):
    if type(own_first) is not bool:
        raise PlanningError('First-pick side must be a boolean')
    order = tuple('own' if (side == 'first') == own_first else 'enemy' for side in PICK_REIHENFOLGE)
    used = len(own) + len(enemy)
    if used >= 6 or order[:used].count('own') != len(own) or order[:used].count('enemy') != len(enemy):
        raise PlanningError('Pick counts do not match the supplied draft order')
    if order[used] != 'own':
        raise PlanningError('Opponent is next to pick')
    return order[used:]


def plan(model, pool, own, enemy, bans, support, *, mode, map_name,
         own_first, width=3, max_leaves=30000):
    if type(width) is not int or not 1 <= width <= 4:
        raise PlanningError('Search width must be 1..4')
    all_ids = own + enemy + bans
    if len(set(all_ids)) != len(all_ids):
        raise PlanningError('Repeated pick or ban')
    order = schedule(own, enemy, own_first)
    pool = tuple(sorted(set(pool)))
    candidates = legal_candidates(pool, own, enemy, bans)
    if len(candidates) < len(order):
        raise PlanningError('Insufficient legal pool to complete the draft')
    # Deterministic work bound, never return a partially evaluated root ranking.
    bound = len(candidates)
    for remaining in range(1, len(order)):
        bound *= min(width, len(candidates) - remaining)
    if bound > max_leaves:
        raise PlanningError('Search exceeds the configured leaf budget')
    evaluated = 0
    omitted = 0

    @lru_cache(maxsize=30000)
    def visit(a, b, depth):
        nonlocal evaluated, omitted
        if len(a) == len(b) == 3:
            evaluated += 1
            if evaluated > max_leaves:
                raise PlanningError('Search leaf budget exceeded')
            return model.predict(_row(a, b, mode, map_name)), ()
        choices = legal_candidates(pool, a, b, bans)
        choices.sort(key=lambda candidate: (-support.get(f'brawler:{candidate}', 0), candidate))
        omitted += max(0, len(choices) - width)
        side = order[depth]
        outcomes = []
        for choice in choices[:width]:
            new_a = tuple(sorted(a + (choice,))) if side == 'own' else a
            new_b = tuple(sorted(b + (choice,))) if side == 'enemy' else b
            value, continuation = visit(new_a, new_b, depth + 1)
            outcomes.append((value, choice, ((side, choice),) + continuation))
        best = min(outcomes, key=lambda item: ((-item[0] if side == 'own' else item[0]), item[1]))
        return best[0], best[2]

    result = []
    for candidate in candidates:
        value, continuation = visit(tuple(sorted(own + (candidate,))), tuple(sorted(enemy)), 1)
        terminal_own = own + (candidate,) + tuple(c for side, c in continuation if side == 'own')
        terminal_enemy = enemy + tuple(c for side, c in continuation if side == 'enemy')
        result.append({'candidate': candidate, 'p_win': value, 'continuation': continuation,
                       'terminal_own': terminal_own, 'terminal_enemy': terminal_enemy})
    result.sort(key=lambda item: (-item['p_win'], item['candidate']))
    return result, {'algorithm': 'bounded_minimax_complete_teams', 'width': width,
                    'remaining_order': order, 'evaluated_leaves': evaluated,
                    'leaf_budget': max_leaves, 'leaf_upper_bound': bound,
                    'omitted_branches': omitted, 'approximate': omitted > 0,
                    'shortlist': 'train_appearance_support',
                    'opponent_policy': 'worst_within_shortlist_not_empirical_pick_probability'}
