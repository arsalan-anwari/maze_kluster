from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from maze_kluster.enums import TileSymbol
from maze_kluster.models.features import FEATURE_COLS, prepare_features
from maze_kluster.models.gbt import GBTScorer
from maze_kluster.models.gp import GPUCBScorer
from maze_kluster.models.protocol import ScorerProtocol
from maze_kluster.models.rf import RFScorer

_SAMPLE_FEATURES = pd.DataFrame(
    {
        "tile_type": [TileSymbol.Reward, TileSymbol.Empty, TileSymbol.Collectible],
        "actual_degree": [2, 1, 3],
        "is_dead_end": [False, True, False],
        "neighbor_reward_mean": [5.0, 0.0, 2.5],
        "neighbor_reward_max": [10.0, 0.0, 5.0],
        "unvisited_neighbors": [1, 0, 2],
    }
)


class TestRFScorer:
    def test_fit_succeeds(self, fixture_parquet: Path) -> None:
        scorer = RFScorer()
        scorer.fit(fixture_parquet)
        assert scorer._model is not None

    def test_score_returns_floats(self, fixture_parquet: Path) -> None:
        scorer = RFScorer()
        scorer.fit(fixture_parquet)
        result = scorer.score(_SAMPLE_FEATURES)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)

    def test_score_shape(self, fixture_parquet: Path) -> None:
        scorer = RFScorer()
        scorer.fit(fixture_parquet)
        df = pd.concat([_SAMPLE_FEATURES] * 4, ignore_index=True)
        result = scorer.score(df)
        assert len(result) == 12

    def test_feature_importances(self, fixture_parquet: Path) -> None:
        scorer = RFScorer()
        scorer.fit(fixture_parquet)
        importances = scorer.feature_importances()
        assert isinstance(importances, dict)
        assert set(importances.keys()) == set(FEATURE_COLS)
        assert sum(importances.values()) == pytest.approx(1.0, abs=0.01)

    def test_save_load_roundtrip(self, fixture_parquet: Path, tmp_path: Path) -> None:
        scorer = RFScorer()
        scorer.fit(fixture_parquet)
        scorer.save(tmp_path / "rf.pkl")
        loaded = RFScorer.load(tmp_path / "rf.pkl")
        original_scores = scorer.score(_SAMPLE_FEATURES)
        loaded_scores = loaded.score(_SAMPLE_FEATURES)
        assert original_scores == loaded_scores

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            RFScorer.load(Path("nonexistent_rf.pkl"))

    def test_score_raises_before_fit(self) -> None:
        with pytest.raises(RuntimeError):
            RFScorer().score(_SAMPLE_FEATURES)


class TestGBTScorer:
    def test_fit_succeeds(self, fixture_parquet: Path) -> None:
        scorer = GBTScorer(early_stopping=False)
        scorer.fit(fixture_parquet)
        assert scorer._model is not None

    def test_score_returns_floats(self, fixture_parquet: Path) -> None:
        scorer = GBTScorer(early_stopping=False)
        scorer.fit(fixture_parquet)
        result = scorer.score(_SAMPLE_FEATURES)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)

    def test_save_load_roundtrip(self, fixture_parquet: Path, tmp_path: Path) -> None:
        scorer = GBTScorer(early_stopping=False)
        scorer.fit(fixture_parquet)
        scorer.save(tmp_path / "gbt.pkl")
        loaded = GBTScorer.load(tmp_path / "gbt.pkl")
        original_scores = scorer.score(_SAMPLE_FEATURES)
        loaded_scores = loaded.score(_SAMPLE_FEATURES)
        assert original_scores == loaded_scores

    def test_score_raises_before_fit(self) -> None:
        with pytest.raises(RuntimeError):
            GBTScorer().score(_SAMPLE_FEATURES)


class TestGPUCBScorer:
    def test_fit_succeeds(self, fixture_parquet: Path) -> None:
        scorer = GPUCBScorer()
        scorer.fit(fixture_parquet)
        assert scorer._pipeline is not None

    def test_score_returns_floats(self, fixture_parquet: Path) -> None:
        scorer = GPUCBScorer()
        scorer.fit(fixture_parquet)
        result = scorer.score(_SAMPLE_FEATURES)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)

    def test_ucb_exceeds_mean(self, fixture_parquet: Path) -> None:
        scorer = GPUCBScorer()
        scorer.fit(fixture_parquet)
        assert scorer._pipeline is not None
        X = prepare_features(_SAMPLE_FEATURES)
        mu = scorer._pipeline.predict(X, return_std=False)
        ucb = scorer.score(_SAMPLE_FEATURES)
        for u, m in zip(ucb, mu):
            assert u >= m

    def test_save_load_roundtrip(self, fixture_parquet: Path, tmp_path: Path) -> None:
        scorer = GPUCBScorer()
        scorer.fit(fixture_parquet)
        scorer.save(tmp_path / "gp.pkl")
        loaded = GPUCBScorer.load(tmp_path / "gp.pkl")
        original_scores = scorer.score(_SAMPLE_FEATURES)
        loaded_scores = loaded.score(_SAMPLE_FEATURES)
        assert original_scores == pytest.approx(loaded_scores)

    def test_score_raises_before_fit(self) -> None:
        with pytest.raises(RuntimeError):
            GPUCBScorer().score(_SAMPLE_FEATURES)


@pytest.mark.parametrize(
    "scorer_cls,kwargs",
    [
        (RFScorer, {}),
        (GBTScorer, {"early_stopping": False}),
        (GPUCBScorer, {}),
    ],
)
def test_scorer_satisfies_protocol(
    scorer_cls: type,
    kwargs: dict[str, object],
    fixture_parquet: Path,
) -> None:
    scorer = scorer_cls(**kwargs)
    scorer.fit(fixture_parquet)
    assert isinstance(scorer, ScorerProtocol)


class TestPrepareFeatures:
    def test_missing_tile_types_filled(self) -> None:
        df = pd.DataFrame(
            {
                "tile_type": [TileSymbol.Reward, TileSymbol.Reward],
                "actual_degree": [2, 3],
                "is_dead_end": [False, False],
                "neighbor_reward_mean": [1.0, 2.0],
                "neighbor_reward_max": [5.0, 6.0],
                "unvisited_neighbors": [1, 2],
            }
        )
        result = prepare_features(df)
        assert "tile_type_collectible" in result.columns
        assert "tile_type_exit" in result.columns
        assert (result["tile_type_collectible"] == 0).all()
        assert (result["tile_type_exit"] == 0).all()

    def test_circular_columns_excluded(self) -> None:
        df = pd.DataFrame(
            {
                "tile_type": [TileSymbol.Reward, TileSymbol.Empty, TileSymbol.Exit],
                "actual_degree": [1, 2, 3],
                "is_dead_end": [True, False, False],
                "neighbor_reward_mean": [0.0, 0.0, 0.0],
                "neighbor_reward_max": [0.0, 0.0, 0.0],
                "unvisited_neighbors": [0, 1, 2],
            }
        )
        result = prepare_features(df)
        assert "tile_type_reward" not in result.columns
        assert "tile_type_empty" not in result.columns
