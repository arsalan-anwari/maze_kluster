from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from maze_kluster.enums import TileSymbol

rng = np.random.default_rng(42)

df = pd.DataFrame(
    {
        "maze_name": ["Hello Maze"] * 8 + ["Exit"] * 12,
        "tile_x": rng.integers(-3, 4, size=20).astype("int64"),
        "tile_y": rng.integers(-3, 4, size=20).astype("int64"),
        "reward": rng.uniform(0, 20, size=20),
        "tile_type": rng.choice([t.value for t in TileSymbol], size=20),
        "actual_degree": rng.integers(1, 5, size=20).astype("int64"),
        "is_dead_end": rng.choice([True, False], size=20),
        "visit_order": np.arange(1, 21, dtype="int64"),
        "times_visited": np.ones(20, dtype="int64"),
        "neighbor_reward_mean": rng.uniform(0, 15, size=20),
        "neighbor_reward_max": rng.uniform(5, 20, size=20),
        "unvisited_neighbors": rng.integers(0, 4, size=20).astype("int64"),
        "maze_total_tiles": [8] * 8 + [11] * 12,
        "maze_potential_reward": [52.0] * 8 + [82.0] * 12,
    }
)

out = Path(__file__).parent / "sample_runs.parquet"
df.to_parquet(out, index=False)
print(f"Wrote {len(df)} rows to {out}")
