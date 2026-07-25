"""Tests for the shared technical indicators."""

import pandas as pd

from alphapulse.strategy.indicators import bollinger_bands, ema, macd, rsi, sma


def _series(n: int = 60) -> pd.Series:
    return pd.Series([100 + (i % 7) * 2 for i in range(n)], dtype=float)


def test_ema_and_sma_lengths():
    s = _series(30)
    assert len(ema(s, 9)) == 30
    assert len(sma(s, 5)) == 30


def test_rsi_bounded_0_100():
    r = rsi(_series(60)).dropna()
    assert not r.empty
    assert (r >= 0).all() and (r <= 100).all()


def test_macd_returns_three_aligned_series():
    macd_line, signal_line, hist = macd(_series(60))
    assert len(macd_line) == len(signal_line) == len(hist) == 60
    assert ((macd_line - signal_line) - hist).abs().max() < 1e-9


def test_bollinger_ordering():
    middle, upper, lower = bollinger_bands(_series(60), period=20)
    valid = middle.dropna().index
    assert (upper.loc[valid] >= middle.loc[valid]).all()
    assert (middle.loc[valid] >= lower.loc[valid]).all()
