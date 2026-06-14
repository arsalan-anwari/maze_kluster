Generating Data and Models
==========================

The baseline bot works out of the box. The smart bots (RF, GBT, GP) need trained
model files to run. Follow these two steps to generate them.

.. note::
   Skip this if you only want to use the baseline bot or replay existing run logs.

Step 1: collect training data
-------------------------------

Run the baseline bot across all training mazes and save tile visit records to
``data/maze_runs.parquet``.

.. code-block:: bash

   python data/generate.py

Each maze can only be completed once per player session. If a maze is already
done, the script skips it. Use ``--reset`` to wipe all progress and start over:

.. code-block:: bash

   python data/generate.py --reset

The training mazes are: Hello Maze, Exit, Loops, Easy deal, Michiel, Dig Down, Egg.

Step 2: train the models
--------------------------

Train all three scorers and save them to ``models/``.

.. code-block:: bash

   python models/generate.py

This reads ``data/maze_runs.parquet`` and writes:

- ``models/rf.pkl``: Random Forest
- ``models/gbt.pkl``: Gradient Boosted Trees
- ``models/gp.pkl``: Gaussian Process

The script also prints RF feature importances so you can verify the training ran
correctly.

After this, the TUI and the smart bots will automatically pick up the model files.
