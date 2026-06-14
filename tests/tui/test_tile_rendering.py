from __future__ import annotations

from maze_kluster.enums import RenderState, TileSymbol
from maze_kluster.graph import MazeGraph
from maze_kluster.tui.app import TILE_CHARS, TILE_COLORS, render_grid


def test_tile_chars_all_types_defined() -> None:
    for member in TileSymbol:
        assert member in TILE_CHARS
    for member in RenderState:
        assert member in TILE_CHARS


def test_tile_colors_all_types_defined() -> None:
    for member in TileSymbol:
        assert member in TILE_COLORS
    for member in RenderState:
        assert member in TILE_COLORS


def test_bot_position_renders_as_bot_char() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    graph.add_node((2, 0), TileSymbol.Exit, 0.0)
    graph.add_to_frontier((2, 0))

    output = render_grid(graph, bot_pos=(1, 0))

    assert TILE_CHARS[RenderState.BotPosition] in output


def test_frontier_tile_renders_as_question_mark() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    graph.add_node((2, 0), TileSymbol.Empty, 0.0)
    graph.add_to_frontier((2, 0))

    output = render_grid(graph, bot_pos=(0, 0))

    assert RenderState.Frontier.value in output


def test_visited_tile_renders_as_tile_type() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    graph.add_node((1, 0), TileSymbol.Collectible, 5.0)
    graph.mark_visited((1, 0))

    output = render_grid(graph, bot_pos=(0, 0))

    assert TileSymbol.Collectible.value in output


def test_unexplored_renders_as_space() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    graph.add_node((2, 0), TileSymbol.Exit, 0.0)
    graph.add_to_frontier((2, 0))

    output = render_grid(graph, bot_pos=(0, 0))

    assert RenderState.Unexplored.value in output


def test_grid_y_axis_inverted() -> None:
    graph = MazeGraph()
    graph.add_node((0, 0), TileSymbol.Start, 0.0)
    graph.mark_visited((0, 0))
    graph.add_node((0, 1), TileSymbol.Exit, 0.0)
    graph.mark_visited((0, 1))

    output = render_grid(graph, bot_pos=(-99, -99))
    lines = output.split("\n")

    assert TileSymbol.Exit.value in lines[0]
    assert TileSymbol.Start.value in lines[1]


def test_empty_graph_returns_placeholder() -> None:
    graph = MazeGraph()
    output = render_grid(graph, bot_pos=(0, 0))
    assert output == "(empty)"
