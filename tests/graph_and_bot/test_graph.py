from __future__ import annotations

import pytest

from maze_kluster.api import Neighbor
from maze_kluster.enums import Direction, TileSymbol
from maze_kluster.graph import MazeGraph


def _neighbor(**kwargs: object) -> Neighbor:
    defaults: dict[str, object] = {
        "direction": Direction.Right,
        "is_start": False,
        "allows_exit": False,
        "allows_score_collection": False,
        "has_been_visited": False,
        "reward": 0.0,
        "visit_count": 0,
    }
    defaults.update(kwargs)
    return Neighbor.model_validate(defaults)


def test_add_node_creates_node_with_attrs() -> None:
    graph = MazeGraph()
    graph.add_node((1, 0), TileSymbol.Reward, 10.0)
    assert (1, 0) in graph.graph.nodes
    attrs = graph.graph.nodes[(1, 0)]
    assert attrs["tile_type"] == TileSymbol.Reward
    assert attrs["reward"] == 10.0
    assert attrs["visit_count"] == 0


def test_add_node_idempotent() -> None:
    graph = MazeGraph()
    graph.add_node((1, 0), TileSymbol.Reward, 10.0)
    graph.add_node((1, 0), TileSymbol.Empty, 99.0)
    assert len(graph.graph.nodes) == 1
    assert graph.graph.nodes[(1, 0)]["tile_type"] == TileSymbol.Reward


def test_add_edge_creates_undirected_edge() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 1.0)
    graph.add_edge((0, 0), (1, 0))
    assert graph.graph.has_edge((0, 0), (1, 0))
    assert graph.graph.has_edge((1, 0), (0, 0))


def test_add_to_frontier() -> None:
    graph = MazeGraph()
    graph.add_to_frontier((2, 0))
    assert (2, 0) in graph.frontier
    graph.add_to_frontier((2, 0))
    assert graph.frontier.count((2, 0)) if hasattr(graph.frontier, "count") else len([x for x in graph.frontier if x == (2, 0)]) == 1


def test_add_to_frontier_skips_visited() -> None:
    graph = MazeGraph()
    graph.add_node((2, 0), TileSymbol.Reward, 0.0)
    graph.visited.add((2, 0))
    graph.add_to_frontier((2, 0))
    assert (2, 0) not in graph.frontier


def test_mark_visited() -> None:
    graph = MazeGraph()
    graph.add_node((1, 0), TileSymbol.Reward, 5.0)
    graph.add_to_frontier((1, 0))
    assert (1, 0) in graph.frontier
    graph.mark_visited((1, 0))
    assert (1, 0) in graph.visited
    assert (1, 0) not in graph.frontier
    assert graph.graph.nodes[(1, 0)]["visit_count"] == 1


def test_backtrack_target_returns_nearest_frontier_node() -> None:
    graph = MazeGraph()
    for x in range(4):
        graph.add_node((x, 0), TileSymbol.Reward, 0.0)
    for x in range(3):
        graph.add_edge((x, 0), (x + 1, 0))
    graph.mark_visited((0, 0))
    for x in range(1, 4):
        graph.add_to_frontier((x, 0))
    assert graph.backtrack_target() == (1, 0)


def test_backtrack_target_returns_none_when_frontier_empty() -> None:
    graph = MazeGraph()
    assert graph.backtrack_target() is None


def test_path_to_same_pos_returns_empty() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    assert graph.path_to((0, 0)) == []


def test_path_to_adjacent() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 1.0)
    graph.add_edge((0, 0), (1, 0))
    graph.mark_visited((0, 0))
    assert graph.path_to((1, 0)) == [Direction.Right]


def test_path_to_multi_hop() -> None:
    graph = MazeGraph()
    for x in range(3):
        graph.add_node((x, 0), TileSymbol.Reward, 0.0)
    for x in range(2):
        graph.add_edge((x, 0), (x + 1, 0))
    graph.mark_visited((0, 0))
    assert graph.path_to((2, 0)) == [Direction.Right, Direction.Right]


def test_apply_neighbors_adds_to_frontier() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    neighbors = [_neighbor(direction=Direction.Right, reward=1.0)]
    graph.apply_neighbors(neighbors, (0, 0))
    assert (1, 0) in graph.frontier
    assert (1, 0) in graph.graph.nodes


def test_portal_detection() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Empty, 0.0)
    graph.add_node((2, 0), TileSymbol.Reward, 1.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((1, 0), (2, 0))
    graph.mark_visited((0, 0))
    graph.mark_visited((1, 0))

    initial_count = len(graph.graph.nodes)

    neighbors = [_neighbor(direction=Direction.Right, has_been_visited=True)]
    graph.apply_neighbors(neighbors, (1, 0))

    assert len(graph.graph.nodes) == initial_count
    assert graph.graph.has_edge((1, 0), (2, 0))
