from __future__ import annotations

from typing import cast

import networkx as nx

from maze_kluster.api import MazeClient
from maze_kluster.bots.base import RunResult
from maze_kluster.data.collector import RunLog, TileLogger
from maze_kluster.enums import Direction, TileSymbol
from maze_kluster.graph import DIRECTION_DELTA, MazeGraph


class BaselineBot:
    """DFS-based bot that explores the whole maze before heading for the exit.

    Picks adjacent unvisited frontier nodes first; backtracks via shortest path
    when none are adjacent. Collects score on the spot; exits when the frontier
    is empty or max_moves is reached.
    """

    def __init__(
        self,
        client: MazeClient,
        logger: TileLogger | None = None,
        runlog: RunLog | None = None,
        bot_name: str = "baseline",
    ) -> None:
        self._client = client
        self._logger = logger
        self._runlog = runlog
        self._bot_name = bot_name

    @classmethod
    def with_logging(
        cls,
        client: MazeClient,
        maze_name: str,
        total_tiles: int,
        potential_reward: float,
        bot_name: str = "baseline",
    ) -> BaselineBot:
        """Convenience constructor that wires up a TileLogger and RunLog automatically."""
        logger = TileLogger(maze_name, total_tiles, potential_reward)
        runlog = RunLog(maze_name, bot_name)
        return cls(client=client, logger=logger, runlog=runlog, bot_name=bot_name)

    def run(self, maze_name: str, max_moves: int | None = None) -> RunResult:
        mazes = self._client.all_mazes()
        maze_info = next((m for m in mazes if m.name == maze_name), None)
        total_tiles = maze_info.total_tiles if maze_info is not None else 0
        potential_reward = maze_info.potential_reward if maze_info is not None else 0.0

        self._client.enter_maze(maze_name)

        graph = MazeGraph()
        graph.add_node((0, 0), TileSymbol.Start, 0.0)
        graph.mark_visited((0, 0))
        known_exits: set[tuple[int, int]] = set()

        response = self._client.possible_actions()
        graph.apply_neighbors(response.neighbors, (0, 0))

        unique_visit_count = 1
        if self._logger:
            self._logger.record_visit(graph, (0, 0), unique_visit_count)

        total_moves = 0

        while True:
            score_in_hand = response.score_in_hand
            if response.can_collect_score and score_in_hand > 0:
                self._client.collect_score()
                score_in_hand = 0.0

            if response.can_exit:
                known_exits.add(graph.current_pos)
                graph.graph.nodes[graph.current_pos]["allows_exit"] = True

            exit_known = bool(known_exits) or graph.nearest_exit(graph.current_pos) is not None
            collectible_reachable = graph.nearest_collectible(graph.current_pos) is not None
            force_exit = (
                max_moves is not None
                and total_moves >= max_moves
                and exit_known
                and (score_in_hand == 0 or collectible_reachable)
            )

            if response.can_exit and (not graph.frontier or force_exit):
                if score_in_hand == 0 or graph.nearest_collectible(graph.current_pos) is None:
                    self._client.exit_maze()
                    break

            direction = self.next_move(graph, known_exits, score_in_hand, force_exit)
            response = self._client.move(direction)
            total_moves += 1

            dx, dy = DIRECTION_DELTA[direction]
            new_pos = (graph.current_pos[0] + dx, graph.current_pos[1] + dy)
            graph.mark_visited(new_pos)
            graph.apply_neighbors(response.neighbors, new_pos)

            if graph.graph.nodes[new_pos]["visit_count"] == 1:
                unique_visit_count += 1
                if self._logger:
                    self._logger.record_visit(graph, new_pos, unique_visit_count)

            if self._runlog:
                self._runlog.record_step(
                    pos=new_pos,
                    tile_type=graph.graph.nodes[new_pos]["tile_type"],
                    score_in_hand=response.score_in_hand,
                    score_in_bag=response.score_in_bag,
                    frontier_size=len(graph.frontier),
                )

        if self._logger:
            self._logger.flush()
        if self._runlog:
            self._runlog.close()

        return RunResult(
            maze_name=maze_name,
            score_in_bag=response.score_in_bag,
            score_lost=response.score_in_hand,
            total_moves=total_moves,
            tiles_visited=len(graph.visited),
            total_tiles=total_tiles,
            potential_reward=potential_reward,
        )

    def next_move(
        self,
        graph: MazeGraph,
        known_exits: set[tuple[int, int]] | None = None,
        score_in_hand: float = 0.0,
        force_exit: bool = False,
    ) -> Direction:
        """Pick the next direction: explore, backtrack, collect, or head for exit."""
        adjacent_frontier = [
            n for n in graph.unvisited_neighbors(graph.current_pos) if n in graph.frontier
        ]

        if not force_exit and adjacent_frontier:
            target: tuple[int, int] = adjacent_frontier[0]
        elif not force_exit and graph.frontier:
            maybe_target = graph.backtrack_target()
            if maybe_target is None:
                raise RuntimeError("Frontier non-empty but no backtrack target found")
            target = maybe_target
        else:
            if score_in_hand > 0:
                collectible = graph.nearest_collectible(graph.current_pos)
                if collectible is not None:
                    target = collectible
                    path = graph.path_to(target)
                    return path[0]

            exit_target = graph.nearest_exit(graph.current_pos)
            if exit_target is None and known_exits:
                exit_target = min(
                    known_exits,
                    key=lambda n: cast(
                        int, nx.shortest_path_length(graph.graph, graph.current_pos, n)
                    ),
                )
            if exit_target is None:
                raise RuntimeError("No exit tile found in graph")
            target = exit_target

        path = graph.path_to(target)
        return path[0]
