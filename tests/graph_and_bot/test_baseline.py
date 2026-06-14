from __future__ import annotations

import json
from pathlib import Path

import responses as responses_lib

from maze_kluster.api import MazeClient
from maze_kluster.bots.baseline import BaselineBot
from maze_kluster.bots.base import BotProtocol

BASE_URL = "https://maze.kluster.htiprojects.nl"
FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "test_maze_responses.json"


def _load_sequence() -> list[dict[str, object]]:
    data = json.loads(FIXTURE_PATH.read_text())
    seq: list[dict[str, object]] = data["test_maze"]["sequence"]
    return seq


def _register(seq: list[dict[str, object]]) -> None:
    for call in seq:
        method = responses_lib.POST if "POST" in str(call["call"]) else responses_lib.GET
        url = f"{BASE_URL}{call['endpoint_path']}"
        responses_lib.add(method, url, json=call["response"])


def _make_bot() -> BaselineBot:
    client = MazeClient(base_url=BASE_URL, api_key="HTI Thanks You [w5J]")
    return BaselineBot(client=client)


def test_baseline_satisfies_protocol() -> None:
    bot = _make_bot()
    assert isinstance(bot, BotProtocol)


@responses_lib.activate
def test_baseline_visits_all_tiles() -> None:
    _register(_load_sequence())
    result = _make_bot().run("Test")
    assert result.tiles_visited == 5


@responses_lib.activate
def test_baseline_collects_score_at_c_tile() -> None:
    _register(_load_sequence())
    result = _make_bot().run("Test")
    collect_calls = [
        c for c in responses_lib.calls if "/api/maze/collectScore" in c.request.url
    ]
    assert len(collect_calls) == 1
    assert result.score_in_bag == 1.0
    assert result.score_lost == 0.0


@responses_lib.activate
def test_baseline_calls_exit_once() -> None:
    _register(_load_sequence())
    _make_bot().run("Test")
    exit_calls = [
        c for c in responses_lib.calls if "/api/maze/exit" in c.request.url
    ]
    assert len(exit_calls) == 1


@responses_lib.activate
def test_baseline_total_moves() -> None:
    _register(_load_sequence())
    result = _make_bot().run("Test")
    assert result.total_moves == 4


@responses_lib.activate
def test_baseline_result_fields() -> None:
    _register(_load_sequence())
    result = _make_bot().run("Test")
    assert result.maze_name == "Test"
    assert result.potential_reward == 1.0
    assert result.total_tiles == 5
