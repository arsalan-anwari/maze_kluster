Setup
=====

The bots connect to the maze API using a ``connection.json`` file. Place it in
your working directory before running anything.

.. code-block:: text

   {
     "base_url": "https://maze.kluster.htiprojects.nl",
     "api_key": "HTI Thanks You [{some-token}]",
     "player": {
       "id": {some-player-id},
       "name": "{some-name}"
     }
   }

The ``api_key`` field accepts ``${ENV_VAR}`` syntax if you prefer to keep the
token out of the file:

.. code-block:: text

   {
     "base_url": "https://maze.kluster.htiprojects.nl",
     "api_key": "${MAZE_API_KEY}",
     "player": { "id": {some-player-id}, "name": "{some-name}" }
   }

Then set the variable in your shell before running:

.. code-block:: bash

   export MAZE_API_KEY="HTI Thanks You [{some-token}]"

Verify the connection
---------------------

List available mazes to confirm the API is reachable:

.. code-block:: bash

   maze-kluster tui --list-mazes

You should see maze names printed to stdout. If you get an authentication error,
check the ``api_key`` value in ``connection.json``.
