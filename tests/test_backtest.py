"""Tests for the backtesting engine."""

from datetime import datetime, timedelta

import pandas as pd

from alphapulse.engine.backtest import BacktestResult, run_backtest
from alphapulse.risk import RiskParams


def _make_candles(closes: list[float]) -> pd.DataFrame:
    start = datetime(2025, 6, 2, 9, 15)
    return pd.DataFrame({
        "Timestamp": [start + timedelta(minutes=5 * i) for i in range(len(closes))],
        "Open": closes,
        "High": [c + 5 for c in closes],
        "Low": [c - 5 for c in closes],
        "Close": closes,
        "Volume": [1_000_000] * len(closes),
        "Open Interest": [0] * len(closes),
    })


def test_run_backtest_returns_result():
    candles = _make_candles([100 + i for i in range(40)])
    result = run_backtest(candles, RiskParams(), quantity=1)
    assert isinstance(result, BacktestResult)
    assert "net_pnl" in result.metrics
    assert "win_rate_pct" in result.metrics


def test_equity_curve_has_one_point_per_candle():
    candles = _make_candles([100 + i for i in range(40)])
    result = run_backtest(candles, RiskParams(), quantity=1)
    assert len(result.equity_curve) == len(candles)


def test_flat_market_produces_no_or_zero_trades():
    candles = _make_candles([100.0] * 40)
    result = run_backtest(candles, RiskParams(), quantity=1)
    assert result.metrics["total_trades"] == 0
    assert result.metrics["net_pnl"] == 0.0


def test_net_pnl_matches_sum_of_trades():
    candles = _make_candles([100 + (i % 7) * 3 for i in range(60)])
    result = run_backtest(candles, RiskParams(), quantity=5)
    assert round(sum(t.pnl for t in result.trades), 2) == result.metrics["net_pnl"]


def test_no_lookahead_all_entries_have_valid_prices():
    candles = _make_candles([100 + (i % 5) * 4 for i in range(50)])
    result = run_backtest(candles, RiskParams(), quantity=1)
    for t in result.trades:
        assert t.entry_time <= t.exit_time
        assert t.entry_price > 0 and t.exit_price > 0
