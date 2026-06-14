from __future__ import annotations

import json
from fnmatch import fnmatch
from pathlib import Path

import pytest

from maze_kluster.data.collector import RunLog
from maze_kluster.enums import TileSymbol

EXPECTED_STEP_KEYS = {"step", "pos", "tile_type", "score", "score_hand", "moves", "frontier_size"}


def _make_runlog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RunLog:
    monkeypatch.setattr(RunLog, "RUNS_DIR", tmp_path)
    return RunLog("Test", "baseline")


def test_record_step_writes_valid_jsonl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runlog = _make_runlog(tmp_path, monkeypatch)
    runlog.record_step((1, 0), TileSymbol.Reward, 5.0, 0.0, 3)
    runlog.record_step((2, 0), TileSymbol.Collectible, 0.0, 5.0, 2)
    runlog.close()

    lines = runlog.path.read_text().strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        data = json.loads(line)
        assert set(data.keys()) == EXPECTED_STEP_KEYS


def test_record_step_increments_step(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runlog = _make_runlog(tmp_path, monkeypatch)
    for _ in range(3):
        runlog.record_step((0, 0), TileSymbol.Reward, 0.0, 0.0, 1)
    runlog.close()

    lines = runlog.path.read_text().strip().split("\n")
    steps = [json.loads(line)["step"] for line in lines]
    assert steps == [1, 2, 3]


def test_file_grows_monotonically(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runlog = _make_runlog(tmp_path, monkeypatch)
    prev_size = runlog.path.stat().st_size

    for i in range(3):
        runlog.record_step((i, 0), TileSymbol.Reward, 0.0, 0.0, 1)
        current_size = runlog.path.stat().st_size
        assert current_size > prev_size
        prev_size = current_size

    runlog.close()


def test_replay_reads_back_correctly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runlog = _make_runlog(tmp_path, monkeypatch)
    positions = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
    frontier_sizes = [5, 4, 3, 2, 1]
    for pos, fs in zip(positions, frontier_sizes):
        runlog.record_step(pos, TileSymbol.Reward, 0.0, 0.0, fs)
    runlog.close()

    lines = runlog.path.read_text().strip().split("\n")
    steps = [json.loads(line) for line in lines]
    assert steps[2]["pos"] == [2, 0]
    assert steps[2]["frontier_size"] == 3


def test_runlog_path_naming(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(RunLog, "RUNS_DIR", tmp_path)
    runlog = RunLog("Hello Maze", "baseline")
    runlog.close()

    assert fnmatch(runlog.path.name, "hello_maze_baseline_*.jsonl")
