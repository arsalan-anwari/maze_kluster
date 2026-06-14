from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from maze_kluster.models.features import (
    MODEL_DIR,
    TARGET_COL,
    load_model,
    prepare_features,
    save_model,
)

_DEFAULT_SAVE_PATH = MODEL_DIR / "gp.pkl"


class GPUCBScorer:
    """Gaussian Process scorer with UCB acquisition: score = mu + kappa * sigma."""

    def __init__(self, ucb_kappa: float = 2.0) -> None:
        self._ucb_kappa = ucb_kappa
        self._pipeline: Pipeline | None = None

    def _build_pipeline(self) -> Pipeline:
        # Without this fix the optimizer collapses length_scale to ~0 on this
        # dataset. Fixed at 1.0 (one std-dev in scaled space); only the
        # amplitude is free to optimize.
        kernel = ConstantKernel(1.0, (0.1, 100.0)) * RBF(
            length_scale=1.0, length_scale_bounds="fixed"
        )
        gpr = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-3,
            n_restarts_optimizer=5,
            random_state=42,
            normalize_y=True,
        )
        return Pipeline([("scaler", StandardScaler()), ("gpr", gpr)])

    def fit(self, parquet_path: Path = Path("data/maze_runs.parquet")) -> None:
        df = pd.read_parquet(parquet_path)
        X = prepare_features(df)
        y = df[TARGET_COL].to_numpy()
        self._pipeline = self._build_pipeline()
        self._pipeline.fit(X, y)

    def score(self, features: pd.DataFrame) -> list[float]:
        if self._pipeline is None:
            raise RuntimeError("GPUCBScorer not fitted or loaded")
        X = prepare_features(features)
        mu, sigma = self._pipeline.predict(X, return_std=True)
        return list(mu + self._ucb_kappa * sigma)

    def save(self, path: Path = _DEFAULT_SAVE_PATH) -> Path:
        if self._pipeline is None:
            raise RuntimeError("GPUCBScorer has no pipeline to save")
        return save_model(self._pipeline, path)

    @classmethod
    def load(cls, path: Path | None = None) -> GPUCBScorer:
        inst = cls()
        if path is not None:
            if not path.exists():
                raise FileNotFoundError(path)
            with path.open("rb") as f:
                import pickle

                inst._pipeline = pickle.load(f)  # noqa: S301
        else:
            inst._pipeline = load_model("gp.pkl")
        return inst
