from __future__ import annotations

from enum import StrEnum


class TileSymbol(StrEnum):
    Start = "S"
    Reward = "o"
    Empty = "x"
    Collectible = "C"
    Exit = "E"


class Direction(StrEnum):
    Up = "Up"
    Down = "Down"
    Left = "Left"
    Right = "Right"


class RenderState(StrEnum):
    """Pseudo-tile states used only for TUI rendering, not part of the maze schema."""

    Frontier = "?"
    BotPosition = "■"
    Unexplored = " "
