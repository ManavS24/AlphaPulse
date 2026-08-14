"""Tests for the EMA strategy and risk manager."""

import pandas as pd

from alphapulse.risk.risk_manager import RiskDecision, check_risk
from alphapulse.strategy import process_market_data
from alphapulse.strategy.ema_crossover import calculate_ema, generate_signal


class _FakeSettings:
    """Minimal stand-in for Settings so risk tests don't need a real .env."""

    stop_loss = 1000.0
    take_profit = 2000.0
    max_daily_loss = 3000.0
    max_trades_per_day = 5


def _make_df(closes: list[float], volumes: list[float] | None = None) -> pd.DataFrame:
    volumes = volumes or [100] * len(closes)
    return pd.DataFrame({
        "Close": closes,
        "Volume": volumes,
        "Open": closes,
        "High": closes,
        "Low": closes,
    })


def test_calculate_ema_length_matches_input():
    ema = calculate_ema(pd.Series([1, 2, 3, 4, 5]), 3)
    assert len(ema) == 5


def test_insufficient_data_returns_hold():
    assert generate_signal(_make_df([100, 101, 102])) == "hold"


def test_empty_data_returns_hold():
    assert process_market_data(pd.DataFrame()) == "hold"


def test_signal_is_valid_value():
    closes = [100 + i for i in range(30)]
    signal = generate_signal(_make_df(closes))
    assert signal in {"buy", "sell", "hold"}


def test_risk_stops_on_max_daily_loss():
    decision = check_risk(_FakeSettings(), trade_history=[], current_pnl=-3000)
    assert isinstance(decision, RiskDecision)
    assert decision.continue_trading is False
    assert decision.reason == "MAX_DAILY_LOSS"


def test_risk_continues_when_within_limits():
    decision = check_risk(_FakeSettings(), trade_history=[], current_pnl=-100, current_position_pnl=50)
    assert decision.continue_trading is True
    assert decision.reason is None


def test_risk_take_profit_triggers():
    decision = check_risk(_FakeSettings(), trade_history=[], current_pnl=0, current_position_pnl=2500)
    assert decision.reason == "TAKE_PROFIT"
