from __future__ import annotations

import pytest

from maze_kluster.bots.base import RunResult
from maze_kluster.metrics import (
    collection_rate,
    exploration_completeness,
    score_efficiency,
    step_efficiency,
)


def make_result(
    maze_name: str = "Test",
    score_in_bag: float = 1.0,
    score_lost: float = 0.0,
    total_moves: int = 4,
    tiles_visited: int = 5,
    total_tiles: int = 5,
    potential_reward: float = 1.0,
) -> RunResult:
    return RunResult(
        maze_name=maze_name,
        score_in_bag=score_in_bag,
        score_lost=score_lost,
        total_moves=total_moves,
        tiles_visited=tiles_visited,
        total_tiles=total_tiles,
        potential_reward=potential_reward,
    )


def test_score_efficiency_full_collection() -> None:
    assert score_efficiency(make_result(score_in_bag=1.0, potential_reward=1.0)) == 1.0


def test_score_efficiency_partial() -> None:
    assert score_efficiency(make_result(score_in_bag=50.0, potential_reward=100.0)) == 0.5


def test_score_efficiency_zero_potential_reward() -> None:
    assert score_efficiency(make_result(score_in_bag=0.0, potential_reward=0.0)) == 0.0


def test_step_efficiency_normal() -> None:
    assert step_efficiency(make_result(score_in_bag=10.0, total_moves=5)) == 2.0


def test_step_efficiency_zero_moves() -> None:
    assert step_efficiency(make_result(score_in_bag=10.0, total_moves=0)) == 0.0


def test_collection_rate_perfect() -> None:
    assert collection_rate(make_result(score_in_bag=10.0, score_lost=0.0)) == 1.0


def test_collection_rate_partial() -> None:
    assert collection_rate(make_result(score_in_bag=8.0, score_lost=2.0)) == pytest.approx(0.8)


def test_collection_rate_all_lost() -> None:
    assert collection_rate(make_result(score_in_bag=0.0, score_lost=10.0)) == 0.0


def test_collection_rate_nothing_to_collect() -> None:
    assert collection_rate(make_result(score_in_bag=0.0, score_lost=0.0)) == 1.0


def test_exploration_completeness_full() -> None:
    assert exploration_completeness(make_result(tiles_visited=5, total_tiles=5)) == 1.0


def test_exploration_completeness_partial() -> None:
    result = make_result(tiles_visited=3, total_tiles=10)
    assert exploration_completeness(result) == pytest.approx(0.3)


def test_exploration_completeness_zero_tiles() -> None:
    assert exploration_completeness(make_result(tiles_visited=0, total_tiles=0)) == 0.0
