CLI Reference
=============

The ``maze-kluster tui`` command launches the terminal UI. All flags are optional.

.. code-block:: bash

   maze-kluster tui [OPTIONS]

Flags
-----

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Flag
     - Default
     - Description
   * - ``--live``
     - off
     - Start a live run immediately (skips the main menu)
   * - ``--maze NAME``
     - None
     - Maze name to use with ``--live``
   * - ``--bot NAME``
     - ``baseline``
     - Bot to use. One of: ``baseline``, ``rf``, ``gbt``, ``gp``
   * - ``--replay PATH``
     - None
     - Load a JSONL run log and enter replay mode
   * - ``--theme NAME``
     - None
     - Color theme for the TUI. See ``--list-themes``
   * - ``--connection PATH``
     - ``connection.json``
     - Path to the connection config file
   * - ``--list-mazes``
     - -
     - Print available maze names and exit
   * - ``--list-themes``
     - -
     - Print available theme names and exit

Two custom themes are included: ``shadcn-dark`` and ``shadcn-light``. Both use
brown (``#916f6f``) as the accent color with a high-contrast black or white background.

Examples
--------

Open the interactive menu:

.. code-block:: bash

   maze-kluster tui

Start a live run directly, skipping the menu:

.. code-block:: bash

   maze-kluster tui --live --maze "Gradius Pathways" --bot rf

Replay a previously recorded run:

.. code-block:: bash

   maze-kluster tui --replay data/runs/gradius_rf_20260613.jsonl

Use a non-default connection file:

.. code-block:: bash

   maze-kluster tui --connection /path/to/my_connection.json

Use a custom theme:

.. code-block:: bash

   maze-kluster tui --theme shadcn-dark
