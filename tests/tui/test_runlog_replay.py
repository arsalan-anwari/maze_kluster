from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample_run.jsonl"


def _load_steps() -> list[dict[str, Any]]:
    with open(FIXTURE) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_replay_loads_correct_number_of_steps() -> None:
    steps = _load_steps()
    assert len(steps) == 5


def test_replay_step_sequence() -> None:
    steps = _load_steps()
    assert steps[0]["step"] == 1
    assert steps[4]["step"] == 5


def test_replay_positions_advance() -> None:
    steps = _load_steps()
    assert steps[0]["pos"] == [1, 0]
    assert steps[1]["pos"] == [2, 0]


def test_replay_score_increases_after_collect() -> None:
    steps = _load_steps()
    assert steps[2]["score"] == 0
    assert steps[3]["score"] == 1


def test_replay_frontier_decreases() -> None:
    steps = _load_steps()
    assert steps[0]["frontier_size"] > steps[4]["frontier_size"]


def test_replay_all_fields_present() -> None:
    required = {"step", "pos", "tile_type", "score", "moves", "frontier_size"}
    for step in _load_steps():
        assert required.issubset(step.keys())
