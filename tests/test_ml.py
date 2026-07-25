"""Tests for feature engineering and the ML signal filter."""

from datetime import datetime, timedelta

import pandas as pd

from alphapulse.strategy import process_market_data
from alphapulse.strategy.features import (
    FEATURE_COLUMNS,
    add_features,
    build_training_set,
    latest_feature_row,
)
from alphapulse.strategy.ml_filter import MLSignalFilter


def _make_candles(n: int = 60) -> pd.DataFrame:
    start = datetime(2025, 6, 2, 9, 15)
    closes = [100 + (i % 9) * 2 for i in range(n)]
    return pd.DataFrame({
        "Timestamp": [start + timedelta(minutes=5 * i) for i in range(n)],
        "Open": closes,
        "High": [c + 3 for c in closes],
        "Low": [c - 3 for c in closes],
        "Close": closes,
        "Volume": [1_000_000 + i * 100 for i in range(n)],
        "Open Interest": [0] * n,
    })


def test_add_features_creates_all_columns():
    featured = add_features(_make_candles())
    for col in FEATURE_COLUMNS:
        assert col in featured.columns


def test_build_training_set_shapes_align():
    X, y = build_training_set(_make_candles())
    assert len(X) == len(y)
    assert list(X.columns) == FEATURE_COLUMNS
    assert set(y.unique()) <= {0, 1}


def test_latest_feature_row_single_row():
    row = latest_feature_row(_make_candles())
    assert row is not None
    assert len(row) == 1


def test_disabled_filter_passes_signals_through():
    flt = MLSignalFilter(model=None)
    assert flt.enabled is False
    assert flt.apply("buy", _make_candles()) == "buy"
    assert flt.apply("sell", _make_candles()) == "sell"


def test_filter_can_veto_buy_below_threshold():
    class LowUpModel:
        def predict_proba(self, X):
            return [[0.9, 0.1]]  # P(up) = 0.1

    flt = MLSignalFilter(model=LowUpModel(), buy_threshold=0.52)
    assert flt.apply("buy", _make_candles()) == "hold"


def test_filter_allows_buy_above_threshold():
    class HighUpModel:
        def predict_proba(self, X):
            return [[0.2, 0.8]]  # P(up) = 0.8

    flt = MLSignalFilter(model=HighUpModel(), buy_threshold=0.52)
    assert flt.apply("buy", _make_candles()) == "buy"


def test_process_market_data_accepts_filter():
    candles = _make_candles()
    assert process_market_data(candles, ml_filter=MLSignalFilter(model=None)) in {"buy", "sell", "hold"}
