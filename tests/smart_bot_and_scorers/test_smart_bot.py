from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import responses as responses_lib

from maze_kluster.api import MazeClient
from maze_kluster.bots.base import BotProtocol
from maze_kluster.bots.smart import SmartBotBase, _build_frontier_features
from maze_kluster.enums import Direction, TileSymbol
from maze_kluster.graph import MazeGraph
from maze_kluster.models.features import prepare_features
from maze_kluster.models.gp import GPUCBScorer
from maze_kluster.models.protocol import ScorerProtocol
from maze_kluster.models.rf import RFScorer

BASE_URL = "https://maze.kluster.htiprojects.nl"
FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "test_maze_responses.json"


def _load_sequence() -> list[dict[str, object]]:
    data: dict[str, object] = json.loads(FIXTURE_PATH.read_text())
    maze = data["test_maze"]
    assert isinstance(maze, dict)
    seq = maze["sequence"]
    assert isinstance(seq, list)
    return seq


def _register(seq: list[dict[str, object]]) -> None:
    for call in seq:
        method = responses_lib.POST if "POST" in str(call["call"]) else responses_lib.GET
        url = f"{BASE_URL}{call['endpoint_path']}"
        responses_lib.add(method, url, json=call["response"])


def _make_client() -> MazeClient:
    return MazeClient(base_url=BASE_URL, api_key="HTI Thanks You [w5J]")


def _two_frontier_graph() -> tuple[MazeGraph, tuple[int, int], tuple[int, int]]:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    graph.add_node((1, 0), TileSymbol.Reward, 20.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_to_frontier((1, 0))
    graph.add_node((-1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (-1, 0))
    graph.add_to_frontier((-1, 0))
    return graph, (1, 0), (-1, 0)


@pytest.fixture
def rf_scorer(fixture_parquet: Path, tmp_path: Path) -> RFScorer:
    scorer = RFScorer()
    scorer.fit(fixture_parquet)
    scorer.save(tmp_path / "rf.pkl")
    return RFScorer.load(tmp_path / "rf.pkl")


@pytest.fixture
def gp_scorer(fixture_parquet: Path) -> GPUCBScorer:
    scorer = GPUCBScorer()
    scorer.fit(fixture_parquet)
    return scorer


def test_smart_bot_satisfies_bot_protocol() -> None:
    class ConstantScorer:
        def score(self, features: pd.DataFrame) -> list[float]:
            return [1.0] * len(features)

    bot = SmartBotBase(client=_make_client(), scorer=ConstantScorer())
    assert isinstance(bot, BotProtocol)


def test_smart_bot_satisfies_scorer_protocol_for_scorer() -> None:
    scorer = RFScorer()
    assert isinstance(scorer, ScorerProtocol)


def test_smart_bot_chooses_highest_scoring_frontier(rf_scorer: RFScorer) -> None:
    graph, node_right, node_left = _two_frontier_graph()
    frontier_nodes = list(graph.frontier)
    features = _build_frontier_features(graph, frontier_nodes)
    scores = rf_scorer.score(features)
    best_idx = scores.index(max(scores))
    best_node = frontier_nodes[best_idx]
    expected_direction = graph.path_to(best_node)[0]

    bot = SmartBotBase(client=_make_client(), scorer=rf_scorer)
    direction = bot.next_move(graph)
    assert direction == expected_direction


def test_smart_bot_satisfies_bot_protocol_with_scorer(rf_scorer: RFScorer) -> None:
    bot = SmartBotBase(client=_make_client(), scorer=rf_scorer)
    assert isinstance(bot, BotProtocol)


def test_smart_bot_handles_empty_frontier(rf_scorer: RFScorer) -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    graph.add_node((1, 0), TileSymbol.Exit, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.graph.nodes[(1, 0)]["allows_exit"] = True

    bot = SmartBotBase(client=_make_client(), scorer=rf_scorer)
    direction = bot.next_move(graph)
    assert direction == Direction.Right


@responses_lib.activate
def test_smart_bot_run_full_test_maze(rf_scorer: RFScorer) -> None:
    _register(_load_sequence())
    bot = SmartBotBase(client=_make_client(), scorer=rf_scorer)
    result = bot.run("Test")
    assert result.tiles_visited == 5
    assert result.score_in_bag == 1.0
    assert result.total_moves == 4


def test_smart_bot_gp_prefers_uncertain_tile(gp_scorer: GPUCBScorer) -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))

    graph.add_node((1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_to_frontier((1, 0))

    graph.add_node((-2, 0), TileSymbol.Reward, 15.0)
    graph.add_node((-1, 0), TileSymbol.Collectible, 0.0)
    graph.add_edge((0, 0), (-1, 0))
    graph.add_edge((-1, 0), (-2, 0))
    graph.add_to_frontier((-1, 0))

    frontier_nodes = list(graph.frontier)
    features = _build_frontier_features(graph, frontier_nodes)
    ucb_scores = gp_scorer.score(features)
    assert gp_scorer._pipeline is not None
    X = prepare_features(features)
    mu = gp_scorer._pipeline.predict(X, return_std=False)

    for u, m in zip(ucb_scores, mu):
        assert u >= m

    best_idx = ucb_scores.index(max(ucb_scores))
    best_node = frontier_nodes[best_idx]
    expected_direction = graph.path_to(best_node)[0]

    bot = SmartBotBase(client=_make_client(), scorer=gp_scorer)
    direction = bot.next_move(graph)
    assert direction == expected_direction


def test_smart_bot_accepts_custom_scorer() -> None:
    class ConstantScorer:
        def score(self, features: pd.DataFrame) -> list[float]:
            return [1.0] * len(features)

    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    graph.add_node((1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_to_frontier((1, 0))

    scorer = ConstantScorer()
    assert isinstance(scorer, ScorerProtocol)

    bot = SmartBotBase(client=_make_client(), scorer=scorer)
    direction = bot.next_move(graph)
    assert direction in list(Direction)


def test_build_frontier_features_shape() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    graph.add_node((1, 0), TileSymbol.Reward, 5.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_to_frontier((1, 0))

    features = _build_frontier_features(graph, [(1, 0)])
    assert len(features) == 1
    assert "tile_type" in features.columns
    assert "actual_degree" in features.columns
    assert "neighbor_reward_max" in features.columns


def test_build_frontier_features_values() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 10.0)
    graph.mark_visited((0, 0))
    graph.add_node((1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_to_frontier((1, 0))

    features = _build_frontier_features(graph, [(1, 0)])
    row = features.iloc[0]
    assert row["actual_degree"] == 1
    assert row["is_dead_end"] == True  # noqa: E712
    assert row["neighbor_reward_mean"] == pytest.approx(10.0)
    assert row["neighbor_reward_max"] == pytest.approx(10.0)
    assert row["unvisited_neighbors"] == 0
