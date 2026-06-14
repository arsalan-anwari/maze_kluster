from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, ClassVar, cast

import requests
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen, Screen
from textual.theme import Theme
from textual.timer import Timer
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Select,
    Static,
)
from textual.widgets._select import NoSelection

from maze_kluster.api import MazeClient
from maze_kluster.bots import BOTS
from maze_kluster.enums import Direction, RenderState, TileSymbol
from maze_kluster.graph import DIRECTION_DELTA, MazeGraph

TILE_CHARS: dict[str, str] = {
    TileSymbol.Start: TileSymbol.Start.value,
    TileSymbol.Reward: TileSymbol.Reward.value,
    TileSymbol.Empty: TileSymbol.Empty.value,
    TileSymbol.Collectible: TileSymbol.Collectible.value,
    TileSymbol.Exit: TileSymbol.Exit.value,
    RenderState.Frontier: RenderState.Frontier.value,
    RenderState.BotPosition: RenderState.BotPosition.value,
    RenderState.Unexplored: RenderState.Unexplored.value,
}

TILE_COLORS: dict[str, str] = {
    TileSymbol.Start: "green",
    TileSymbol.Reward: "white",
    TileSymbol.Empty: "dim",
    TileSymbol.Collectible: "yellow",
    TileSymbol.Exit: "red",
    RenderState.Frontier: "blue dim",
    RenderState.BotPosition: "bold cyan",
    RenderState.Unexplored: "",
}


def render_grid(graph: MazeGraph, bot_pos: tuple[int, int]) -> str:
    """Render the known maze state as a Textual markup string, one char per tile."""
    if not graph.visited and not graph.frontier:
        return "(empty)"
    all_pos = graph.visited | graph.frontier
    min_x = min(p[0] for p in all_pos)
    max_x = max(p[0] for p in all_pos)
    min_y = min(p[1] for p in all_pos)
    max_y = max(p[1] for p in all_pos)

    lines: list[str] = []
    for y in range(max_y, min_y - 1, -1):
        row: list[str] = []
        for x in range(min_x, max_x + 1):
            pos = (x, y)
            if pos == bot_pos:
                char = TILE_CHARS[RenderState.BotPosition]
                color = TILE_COLORS[RenderState.BotPosition]
            elif pos in graph.visited:
                tile_type: str = str(graph.graph.nodes[pos]["tile_type"])
                char = TILE_CHARS[tile_type]
                color = TILE_COLORS[tile_type]
            elif pos in graph.frontier:
                char = TILE_CHARS[RenderState.Frontier]
                color = TILE_COLORS[RenderState.Frontier]
            else:
                char = TILE_CHARS[RenderState.Unexplored]
                color = TILE_COLORS[RenderState.Unexplored]
            if color:
                row.append(f"[{color}]{char}[/{color}]")
            else:
                row.append(char)
        lines.append(" ".join(row))
    return "\n".join(lines)


def _format_stats(
    maze_name: str,
    bot_name: str,
    step: int,
    score_in_bag: float,
    score_in_hand: float,
    total_reward: float,
    frontier_size: int,
    delay: float,
    finished: bool,
    max_moves: int | None = None,
) -> str:
    pct = score_in_bag / total_reward * 100 if total_reward > 0 else 0.0
    status = "DONE" if finished else "Running"
    step_str = f"{step} / {max_moves}" if max_moves is not None else str(step)
    return (
        f"Maze:     {maze_name}\n"
        f"Bot:      {bot_name}\n"
        f"Step:     {step_str}\n"
        f"Score:    {score_in_bag:.0f} / {total_reward:.0f} ({pct:.0f}%)\n"
        f"In Hand:  {score_in_hand:.0f}\n"
        f"Frontier: {frontier_size}\n"
        f"Speed:    {delay:.2f}s\n"
        f"Status:   {status}\n"
    )


def _load_mazes() -> list[str]:
    """Read maze names from mazes.json for the menu dropdown. Returns empty list on error."""
    try:
        local = Path("data/mazes.json")
        if local.exists():
            data: list[Any] = json.loads(local.read_text())
        else:
            from importlib.resources import files

            data = json.loads(files("maze_kluster.data").joinpath("mazes.json").read_text())
        return [str(m["name"]) for m in data]
    except Exception:
        return []


