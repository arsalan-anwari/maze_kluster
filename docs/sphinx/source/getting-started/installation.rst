Installation
============

Python 3.11 or newer is required.

Base install
------------

Installs the bots and data collection layer. No terminal UI.

.. code-block:: bash

   pip install maze-kluster

With the terminal UI
--------------------

.. code-block:: bash

   pip install maze-kluster[tui]

Development install
-------------------

Clone the repo and install in editable mode with all dev tools included.

.. code-block:: bash

   git clone https://github.com/arsalan-anwari/maze_kluster
   cd maze_kluster
   pip install -e ".[dev]"

The ``dev`` extra includes the TUI, test dependencies, mypy, and ruff.
