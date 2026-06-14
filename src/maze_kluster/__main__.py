from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _list_mazes() -> list[str]:
    """Return maze names from data/mazes.json (local) or bundled package data."""
    local = Path("data/mazes.json")
    if local.exists():
        data: list[dict[str, object]] = json.loads(local.read_text())
    else:
        from importlib.resources import files

        data = json.loads(files("maze_kluster.data").joinpath("mazes.json").read_text())
    return [str(m["name"]) for m in data]


def main() -> None:
    """CLI entry point. Currently only the 'tui' subcommand is supported."""
    parser = argparse.ArgumentParser(prog="maze-kluster")
    subparsers = parser.add_subparsers(dest="command")

    tui_parser = subparsers.add_parser("tui", help="Launch the TUI")
    tui_parser.add_argument("--live", action="store_true", help="Start a live run")
    tui_parser.add_argument("--maze", type=str, default=None, help="Maze name for live run")
    tui_parser.add_argument(
        "--bot", type=str, default="baseline", help="Bot name from BOTS registry"
    )  # noqa: E501
    tui_parser.add_argument(
        "--replay", type=str, default=None, metavar="PATH", help="Path to JSONL run log for replay"
    )  # noqa: E501
    tui_parser.add_argument(
        "--theme",
        type=str,
        default=None,
        metavar="THEME_NAME",
        help="TUI colour theme (see --list-themes)",
    )  # noqa: E501
    tui_parser.add_argument(
        "--connection",
        type=str,
        default="connection.json",
        metavar="PATH",
        help="Path to connection.json with API credentials",
    )  # noqa: E501
    tui_parser.add_argument(
        "--list-mazes", action="store_true", help="Print available maze names and exit"
    )  # noqa: E501
    tui_parser.add_argument(
        "--list-themes", action="store_true", help="Print available theme names and exit"
    )  # noqa: E501

    args = parser.parse_args()

    if args.command == "tui":
        if args.list_mazes:
            try:
                for name in _list_mazes():
                    print(name)
            except Exception as exc:
                print(f"Error reading maze list: {exc}", file=sys.stderr)
                sys.exit(1)
            sys.exit(0)

        if args.list_themes:
            from maze_kluster.tui.app import MazeApp

            app = MazeApp()
            for name in sorted(app.available_themes):
                print(name)
            sys.exit(0)

        from maze_kluster.tui.app import MazeApp

        app = MazeApp(
            live=args.live,
            maze_name=args.maze,
            bot_name=args.bot,
            log_path=args.replay,
            theme_name=args.theme,
            connection_path=args.connection,
        )
        app.run()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