SHADCN_DARK = Theme(
    name="shadcn-dark",
    dark=True,
    primary="#916f6f",
    secondary="#999999",
    background="#09090b",
    surface="#18181b",
    panel="#27272a",
    boost="#3f3f46",
    foreground="#fafafa",
    accent="#916f6f",
    warning="#f59e0b",
    error="#ef4444",
    success="#22c55e",
)

SHADCN_LIGHT = Theme(
    name="shadcn-light",
    dark=False,
    primary="#916f6f",
    secondary="#999999",
    background="#ffffff",
    surface="#f4f4f5",
    panel="#e4e4e7",
    boost="#d4d4d8",
    foreground="#09090b",
    accent="#916f6f",
    warning="#d97706",
    error="#dc2626",
    success="#16a34a",
)


class MainMenuScreen(Screen[None]):
    """Start screen: pick a maze and bot, then launch a live run or replay a log."""

    DEFAULT_CSS: ClassVar[str] = """
    MainMenuScreen {
        align: center middle;
    }
    #menu {
        width: 60;
        height: auto;
        border: solid $accent;
        padding: 1 2;
        background: $surface;
    }
    #menu Label {
        margin-top: 1;
    }
    #menu-header {
        height: auto;
        width: 1fr;
    }
    #menu-header Label {
        width: 1fr;
        margin-top: 0;
    }
    #exit-btn {
        width: auto;
        min-width: 5;
        background: $error;
        color: $text;
    }
    .hidden {
        display: none;
    }
    #menu-actions {
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="menu"):
            with Horizontal(id="menu-header"):
                yield Label("[bold]maze-kluster[/bold]", markup=True)
                yield Button("X", id="exit-btn")
            yield Label("Maze:")
            yield Select(
                [(name, name) for name in _load_mazes()],
                id="maze-select",
                allow_blank=True,
                prompt="Select a maze...",
            )
            yield Label("Bot:")
            yield Select(
                [(name, name) for name in BOTS.keys()],
                id="bot-select",
                allow_blank=False,
                value="baseline",
            )
            yield Label("Max Moves (optional):")
            yield Input(placeholder="e.g. 30  (blank = unlimited)", id="max-moves-input")
            yield Label("Mode:")
            yield RadioSet(
                RadioButton("Live Run", value=True),
                RadioButton("Load Log"),
                id="mode-radio",
            )
            yield Label("Log path:", id="log-label", classes="hidden")
            yield Input(placeholder="Path to JSONL file...", id="log-input", classes="hidden")
            with Horizontal(id="menu-actions"):
                yield Button("Start", id="start-btn", variant="primary")

    def on_mount(self) -> None:
        self.run_worker(self._auto_reset, thread=True, exit_on_error=False)

    def _auto_reset(self) -> None:
        # Reset player state on each app launch so previous run scores don't carry over.
        try:
            connection_path = cast("MazeApp", self.app).connection_path
            with open(connection_path) as f:
                cfg: dict[str, Any] = json.load(f)
            player_name = str(cfg.get("player", {}).get("name", ""))
            if not player_name:
                return
            client = MazeClient.from_config(connection_path)
            client.forget()
            client.register(player_name)
        except Exception:
            pass

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        is_replay = event.index == 1
        self.query_one("#log-label", Label).set_class(not is_replay, "hidden")
        self.query_one("#log-input", Input).set_class(not is_replay, "hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit-btn":
            self.app.exit()
            return
        if event.button.id != "start-btn":
            return
        mode_radio = self.query_one("#mode-radio", RadioSet)
        is_replay = mode_radio.pressed_index == 1

        if not is_replay:
            maze_select = self.query_one("#maze-select", Select)
            bot_select = self.query_one("#bot-select", Select)
            maze_val = maze_select.value
            if isinstance(maze_val, NoSelection):
                self.notify("Please select a maze", severity="error")
                return
            bot_val = bot_select.value
            bot_name = str(bot_val) if not isinstance(bot_val, NoSelection) else "baseline"
            max_moves_str = self.query_one("#max-moves-input", Input).value.strip()
            max_moves: int | None = int(max_moves_str) if max_moves_str.isdigit() else None
            self.app.push_screen(
                RunScreen(
                    mode="live", maze_name=str(maze_val), bot_name=bot_name, max_moves=max_moves
                )
            )
        else:
            log_path = self.query_one("#log-input", Input).value.strip()
            if not log_path:
                self.notify("Please enter a log path", severity="error")
                return
            self.app.push_screen(RunScreen(mode="replay", log_path=log_path))


class BotMenuScreen(ModalScreen[tuple[str, str] | None]):
    """Modal for switching bots or loading a replay log mid-run."""

    DEFAULT_CSS: ClassVar[str] = """
    BotMenuScreen {
        align: center middle;
    }
    #bot-menu {
        width: 44;
        height: auto;
        border: solid $accent;
        padding: 1 2;
        background: $surface;
    }
    #bot-menu Label {
        margin-top: 1;
    }
    #bot-actions {
        margin-top: 1;
    }
    #bot-actions Button {
        width: 100%;
        margin-top: 1;
    }
    """
    BINDINGS: ClassVar[list[BindingType]] = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Container(id="bot-menu"):
            yield Label("[bold]Switch Bot[/bold]", markup=True)
            yield RadioSet(
                *(RadioButton(name) for name in BOTS.keys()),
                id="bot-radio",
            )
            yield Label("Or load a replay log:")
            yield Input(placeholder="Path to JSONL file...", id="log-input")
            with Container(id="bot-actions"):
                yield Button("Switch Bot", id="switch-bot", variant="primary")
                yield Button("Load Log", id="load-log")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "load-log":
            path = self.query_one("#log-input", Input).value.strip()
            self.dismiss(("log", path) if path else None)
        elif event.button.id == "switch-bot":
            radio = self.query_one("#bot-radio", RadioSet)
            pressed = radio.pressed_button
            if pressed is None:
                self.dismiss(None)
                return
            self.dismiss(("bot", str(pressed.label)))

    def action_cancel(self) -> None:
        self.dismiss(None)


class RunScreen(Screen[None]):
    """Main run screen showing the maze grid on the left and live stats on the right."""

    DEFAULT_CSS: ClassVar[str] = """
    RunScreen {
        layout: horizontal;
    }
    #maze-panel {
        width: 2fr;
        border: solid $accent;
        padding: 1;
        overflow: auto;
    }
    #stats-panel {
        width: 1fr;
        border: solid $accent;
        padding: 1 2;
    }
    #maze-grid {
        height: auto;
    }
    #stats-text {
        height: auto;
    }
    """
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("b", "open_bot_menu", "Bot menu"),
        Binding("r", "reset_run", "Reset"),
        Binding("q", "quit_run", "Return to menu"),
        Binding("e", "exit_app", "Exit"),
        Binding("comma", "speed_down", "Slower", key_display=","),
        Binding("period", "speed_up", "Faster", key_display="."),
    ]

    def __init__(
        self,
        mode: str,
        maze_name: str | None = None,
        bot_name: str = "baseline",
        log_path: str | None = None,
        max_moves: int | None = None,
    ) -> None:
        super().__init__()
        self._mode = mode
        self._maze_name = maze_name or ""
        self._bot_name = bot_name
        self._log_path = log_path or ""
        self._max_moves = max_moves
        self._step: int = 0
        self._score_in_bag: float = 0.0
        self._score_in_hand: float = 0.0
        self._total_reward: float = 0.0
        self._frontier_size: int = 0
        self._delay: float = 0.5
        self._finished: bool = False
        self._replay_steps: list[dict[str, Any]] = []
        self._replay_idx: int = 0
        self._replay_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Container(id="maze-panel"):
                yield Static("(loading...)", id="maze-grid")
            with Container(id="stats-panel"):
                yield Static("(loading...)", id="stats-text")
        yield Footer()

    def on_mount(self) -> None:
        if self._mode == "replay":
            self._start_replay()
        else:
            self.run_worker(self._live_run, thread=True, name="live_run", exit_on_error=False)

    def _apply_display(self, grid: str, stats: str) -> None:
        self.query_one("#maze-grid", Static).update(grid)
        self.query_one("#stats-text", Static).update(stats)

    def _on_enter_blocked(self, maze_name: str) -> None:
        self.notify(
            f"'{maze_name}' is already completed or locked, choose a different maze.",
            severity="error",
            timeout=5,
        )
        self.app.pop_screen()

    def _start_replay(self) -> None:
        try:
            with open(self._log_path) as f:
                self._replay_steps = [json.loads(line) for line in f if line.strip()]
        except OSError as exc:
            self._apply_display("", f"Error loading log: {exc}")
            return
        self._replay_timer = self.set_interval(self._delay, self._advance_replay)

    def _advance_replay(self) -> None:
        if self._replay_idx >= len(self._replay_steps):
            if self._replay_timer is not None:
                self._replay_timer.stop()
                self._replay_timer = None
            self._finished = True
            grid = render_grid(MazeGraph(), (-9999, -9999))
            stats = _format_stats(
                self._maze_name,
                self._bot_name,
                self._step,
                self._score_in_bag,
                self._score_in_hand,
                self._total_reward,
                self._frontier_size,
                self._delay,
                self._finished,
            )
            self._apply_display(grid, stats)
            return

        step_data = self._replay_steps[self._replay_idx]
        raw_pos: list[int] = step_data["pos"]
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        tile_sym = TileSymbol(str(step_data["tile_type"]))

        graph = MazeGraph()
        for prev in self._replay_steps[: self._replay_idx + 1]:
            p = (int(prev["pos"][0]), int(prev["pos"][1]))
            t = TileSymbol(str(prev["tile_type"]))
            graph.add_node(p, t, 0.0)
            graph.mark_visited(p)
        _ = tile_sym

        self._step = int(step_data["step"])
        self._score_in_bag = float(step_data["score"])
        self._score_in_hand = float(step_data.get("score_hand", 0))
        self._frontier_size = int(step_data["frontier_size"])
        self._replay_idx += 1

        grid = render_grid(graph, pos)
        stats = _format_stats(
            self._maze_name,
            self._bot_name,
            self._step,
            self._score_in_bag,
            self._score_in_hand,
            self._total_reward,
            self._frontier_size,
            self._delay,
            self._finished,
        )
        self._apply_display(grid, stats)

    def _live_run(self) -> None:
        """Run the selected bot in a background thread, pushing display updates to the UI thread."""
        try:
            connection_path = cast("MazeApp", self.app).connection_path
            client = MazeClient.from_config(connection_path)
            try:
                with open(connection_path) as f:
                    cfg: dict[str, Any] = json.load(f)
                player_name = str(cfg.get("player", {}).get("name", ""))
                if player_name:
                    client.forget()
                    client.register(player_name)
            except Exception:
                pass
            mazes = client.all_mazes()
            maze_info = next((m for m in mazes if m.name == self._maze_name), None)
            total_reward = maze_info.potential_reward if maze_info is not None else 0.0

            try:
                client.exit_maze()
            except Exception:
                pass

            try:
                client.enter_maze(self._maze_name)
            except requests.exceptions.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 409:
                    self.app.call_from_thread(self._on_enter_blocked, self._maze_name)
                    return
                raise

            graph = MazeGraph()
            graph.add_node((0, 0), TileSymbol.Start, 0.0)
            graph.mark_visited((0, 0))

            response = client.possible_actions()
            graph.apply_neighbors(response.neighbors, (0, 0))

            score_in_bag = response.score_in_bag
            score_in_hand = response.score_in_hand
            step = 0
            known_exits: set[tuple[int, int]] = set()

            grid = render_grid(graph, (0, 0))
            stats = _format_stats(
                self._maze_name,
                self._bot_name,
                step,
                score_in_bag,
                score_in_hand,
                total_reward,
                len(graph.frontier),
                self._delay,
                False,
                self._max_moves,
            )
            self.app.call_from_thread(self._apply_display, grid, stats)

            bot = BOTS[self._bot_name](client)

            while True:
                if response.can_collect_score and score_in_hand > 0:
                    client.collect_score()
                    score_in_hand = 0.0

                if response.can_exit:
                    known_exits.add(graph.current_pos)

                exit_known = bool(known_exits) or graph.nearest_exit(graph.current_pos) is not None
                collectible_reachable = graph.nearest_collectible(graph.current_pos) is not None
                force_exit = (
                    self._max_moves is not None
                    and step >= self._max_moves
                    and exit_known
                    and (score_in_hand == 0 or collectible_reachable)
                )

                if response.can_exit and (not graph.frontier or force_exit):
                    if score_in_hand == 0 or graph.nearest_collectible(graph.current_pos) is None:
                        client.exit_maze()
                        grid = render_grid(graph, graph.current_pos)
                        stats = _format_stats(
                            self._maze_name,
                            self._bot_name,
                            step,
                            score_in_bag,
                            score_in_hand,
                            total_reward,
                            0,
                            self._delay,
                            True,
                            self._max_moves,
                        )
                        self.app.call_from_thread(self._apply_display, grid, stats)
                        break

                direction: Direction = cast(Any, bot).next_move(
                    graph, known_exits, score_in_hand, force_exit
                )
                response = client.move(direction)
                step += 1

                dx, dy = DIRECTION_DELTA[direction]
                new_pos = (graph.current_pos[0] + dx, graph.current_pos[1] + dy)
                graph.mark_visited(new_pos)
                graph.apply_neighbors(response.neighbors, new_pos)

                score_in_bag = response.score_in_bag
                score_in_hand = response.score_in_hand

                grid = render_grid(graph, new_pos)
                stats = _format_stats(
                    self._maze_name,
                    self._bot_name,
                    step,
                    score_in_bag,
                    score_in_hand,
                    total_reward,
                    len(graph.frontier),
                    self._delay,
                    False,
                    self._max_moves,
                )
                self.app.call_from_thread(self._apply_display, grid, stats)
                time.sleep(self._delay)

        except Exception as exc:
            self.app.call_from_thread(self._apply_display, f"Error: {exc}", "")

    def action_open_bot_menu(self) -> None:
        def handle_result(result: tuple[str, str] | None) -> None:
            if result is None:
                return
            action, value = result
            if action == "bot":
                self.app.switch_screen(
                    RunScreen(
                        mode=self._mode,
                        maze_name=self._maze_name,
                        bot_name=value,
                        log_path=self._log_path,
                        max_moves=self._max_moves,
                    )
                )
            elif action == "log":
                self.app.switch_screen(RunScreen(mode="replay", log_path=value))

        self.app.push_screen(BotMenuScreen(), callback=handle_result)

    def action_reset_run(self) -> None:
        self.app.switch_screen(
            RunScreen(
                mode=self._mode,
                maze_name=self._maze_name,
                bot_name=self._bot_name,
                log_path=self._log_path,
                max_moves=self._max_moves,
            )
        )

    def action_quit_run(self) -> None:
        self.app.pop_screen()

    def action_exit_app(self) -> None:
        self.app.exit()

    def action_speed_up(self) -> None:
        self._delay = max(0.05, self._delay / 2)
        if self._replay_timer is not None:
            self._replay_timer.stop()
            self._replay_timer = self.set_interval(self._delay, self._advance_replay)

    def action_speed_down(self) -> None:
        self._delay = min(2.0, self._delay * 2)
        if self._replay_timer is not None:
            self._replay_timer.stop()
            self._replay_timer = self.set_interval(self._delay, self._advance_replay)


class MazeApp(App[None]):
    """Entry point for the Textual TUI. Pushes directly to RunScreen if args are provided."""

    def __init__(
        self,
        live: bool = False,
        maze_name: str | None = None,
        bot_name: str = "baseline",
        log_path: str | None = None,
        theme_name: str | None = None,
        connection_path: str = "connection.json",
    ) -> None:
        super().__init__()
        self.register_theme(SHADCN_DARK)
        self.register_theme(SHADCN_LIGHT)
        self._live = live
        self._maze_name = maze_name
        self._bot_name = bot_name
        self._log_path = log_path
        self._theme_name = theme_name
        self.connection_path = connection_path

    def on_mount(self) -> None:
        self.theme = self._theme_name or "shadcn-dark"
        if self._live and self._maze_name:
            self.push_screen(
                RunScreen(mode="live", maze_name=self._maze_name, bot_name=self._bot_name)
            )
        elif self._log_path:
            self.push_screen(RunScreen(mode="replay", log_path=self._log_path))
        else:
            self.push_screen(MainMenuScreen())
