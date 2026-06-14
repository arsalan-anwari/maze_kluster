from __future__ import annotations

import pickle
from importlib.resources import files
from pathlib import Path
from typing import Any

import pandas as pd

from maze_kluster.enums import TileSymbol

_TYPE_LABELS: dict[str, str] = {t.value: t.name.lower() for t in TileSymbol}

FEATURE_COLS: list[str] = [
    "actual_degree",
    "is_dead_end",
    "neighbor_reward_mean",
    "neighbor_reward_max",
    "unvisited_neighbors",
    "tile_type_collectible",
    "tile_type_exit",
]

TARGET_COL = "reward"
MODEL_DIR = Path("models")


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode tile_type and return only FEATURE_COLS."""
    df = df.copy()
    labels = df["tile_type"].map(_TYPE_LABELS)
    dummies = pd.get_dummies(labels, prefix="tile_type", drop_first=False)
    for col in ("tile_type_collectible", "tile_type_exit"):
        if col not in dummies.columns:
            dummies[col] = 0
    dummies = dummies.drop(
        columns=["tile_type_reward", "tile_type_empty", "tile_type_start"],
        errors="ignore",
    )
    df = pd.concat([df, dummies], axis=1)
    df["is_dead_end"] = df["is_dead_end"].astype(int)
    available = [c for c in FEATURE_COLS if c in df.columns]
    return df[available]


def save_model(obj: Any, path: Path) -> Path:
    """Pickle an object to path, creating the models directory if needed."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(obj, f)
    return path


def load_model(name: str) -> Any:
    """Load a pickled model by filename.

    Tries models/<name> relative to the working directory first, then falls
    back to the bundled package data.
    """
    local = MODEL_DIR / name
    if local.exists():
        with local.open("rb") as f:
            return pickle.load(f)  # noqa: S301
    with files("maze_kluster.models").joinpath(f"data/{name}").open("rb") as f:
        return pickle.load(f)  # noqa: S301
