from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from maze_kluster.models.features import (
    MODEL_DIR,
    TARGET_COL,
    load_model,
    prepare_features,
    save_model,
)

_DEFAULT_SAVE_PATH = MODEL_DIR / "gbt.pkl"


class GBTScorer:
    """Histogram Gradient Boosting regressor, faster than RF on larger datasets."""

    def __init__(self, early_stopping: bool = True) -> None:
        self._early_stopping = early_stopping
        self._model: HistGradientBoostingRegressor | None = None

    def fit(self, parquet_path: Path = Path("data/maze_runs.parquet")) -> None:
        df = pd.read_parquet(parquet_path)
        X = prepare_features(df)
        y = df[TARGET_COL].to_numpy()
        self._model = HistGradientBoostingRegressor(
            early_stopping=self._early_stopping,
            random_state=42,
        )
        self._model.fit(X, y)

    def score(self, features: pd.DataFrame) -> list[float]:
        if self._model is None:
            raise RuntimeError("GBTScorer not fitted or loaded")
        return list(self._model.predict(prepare_features(features)))

    def save(self, path: Path = _DEFAULT_SAVE_PATH) -> Path:
        if self._model is None:
            raise RuntimeError("GBTScorer has no model to save")
        return save_model(self._model, path)

    @classmethod
    def load(cls) -> GBTScorer:
        inst = cls()
        inst._model = load_model("gbt.pkl")
        return inst
