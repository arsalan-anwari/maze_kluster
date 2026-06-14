Adding a New Scorer
===================

A scorer is any class that implements :class:`~maze_kluster.models.protocol.ScorerProtocol`.

.. code-block:: python

   class ScorerProtocol(Protocol):
       def score(self, features: pd.DataFrame) -> list[float]: ...

The ``score`` method receives a DataFrame of frontier tile features and returns
one float per row. Higher scores mean the bot visits that tile sooner.

Minimal example
---------------

.. code-block:: python

   class RandomScorer:
       """Picks tiles at random (for testing)."""

       def score(self, features: pd.DataFrame) -> list[float]:
           import random
           return [random.random() for _ in range(len(features))]

Scorer with training and persistence
-------------------------------------

If your scorer needs to be trained and saved to disk, follow the same pattern
as the built-in scorers. ``RFScorer`` in ``models/rf.py`` is a good reference.

.. code-block:: python

   from pathlib import Path
   import pandas as pd
   from maze_kluster.models.features import prepare_features, save_model, load_model, TARGET_COL

   class MyScorer:
       def __init__(self) -> None:
           self._model = None

       def fit(self, parquet_path: Path = Path("data/maze_runs.parquet")) -> None:
           df = pd.read_parquet(parquet_path)
           X = prepare_features(df)         # returns a DataFrame with FEATURE_COLS
           y = df[TARGET_COL].to_numpy()    # TARGET_COL = "reward"
           self._model = ...                # train your model
           self._model.fit(X, y)

       def score(self, features: pd.DataFrame) -> list[float]:
           X = prepare_features(features)
           return list(self._model.predict(X))

       def save(self, path: Path = Path("models/my_scorer.pkl")) -> Path:
           return save_model(self._model, path)

       @classmethod
       def load(cls) -> "MyScorer":
           inst = cls()
           inst._model = load_model("my_scorer.pkl")
           return inst

``prepare_features`` handles one-hot encoding of ``tile_type`` and filters the
DataFrame to exactly the columns in ``FEATURE_COLS``. Always call it on both
training data and inference data so the shapes match.

Feature columns
---------------

See :ref:`exploration-feature-selection` for the rationale behind each feature
and why ``tile_type_reward`` and ``tile_type_empty`` are excluded.
