from __future__ import annotations

import pytest

from maze_kluster.data.collector import TileLogger
from maze_kluster.enums import TileSymbol
from maze_kluster.graph import MazeGraph


@pytest.fixture
def small_graph() -> MazeGraph:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 10.0)
    graph.add_node((2, 0), TileSymbol.Collectible, 20.0)
    graph.add_node((3, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((1, 0), (2, 0))
    graph.add_edge((2, 0), (3, 0))
    graph.mark_visited((0, 0))
    graph.mark_visited((1, 0))
    graph.mark_visited((2, 0))
    graph.mark_visited((3, 0))
    return graph


def test_actual_degree_correct() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 5.0)
    graph.add_node((0, 1), TileSymbol.Reward, 3.0)
    graph.add_node((-1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((0, 0), (0, 1))
    graph.add_edge((0, 0), (-1, 0))
    graph.mark_visited((0, 0))

    logger = TileLogger("TestMaze", 4, 8.0)
    logger.record_visit(graph, (0, 0), visit_order=1)

    assert logger._rows[0]["actual_degree"] == 3


def test_is_dead_end_true_for_degree_one(small_graph: MazeGraph) -> None:
    logger = TileLogger("TestMaze", 4, 30.0)
    logger.record_visit(small_graph, (3, 0), visit_order=1)

    assert logger._rows[0]["is_dead_end"] is True


def test_is_dead_end_false_for_degree_two(small_graph: MazeGraph) -> None:
    logger = TileLogger("TestMaze", 4, 30.0)
    logger.record_visit(small_graph, (1, 0), visit_order=1)

    assert logger._rows[0]["is_dead_end"] is False


def test_neighbor_reward_mean_correct() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 10.0)
    graph.add_node((0, 1), TileSymbol.Reward, 20.0)
    graph.add_node((-1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((0, 0), (0, 1))
    graph.add_edge((0, 0), (-1, 0))
    graph.mark_visited((0, 0))

    logger = TileLogger("TestMaze", 4, 30.0)
    logger.record_visit(graph, (0, 0), visit_order=1)

    assert logger._rows[0]["neighbor_reward_mean"] == pytest.approx(10.0)


def test_neighbor_reward_mean_manual_calc() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 5.0)
    graph.add_node((0, 1), TileSymbol.Reward, 15.0)
    graph.add_node((-1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((0, 0), (0, 1))
    graph.add_edge((0, 0), (-1, 0))
    graph.mark_visited((0, 0))

    logger = TileLogger("TestMaze", 4, 20.0)
    logger.record_visit(graph, (0, 0), visit_order=1)

    assert logger._rows[0]["neighbor_reward_mean"] == pytest.approx(6.667, abs=0.001)


def test_neighbor_reward_max_correct() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 10.0)
    graph.add_node((0, 1), TileSymbol.Reward, 20.0)
    graph.add_node((-1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((0, 0), (0, 1))
    graph.add_edge((0, 0), (-1, 0))
    graph.mark_visited((0, 0))

    logger = TileLogger("TestMaze", 4, 30.0)
    logger.record_visit(graph, (0, 0), visit_order=1)

    assert logger._rows[0]["neighbor_reward_max"] == pytest.approx(20.0)


def test_neighbor_reward_zero_when_no_neighbors() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))

    logger = TileLogger("TestMaze", 1, 0.0)
    logger.record_visit(graph, (0, 0), visit_order=1)

    assert logger._rows[0]["neighbor_reward_mean"] == 0.0
    assert logger._rows[0]["neighbor_reward_max"] == 0.0


def test_unvisited_neighbors_count() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 5.0)
    graph.add_node((0, 1), TileSymbol.Reward, 3.0)
    graph.add_node((-1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((0, 0), (0, 1))
    graph.add_edge((0, 0), (-1, 0))
    graph.mark_visited((0, 0))
    graph.mark_visited((1, 0))
    graph.add_to_frontier((0, 1))
    graph.add_to_frontier((-1, 0))

    logger = TileLogger("TestMaze", 4, 8.0)
    logger.record_visit(graph, (0, 0), visit_order=1)

    assert logger._rows[0]["unvisited_neighbors"] == 2


def test_visit_order_increments(small_graph: MazeGraph) -> None:
    logger = TileLogger("TestMaze", 4, 30.0)
    logger.record_visit(small_graph, (0, 0), visit_order=1)
    logger.record_visit(small_graph, (1, 0), visit_order=2)
    logger.record_visit(small_graph, (2, 0), visit_order=3)

    assert logger._rows[0]["visit_order"] == 1
    assert logger._rows[2]["visit_order"] == 3


def test_tile_type_recorded_correctly(small_graph: MazeGraph) -> None:
    logger = TileLogger("TestMaze", 4, 30.0)
    logger.record_visit(small_graph, (2, 0), visit_order=1)

    assert logger._rows[0]["tile_type"] == TileSymbol.Collectible
