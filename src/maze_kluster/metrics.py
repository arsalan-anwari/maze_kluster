from __future__ import annotations

from maze_kluster.bots.base import RunResult


def score_efficiency(result: RunResult) -> float:
    """Fraction of the total potential reward that ended up in the bag (0-1)."""
    if result.potential_reward == 0:
        return 0.0
    return result.score_in_bag / result.potential_reward


def step_efficiency(result: RunResult) -> float:
    """Score collected per move, a proxy for how directly the bot found rewards."""
    if result.total_moves == 0:
        return 0.0
    return result.score_in_bag / result.total_moves


def collection_rate(result: RunResult) -> float:
    """Of all score picked up, how much made it into the bag vs. lost in hand."""
    total_collected = result.score_in_bag + result.score_lost
    if total_collected == 0:
        return 1.0
    return result.score_in_bag / total_collected


def exploration_completeness(result: RunResult) -> float:
    """Fraction of the maze's tiles that were visited, capped at 1.0."""
    if result.total_tiles == 0:
        return 0.0
    return min(result.tiles_visited / result.total_tiles, 1.0)
