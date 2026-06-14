from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import IO, TYPE_CHECKING, TypedDict

import pandas as pd

from maze_kluster.enums import TileSymbol

if TYPE_CHECKING:
    from maze_kluster.graph import MazeGraph


class RecordRow(TypedDict):
    """Schema for one row in the tile visit parquet dataset."""

    maze_name: str
    tile_x: int
    tile_y: int
    reward: float
    tile_type: str
    actual_degree: int
    is_dead_end: bool
    visit_order: int
    times_visited: int
    neighbor_reward_mean: float
    neighbor_reward_max: float
    unvisited_neighbors: int
    maze_total_tiles: int
    maze_potential_reward: float


EXPECTED_COLUMNS: frozenset[str] = frozenset(RecordRow.__annotations__)


class TileLogger:
    """Accumulates per-tile visit records and appends them to the parquet dataset on flush."""

    PARQUET_PATH: Path = Path("data/maze_runs.parquet")

    def __init__(
        self,
        maze_name: str,
        total_tiles: int,
        potential_reward: float,
    ) -> None:
        self._maze_name = maze_name
        self._total_tiles = total_tiles
        self._potential_reward = potential_reward
        self._rows: list[RecordRow] = []

    def record_visit(
        self,
        graph: MazeGraph,
        pos: tuple[int, int],
        visit_order: int,
    ) -> None:
        node = graph.graph.nodes[pos]
        neighbors = list(graph.graph.neighbors(pos))
        neighbor_rewards: list[float] = [float(graph.graph.nodes[n]["reward"]) for n in neighbors]
        degree = int(graph.graph.degree(pos))
        row: RecordRow = {
            "maze_name": self._maze_name,
            "tile_x": pos[0],
            "tile_y": pos[1],
            "reward": float(node["reward"]),
            "tile_type": str(node["tile_type"]),
            "actual_degree": degree,
            "is_dead_end": degree == 1,
            "visit_order": visit_order,
            "times_visited": int(node["visit_count"]),
            "neighbor_reward_mean": (
                float(sum(neighbor_rewards) / len(neighbor_rewards)) if neighbor_rewards else 0.0
            ),
            "neighbor_reward_max": (float(max(neighbor_rewards)) if neighbor_rewards else 0.0),
            "unvisited_neighbors": sum(1 for n in neighbors if n not in graph.visited),
            "maze_total_tiles": self._total_tiles,
            "maze_potential_reward": float(self._potential_reward),
        }
        self._rows.append(row)

    def flush(self) -> None:
        """Write buffered rows to parquet, appending to any existing data."""
        if not self._rows:
            return
        df = pd.DataFrame(self._rows)
        df = df.astype(
            {
                "tile_x": "int64",
                "tile_y": "int64",
                "actual_degree": "int64",
                "is_dead_end": "bool",
                "visit_order": "int64",
                "times_visited": "int64",
                "unvisited_neighbors": "int64",
                "maze_total_tiles": "int64",
            }
        )
        self.PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
        if self.PARQUET_PATH.exists():
            existing = pd.read_parquet(self.PARQUET_PATH)
            combined = pd.concat([existing, df], ignore_index=True)
        else:
            combined = df
        combined.to_parquet(self.PARQUET_PATH, index=False)
        self._rows = []


class RunLog:
    """Writes a step-by-step JSONL trace of a bot run for later replay or analysis."""

    RUNS_DIR: Path = Path("data/runs")

    def __init__(self, maze_name: str, bot_name: str) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = maze_name.replace(" ", "_").lower()
        self._path = self.RUNS_DIR / f"{safe_name}_{bot_name}_{timestamp}.jsonl"
        self.RUNS_DIR.mkdir(parents=True, exist_ok=True)
        self._file: IO[str] = self._path.open("w")
        self._step = 0

    def record_step(
        self,
        pos: tuple[int, int],
        tile_type: TileSymbol,
        score_in_hand: float,
        score_in_bag: float,
        frontier_size: int,
    ) -> None:
        self._step += 1
        line = json.dumps(
            {
                "step": self._step,
                "pos": list(pos),
                "tile_type": tile_type,
                "score": score_in_bag,
                "score_hand": score_in_hand,
                "moves": self._step,
                "frontier_size": frontier_size,
            }
        )
        self._file.write(line + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    @property
    def path(self) -> Path:
        return self._path
