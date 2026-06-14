from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from maze_kluster.data.collector import EXPECTED_COLUMNS, TileLogger
from maze_kluster.enums import TileSymbol
from maze_kluster.graph import MazeGraph


def _two_node_graph() -> tuple[MazeGraph, tuple[int, int]]:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 5.0)
    graph.add_edge((0, 0), (1, 0))
    graph.mark_visited((0, 0))
    graph.mark_visited((1, 0))
    return graph, (1, 0)


def test_record_visit_appends_correct_row() -> None:
    graph, pos = _two_node_graph()
    logger = TileLogger("TestMaze", 10, 100.0)
    logger.record_visit(graph, pos, visit_order=1)

    row = logger._rows[0]
    assert row["maze_name"] == "TestMaze"
    assert row["tile_x"] == 1
    assert row["tile_y"] == 0
    assert row["reward"] == 5.0
    assert row["tile_type"] == TileSymbol.Reward
    assert row["actual_degree"] == 1
    assert row["is_dead_end"] is True
    assert row["visit_order"] == 1
    assert row["times_visited"] == 1
    assert row["maze_total_tiles"] == 10
    assert row["maze_potential_reward"] == 100.0


def test_record_visit_schema_columns() -> None:
    graph, pos = _two_node_graph()
    logger = TileLogger("TestMaze", 10, 100.0)
    logger.record_visit(graph, pos, visit_order=1)

    df = pd.DataFrame(logger._rows)
    assert set(df.columns) == EXPECTED_COLUMNS


def _three_node_graph() -> MazeGraph:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 3.0)
    graph.add_node((2, 0), TileSymbol.Collectible, 7.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((1, 0), (2, 0))
    graph.mark_visited((0, 0))
    graph.mark_visited((1, 0))
    graph.mark_visited((2, 0))
    return graph


def test_flush_writes_parquet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parquet_path = tmp_path / "test.parquet"
    monkeypatch.setattr(TileLogger, "PARQUET_PATH", parquet_path)

    graph = _three_node_graph()
    logger = TileLogger("TestMaze", 5, 50.0)
    logger.record_visit(graph, (0, 0), 1)
    logger.record_visit(graph, (1, 0), 2)
    logger.record_visit(graph, (2, 0), 3)
    logger.flush()

    df = pd.read_parquet(parquet_path)
    assert len(df) == 3
    assert set(df.columns) == EXPECTED_COLUMNS


def test_flush_appends_across_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parquet_path = tmp_path / "test.parquet"
    monkeypatch.setattr(TileLogger, "PARQUET_PATH", parquet_path)

    graph = _three_node_graph()

    logger1 = TileLogger("Maze1", 5, 50.0)
    logger1.record_visit(graph, (0, 0), 1)
    logger1.record_visit(graph, (1, 0), 2)
    logger1.record_visit(graph, (2, 0), 3)
    logger1.flush()

    logger2 = TileLogger("Maze2", 5, 50.0)
    logger2.record_visit(graph, (0, 0), 1)
    logger2.record_visit(graph, (1, 0), 2)
    logger2.flush()

    df = pd.read_parquet(parquet_path)
    assert len(df) == 5


def test_flush_preserves_dtypes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parquet_path = tmp_path / "test.parquet"
    monkeypatch.setattr(TileLogger, "PARQUET_PATH", parquet_path)

    graph = _two_node_graph()[0]
    logger = TileLogger("TestMaze", 5, 50.0)
    logger.record_visit(graph, (0, 0), 1)
    logger.flush()

    df = pd.read_parquet(parquet_path)
    assert df["tile_x"].dtype == "int64"
    assert df["reward"].dtype == "float64"
    assert df["is_dead_end"].dtype == "bool"


def test_flush_empty_is_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parquet_path = tmp_path / "test.parquet"
    monkeypatch.setattr(TileLogger, "PARQUET_PATH", parquet_path)

    logger = TileLogger("TestMaze", 5, 50.0)
    logger.flush()

    assert not parquet_path.exists()


def test_neighbor_reward_mean() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 10.0)
    graph.add_node((0, 1), TileSymbol.Reward, 20.0)
    graph.add_node((-1, 0), TileSymbol.Empty, 0.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((0, 0), (0, 1))
    graph.add_edge((0, 0), (-1, 0))
    graph.mark_visited((0, 0))

    logger = TileLogger("TestMaze", 5, 50.0)
    logger.record_visit(graph, (0, 0), 1)

    row = logger._rows[0]
    assert row["neighbor_reward_mean"] == pytest.approx(10.0)
    assert row["neighbor_reward_max"] == pytest.approx(20.0)


def test_is_dead_end_true_for_degree_one() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 5.0)
    graph.add_edge((0, 0), (1, 0))
    graph.mark_visited((0, 0))

    logger = TileLogger("TestMaze", 5, 50.0)
    logger.record_visit(graph, (0, 0), 1)

    assert logger._rows[0]["is_dead_end"] is True


def test_is_dead_end_false_for_degree_two_plus() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.add_node((1, 0), TileSymbol.Reward, 5.0)
    graph.add_node((0, 1), TileSymbol.Reward, 3.0)
    graph.add_edge((0, 0), (1, 0))
    graph.add_edge((0, 0), (0, 1))
    graph.mark_visited((0, 0))

    logger = TileLogger("TestMaze", 5, 50.0)
    logger.record_visit(graph, (0, 0), 1)

    assert logger._rows[0]["is_dead_end"] is False
