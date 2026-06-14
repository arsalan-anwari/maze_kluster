Adding a New Bot
================

There are two paths depending on how much you want to control.

Path A: new ML scorer
----------------------

Use this if you want a different model but the same navigation loop. ``SmartBotBase``
handles all the graph traversal, backtracking, and data logging. You just provide
a scorer that ranks frontier tiles.

Implement :class:`~maze_kluster.models.protocol.ScorerProtocol`:

.. code-block:: python

   import pandas as pd

   class MyScorer:
       def score(self, features: pd.DataFrame) -> list[float]:
           # return one float per row; higher = visit this tile sooner
           return [1.0] * len(features)

Then register it in ``src/maze_kluster/bots/__init__.py``:

.. code-block:: python

   from my_package import MyScorer

   BOTS: dict[str, ...] = {
       "baseline": BaselineBot,
       "rf":       lambda client: SmartBotBase(client=client, scorer=RFScorer.load()),
       "my_bot":   lambda client: SmartBotBase(client=client, scorer=MyScorer()),
   }

``my_bot`` will now appear in the TUI menu and be usable via ``--bot my_bot``.

The features DataFrame passed to ``score()`` has one row per frontier tile and
these columns:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Column
     - Description
   * - ``actual_degree``
     - Number of edges on this tile (known connections)
   * - ``is_dead_end``
     - 1 if degree == 1
   * - ``neighbor_reward_mean``
     - Mean reward of adjacent tiles
   * - ``neighbor_reward_max``
     - Max reward of adjacent tiles
   * - ``unvisited_neighbors``
     - Count of adjacent tiles not yet visited
   * - ``tile_type_collectible``
     - 1 if tile is a collection point
   * - ``tile_type_exit``
     - 1 if tile is an exit

Path B: full custom bot
-------------------------

Use this when your navigation logic does not fit the frontier-scoring model. You
implement the entire run loop yourself.

Implement :class:`~maze_kluster.bots.base.BotProtocol`:

.. code-block:: python

   from maze_kluster.bots.base import RunResult
   from maze_kluster.enums import Direction
   from maze_kluster.graph import MazeGraph

   class MyBot:
       def __init__(self, client):
           self._client = client

       def run(self, maze_name: str, max_moves: int | None = None) -> RunResult:
           self._client.enter_maze(maze_name)
           # your exploration loop here
           ...

       def next_move(self, graph: MazeGraph) -> Direction:
           # return the next direction to move
           ...

Then register it the same way:

.. code-block:: python

   BOTS = {
       ...
       "my_bot": MyBot,
   }

No inheritance is needed. Both ``BotProtocol`` and ``ScorerProtocol`` use
structural typing, so any class with the right methods satisfies them.
