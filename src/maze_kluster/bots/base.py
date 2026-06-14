from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from maze_kluster.enums import Direction

if TYPE_CHECKING:
    from maze_kluster.graph import MazeGraph


@dataclass
class RunResult:
    """Summary returned by a bot after completing or stopping a maze run."""

    maze_name: str
    score_in_bag: float
    score_lost: float
    total_moves: int
    tiles_visited: int
    total_tiles: int
    potential_reward: float


@runtime_checkable
class BotProtocol(Protocol):
    """Interface that all bot implementations must satisfy."""

    def run(self, maze_name: str, max_moves: int | None = None) -> RunResult: ...

    def next_move(self, graph: MazeGraph) -> Direction: ...
