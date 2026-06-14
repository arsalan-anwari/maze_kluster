Evaluation
==========

We compared the baseline bot (DFS) against the three smart bots on four held-out
evaluation mazes: Gradius Pathways, O Contra, Glasses, and Reverse. None of these
appeared in training.

Metrics
-------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Metric
     - Formula
     - What it shows
   * - Score efficiency
     - score collected / potential reward
     - How much of the available reward was captured
   * - Step efficiency
     - score collected / total moves
     - Reward earned per API call
   * - Collection rate
     - score in bag / (score in bag + score lost on exit)
     - How consistently the bot bags score before exiting
   * - Exploration completeness
     - tiles visited / total tiles
     - Whether the bot fully explored the maze

Baseline vs smart bots
-----------------------

The baseline explores every tile before exiting, so its score efficiency is near
100%. The smart bots prioritize high-value tiles first, so they reach the same
reward in fewer moves. That difference is visible in step efficiency.

.. image:: ../../res/analysis/evaluate/unlimited-budget-runs-dfs-vs-smart-bots.svg
   :alt: Unlimited budget runs comparison
   :width: 100%

The real advantage becomes clear when a move budget is imposed. With a limited
number of moves, the smart bot has already visited the most valuable tiles, so it
exits with more score. The baseline, which visits tiles in graph order, may not
have reached the high-reward areas yet.

.. image:: ../../res/analysis/evaluate/score-efficiency-bot-x-budget-per-maze.svg
   :alt: Score efficiency per bot and budget per maze
   :width: 100%

.. image:: ../../res/analysis/evaluate/score-efficiency-vs-moves-used-per-budget.svg
   :alt: Score efficiency vs moves used per budget
   :width: 100%

.. image:: ../../res/analysis/evaluate/step-efficiency-vs-move-budget.svg
   :alt: Step efficiency vs move budget
   :width: 100%

.. image:: ../../res/analysis/evaluate/actual-moves-used-vs-move-budget-setting.svg
   :alt: Actual moves used vs move budget
   :width: 100%

.. image:: ../../res/analysis/evaluate/exploration-completeness-vs-move-budget.svg
   :alt: Exploration completeness vs move budget
   :width: 100%

Feature importances
-------------------

The RF model confirms that ``neighbor_reward_mean`` is by far the most informative
feature (importance ~0.53), consistent with the Pearson correlation found during
exploration. The next most informative features are ``tile_type_exit`` (~0.11) and
``tile_type_collectible`` (~0.09). Notably, ``neighbor_reward_max`` is the least
informative feature (~0.02) despite being a neighbor-reward statistic.

.. image:: ../../res/analysis/evaluate/rf-feature-importances.svg
   :alt: RF feature importances
   :width: 100%
