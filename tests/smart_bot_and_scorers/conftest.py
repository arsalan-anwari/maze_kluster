from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_PARQUET = Path("tests/fixtures/sample_runs.parquet")


@pytest.fixture
def fixture_parquet() -> Path:
    return FIXTURE_PARQUET
