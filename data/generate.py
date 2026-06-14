#!/usr/bin/env python
"""Run the baseline bot on all training mazes and append data to data/maze_runs.parquet.

Run from the project root:
    python data/generate.py

Each maze can only be played once per player session. Already-completed mazes are
skipped automatically. Use --reset to wipe all progress and start over.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from maze_kluster.api import MazeClient
from maze_kluster.bots.baseline import BaselineBot

TRAIN_MAZES = [
    "Hello Maze",
    "Exit",
    "Loops",
    "Easy deal",
    "Michiel",
    "Dig Down",
    "Egg",
]

PARQUET_PATH = Path("data/maze_runs.parquet")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Forget all player progress and re-register before collecting data.",
    )
    args = parser.parse_args()

    with open("connection.json") as f:
        cfg: dict[str, Any] = json.load(f)
    player_name = str(cfg.get("player", {}).get("name", ""))

    client = MazeClient.from_config("connection.json")

    if args.reset:
        if not player_name:
            raise ValueError("player.name missing from connection.json, cannot re-register")
        client.forget()
        client.register(player_name)
        print(f"Session reset. Re-registered as {player_name!r}.\n")

    all_mazes = {m.name: m for m in client.all_mazes()}

    skipped = 0
    for maze_name in TRAIN_MAZES:
        info = all_mazes.get(maze_name)
        total_tiles = info.total_tiles if info is not None else 0
        potential_reward = info.potential_reward if info is not None else 0.0

        print(f"Running {maze_name!r}  ({total_tiles} tiles, {potential_reward:.1f} potential reward)...")
        bot = BaselineBot.with_logging(
            client=client,
            maze_name=maze_name,
            total_tiles=total_tiles,
            potential_reward=potential_reward,
        )

        try:
            result = bot.run(maze_name)
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 409:
                print("  skipped, maze already completed this session")
                skipped += 1
                continue
            raise

        efficiency = (
            result.score_in_bag / result.potential_reward * 100
            if result.potential_reward > 0
            else 0.0
        )
        print(
            f"  score={result.score_in_bag:.1f}/{result.potential_reward:.1f} ({efficiency:.1f}%)  "
            f"tiles={min(result.tiles_visited, result.total_tiles)}/{result.total_tiles}  "
            f"moves={result.total_moves}"
        )

    total_rows = len(pd.read_parquet(PARQUET_PATH)) if PARQUET_PATH.exists() else 0
    note = f"  ({skipped} skipped, already completed)" if skipped else ""
    print(f"\nDone. {total_rows} rows in {PARQUET_PATH}{note}")
    if skipped == len(TRAIN_MAZES):
        print("All mazes already completed. Use DELETE /api/player/forget to reset and replay.")


if __name__ == "__main__":
    main()
