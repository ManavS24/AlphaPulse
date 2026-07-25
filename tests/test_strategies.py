"""Tests for the trading strategies and the strategy registry."""

import pandas as pd
import pytest

from alphapulse.strategy import (
    DEFAULT_STRATEGY,
    STRATEGIES,
    bollinger_strategy,
    get_strategy,
    macd_strategy,
    process_market_data,
    rsi_strategy,
)


def _df(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame({
        "Open": closes,
        "High": [c + 1 for c in closes],
        "Low": [c - 1 for c in closes],
        "Close": closes,
        "Volume": [1_000] * len(closes),
    })


def test_registry_contains_all_strategies():
    assert set(STRATEGIES) == {"ema", "rsi", "macd", "bollinger"}
    assert DEFAULT_STRATEGY in STRATEGIES


def test_get_strategy_unknown_raises():
    with pytest.raises(ValueError, match="Unknown strategy"):
        get_strategy("does-not-exist")


@pytest.mark.parametrize("name", sorted(STRATEGIES))
def test_strategy_returns_valid_signal(name):
    closes = [100 + (i % 11) * 3 for i in range(60)]
    assert process_market_data(_df(closes), strategy=name) in {"buy", "sell", "hold"}


@pytest.mark.parametrize("name", sorted(STRATEGIES))
def test_strategy_holds_on_insufficient_data(name):
    assert get_strategy(name)(_df([100, 101, 102])) == "hold"


def test_rsi_strategy_buy_and_sell(monkeypatch):
    df = _df([100.0] * 25)
    monkeypatch.setattr(rsi_strategy, "rsi", lambda s, period=14: pd.Series([50] * 23 + [29, 31]))
    assert rsi_strategy.generate_signal(df) == "buy"
    monkeypatch.setattr(rsi_strategy, "rsi", lambda s, period=14: pd.Series([50] * 23 + [71, 69]))
    assert rsi_strategy.generate_signal(df) == "sell"


def test_macd_strategy_buy_and_sell(monkeypatch):
    df = _df([100.0] * 40)
    zeros = pd.Series([0.0] * 40)
    monkeypatch.setattr(macd_strategy, "macd",
                        lambda s, **k: (pd.Series([0.0] * 38 + [-1, 1]), zeros, zeros))
    assert macd_strategy.generate_signal(df) == "buy"
    monkeypatch.setattr(macd_strategy, "macd",
                        lambda s, **k: (pd.Series([0.0] * 38 + [1, -1]), zeros, zeros))
    assert macd_strategy.generate_signal(df) == "sell"


def test_bollinger_strategy_buy(monkeypatch):
    df = _df([100.0] * 23 + [90.0, 95.0])  # prev_close=90, cur_close=95
    monkeypatch.setattr(
        bollinger_strategy, "bollinger_bands",
        lambda s, period=20, num_std=2.0: (
            pd.Series([100.0] * 25),                 # middle
            pd.Series([200.0] * 25),                 # upper (no sell)
            pd.Series([100.0] * 23 + [95.0, 94.0]),  # lower: crosses back inside -> buy
        ),
    )
    assert bollinger_strategy.generate_signal(df) == "buy"
