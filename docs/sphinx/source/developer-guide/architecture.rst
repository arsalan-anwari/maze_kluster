Architecture
============

The library has four layers, each with a clear boundary so you can swap or
extend any one without touching the others.

.. code-block:: text

   connection.json
       |
       v
   MazeClient  (api.py)         -- HTTP calls to the maze API
       |
       v
   MazeGraph   (graph.py)       -- NetworkX graph, built tile by tile
       |
       v
   Bot         (bots/)          -- navigation logic; reads graph, writes moves
       |
       v
   TileLogger / RunLog          -- records visits and steps to disk
   (data/collector.py)

Packages
--------

**maze_kluster.api**
  Wraps the HTTP client. ``MazeClient`` is the only way data enters the system.
  All API responses are validated with Pydantic before anything else sees them.

**maze_kluster.graph**
  ``MazeGraph`` holds the NetworkX graph and two sets: ``visited`` and
  ``frontier``. It grows one tile at a time as the bot moves. Uses
  ``nx.shortest_path`` for backtracking and navigation.

**maze_kluster.bots**
  Two concrete bots and a registry. ``BaselineBot`` uses iterative DFS.
  ``SmartBotBase`` uses a scorer to rank frontier tiles. The ``BOTS`` dict
  maps bot names to factories and is shared by the CLI and the TUI.

**maze_kluster.models**
  Three scorer implementations (RF, GBT, GP) and the ``ScorerProtocol`` they
  implement. Feature preparation is centralized in ``features.py`` so all
  scorers get consistent input.

**maze_kluster.data**
  ``TileLogger`` buffers per-tile records and flushes them to parquet.
  ``RunLog`` writes a step-by-step JSONL trace for replay.

**maze_kluster.tui**
  Textual-based terminal UI. Reads ``BOTS`` from the bots package so new bots
  appear in the menu automatically.

Extension points
----------------

There are two ways to extend the library. See the following pages for details:

- :doc:`adding-a-bot`: add a new navigation strategy
- :doc:`adding-a-scorer`: add a new ML scorer for the smart bot
