#!/usr/bin/env python
"""Run bots on the four held-out eval mazes and append results to data/eval_results.json.

Run from the project root:
    python data/generate_eval.py --bot baseline          # run one bot
    python data/generate_eval.py --bot rf --reset        # reset then run RF
    python data/generate_eval.py --bot all --reset       # full 16-run sweep

Each maze can only be completed once per player session.  When --bot all is
used the script automatically resets the session between bot types so every
bot gets a fresh run on every maze (4 bots × 4 mazes = 16 results).

Results are appended to data/eval_results.json so each invocation adds to
the file rather than overwriting it.

--reset (and the automatic resets inside --bot all) clear ALL player progress
including training-maze completions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests

from maze_kluster.api import MazeClient
from maze_kluster.bots.base import BotProtocol
from maze_kluster.bots.baseline import BaselineBot
from maze_kluster.bots.smart import SmartBotBase
from maze_kluster.models.gbt import GBTScorer
from maze_kluster.models.gp import GPUCBScorer
from maze_kluster.models.protocol import ScorerProtocol
from maze_kluster.models.rf import RFScorer

EVAL_MAZES = [
    "Gradius Pathways",
    "O Contra",
    "Glasses",
    "Reverse",
]

ALL_BOT_NAMES = ["baseline", "rf", "gbt", "gp"]
OUT_PATH = Path("data/eval_results.json")


def _load_scorers(bot_names: list[str]) -> dict[str, ScorerProtocol]:
    scorers: dict[str, ScorerProtocol] = {}
    if "rf" in bot_names:
        scorers["rf"] = RFScorer.load()
    if "gbt" in bot_names:
        scorers["gbt"] = GBTScorer.load()
    if "gp" in bot_names:
        scorers["gp"] = GPUCBScorer.load()
    return scorers


def _make_bot(
    bot_name: str, client: MazeClient, scorers: dict[str, ScorerProtocol]
) -> BotProtocol:
    if bot_name == "baseline":
        return BaselineBot(client=client)
    return SmartBotBase(client=client, scorer=scorers[bot_name])


def _reset_session(player_name: str) -> None:
    client = MazeClient.from_config("connection.json")
    client.forget()
    client.register(player_name)
    print(f"Session reset. Re-registered as {player_name!r}.\n")


def _run_bot(
    bot_name: str,
    maze_name: str,
    scorers: dict[str, ScorerProtocol],
    max_moves: int | None = None,
) -> dict[str, object] | None:
    print(f"Running {maze_name!r} / {bot_name!r}...", end=" ", flush=True)
    client = MazeClient.from_config("connection.json")
    bot = _make_bot(bot_name, client, scorers)
    try:
        result = bot.run(maze_name, max_moves=max_moves)
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 409:
            print("skipped (maze already completed this session)")
            return None
        raise
    efficiency = (
        result.score_in_bag / result.potential_reward * 100
        if result.potential_reward > 0
        else 0.0
    )
    print(
        f"score={result.score_in_bag:.1f}/{result.potential_reward:.1f} "
        f"({efficiency:.1f}%)  "
        f"tiles={min(result.tiles_visited, result.total_tiles)}/{result.total_tiles}  "
        f"moves={result.total_moves}"
    )
    return {
        "maze": result.maze_name,
        "bot": bot_name,
        "max_moves": max_moves,
        "score_in_bag": result.score_in_bag,
        "score_lost": result.score_lost,
        "total_moves": result.total_moves,
        "tiles_visited": result.tiles_visited,
        "total_tiles": result.total_tiles,
        "potential_reward": result.potential_reward,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--bot",
        choices=["all", *ALL_BOT_NAMES],
        default="all",
        help="Bot to run. 'all' runs every bot with automatic resets between them (default).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help=(
            "Forget all player progress and re-register before running. "
            "WARNING: also clears all training-maze scores."
        ),
    )
    parser.add_argument(
        "--max-moves",
        type=int,
        default=None,
        metavar="N",
        help="Stop exploring after N moves and head for the exit. Omit for unlimited (default).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=OUT_PATH,
        metavar="FILE",
        help=f"Output JSON file (default: {OUT_PATH}). Results are appended if the file exists.",
    )
    args = parser.parse_args()

    bot_names = ALL_BOT_NAMES if args.bot == "all" else [args.bot]
    needs_player_name = args.reset or len(bot_names) > 1

    with open("connection.json") as f:
        cfg: dict[str, Any] = json.load(f)
    player_name = str(cfg.get("player", {}).get("name", ""))

    if needs_player_name and not player_name:
        raise ValueError("player.name missing from connection.json, cannot reset/re-register")

    if args.reset:
        _reset_session(player_name)

    scorers = _load_scorers(bot_names)

    out_path: Path = args.out

    existing: list[dict[str, object]] = []
    if out_path.exists():
        existing = json.loads(out_path.read_text())

    new_results: list[dict[str, object]] = []
    for i, bot_name in enumerate(bot_names):
        if i > 0:
            _reset_session(player_name)
        for maze_name in EVAL_MAZES:
            record = _run_bot(bot_name, maze_name, scorers, max_moves=args.max_moves)
            if record is not None:
                new_results.append(record)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    all_results = existing + new_results
    out_path.write_text(json.dumps(all_results, indent=2))
    print(f"\nSaved {len(new_results)} new records ({len(all_results)} total) to {out_path}")


if __name__ == "__main__":
    main()
