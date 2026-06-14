from __future__ import annotations

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class ScorerProtocol(Protocol):
    def score(self, features: pd.DataFrame) -> list[float]:
        """Return one priority score per row. Higher = more desirable frontier tile."""
        ...
