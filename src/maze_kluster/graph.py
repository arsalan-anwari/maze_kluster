from __future__ import annotations

from typing import TYPE_CHECKING, cast

import networkx as nx

from maze_kluster.enums import Direction, TileSymbol

if TYPE_CHECKING:
    from maze_kluster.api import Neighbor

DIRECTION_DELTA: dict[Direction, tuple[int, int]] = {
    Direction.Up:    (0, 1),
    Direction.Down:  (0, -1),
    Direction.Right: (1, 0),
    Direction.Left:  (-1, 0),
}

DELTA_TO_DIRECTION: dict[tuple[int, int], Direction] = {
    v: k for k, v in DIRECTION_DELTA.items()
}

OPPOSITE: dict[Direction, Direction] = {
    Direction.Up:    Direction.Down,
    Direction.Down:  Direction.Up,
    Direction.Left:  Direction.Right,
    Direction.Right: Direction.Left,
}


class MazeGraph:
    """Incrementally-built graph of the maze, updated as the bot explores.

    Coordinates use (x, y) with the start tile at (0, 0). y increases going up.
    """

    def __init__(self) -> None:
        self.graph: nx.Graph[tuple[int, int]] = nx.Graph()
        self.frontier: set[tuple[int, int]] = set()
        self.visited: set[tuple[int, int]] = set()
        self.current_pos: tuple[int, int] = (0, 0)

    def add_node(
        self,
        pos: tuple[int, int],
        tile_type: TileSymbol,
        reward: float,
        allows_exit: bool = False,
    ) -> None:
        if pos in self.graph.nodes:
            return
        self.graph.add_node(
            pos, tile_type=tile_type, reward=reward, visit_count=0, allows_exit=allows_exit
        )

    def add_edge(self, from_pos: tuple[int, int], to_pos: tuple[int, int]) -> None:
        if not self.graph.has_edge(from_pos, to_pos):
            self.graph.add_edge(from_pos, to_pos)

    def add_to_frontier(self, pos: tuple[int, int]) -> None:
        if pos not in self.visited:
            self.frontier.add(pos)

    def mark_visited(self, pos: tuple[int, int]) -> None:
        self.frontier.discard(pos)
        self.visited.add(pos)
        self.graph.nodes[pos]["visit_count"] += 1
        self.current_pos = pos

    def unvisited_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        return [n for n in self.graph.neighbors(pos) if n not in self.visited]

    def backtrack_target(self) -> tuple[int, int] | None:
        """Return the nearest unvisited frontier node by graph distance, or None if frontier is empty."""
        if not self.frontier:
            return None
        return min(
            self.frontier,
            key=lambda node: cast(
                int,
                nx.shortest_path_length(self.graph, self.current_pos, node),
            ),
        )

    def path_to(self, target: tuple[int, int]) -> list[Direction]:
        """Return the shortest direction sequence from current_pos to target."""
        if target == self.current_pos:
            return []
        raw_path = cast(
            list[tuple[int, int]],
            nx.shortest_path(self.graph, self.current_pos, target),
        )
        directions: list[Direction] = []
        for i in range(len(raw_path) - 1):
            a = raw_path[i]
            b = raw_path[i + 1]
            delta = (b[0] - a[0], b[1] - a[1])
            directions.append(DELTA_TO_DIRECTION[delta])
        return directions

    def nearest_exit(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        exits = [
            n for n in self.graph.nodes
            if self.graph.nodes[n].get("tile_type") == TileSymbol.Exit
            or self.graph.nodes[n].get("allows_exit")
        ]
        if not exits:
            return None
        return cast(
            tuple[int, int],
            min(exits, key=lambda n: cast(int, nx.shortest_path_length(self.graph, pos, n))),
        )

    def nearest_collectible(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        collectibles = [
            n for n in self.graph.nodes
            if self.graph.nodes[n].get("tile_type") == TileSymbol.Collectible
        ]
        if not collectibles:
            return None
        return cast(
            tuple[int, int],
            min(collectibles, key=lambda n: cast(int, nx.shortest_path_length(self.graph, pos, n))),
        )

    def apply_neighbors(
        self, neighbors: list[Neighbor], current_pos: tuple[int, int]
    ) -> None:
        """Sync the local graph with the neighbors reported by the API after a move."""
        for neighbor in neighbors:
            dx, dy = DIRECTION_DELTA[neighbor.direction]
            neighbor_pos = (current_pos[0] + dx, current_pos[1] + dy)
            if neighbor_pos in self.graph.nodes:
                self.add_edge(current_pos, neighbor_pos)
                if not neighbor.has_been_visited and neighbor_pos in self.visited:
                    self.frontier.add(neighbor_pos)
            else:
                self.add_node(
                    neighbor_pos, neighbor.tile_type, neighbor.reward, neighbor.allows_exit
                )
                self.add_edge(current_pos, neighbor_pos)
                if neighbor.has_been_visited:
                    self.visited.add(neighbor_pos)
                else:
                    self.add_to_frontier(neighbor_pos)
