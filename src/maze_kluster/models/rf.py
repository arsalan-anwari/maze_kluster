from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from maze_kluster.models.features import (
    FEATURE_COLS,
    MODEL_DIR,
    TARGET_COL,
    load_model,
    prepare_features,
    save_model,
)

_DEFAULT_SAVE_PATH = MODEL_DIR / "rf.pkl"


class RFScorer:
    """Random Forest regressor trained on tile visit data to predict tile reward."""

    def __init__(self) -> None:
        self._model: RandomForestRegressor | None = None

    def fit(self, parquet_path: Path = Path("data/maze_runs.parquet")) -> None:
        df = pd.read_parquet(parquet_path)
        X = prepare_features(df)
        y = df[TARGET_COL].to_numpy()
        self._model = RandomForestRegressor(n_estimators=100, random_state=42)
        self._model.fit(X, y)

    def score(self, features: pd.DataFrame) -> list[float]:
        if self._model is None:
            raise RuntimeError("RFScorer not fitted or loaded")
        return list(self._model.predict(prepare_features(features)))

    def feature_importances(self) -> dict[str, float]:
        """Return feature name -> importance mapping from the fitted forest."""
        if self._model is None:
            raise RuntimeError("RFScorer not fitted or loaded")
        return dict(zip(FEATURE_COLS, self._model.feature_importances_))

    def save(self, path: Path = _DEFAULT_SAVE_PATH) -> Path:
        if self._model is None:
            raise RuntimeError("RFScorer has no model to save")
        return save_model(self._model, path)

    @classmethod
    def load(cls) -> RFScorer:
        inst = cls()
        inst._model = load_model("rf.pkl")
        return inst
