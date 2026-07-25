"""Tests for the live/paper trading loop using a fake broker (no network, no real orders).

These exercise orchestration and the None-price safety guards without an Upstox connection.
"""

from dataclasses import dataclass

import pandas as pd

from alphapulse.broker.base import Broker
from alphapulse.engine import runner


@dataclass
class FakeSettings:
    instrument_key: str = "NSE_INDEX|Test"
    unit: str = "minutes"
    interval: str = "5"
    strategy: str = "ema"
    quantity: int = 1
    trade_check_interval: float = 0.0
    max_runtime: float = 0.02
    # Risk limits set wide so risk never halts the loop during these tests.
    stop_loss: float = 1e9
    take_profit: float = 1e9
    max_daily_loss: float = 1e9
    max_trades_per_day: int = 10_000


class FakeBroker(Broker):
    def __init__(self, price: float | None = 100.0):
        self.price = price
        self.orders: list[tuple] = []

    def connect(self) -> bool:
        return True

    def get_candles(self, instrument_key, unit, interval) -> pd.DataFrame:
        return pd.DataFrame({"Close": [100, 101, 102], "Volume": [1, 1, 1]})

    def get_price(self, instrument_key):
        return self.price

    def buy(self, instrument_key, quantity) -> bool:
        self.orders.append(("buy", instrument_key, quantity))
        return True

    def sell(self, instrument_key, quantity) -> bool:
        self.orders.append(("sell", instrument_key, quantity))
        return True


class NoConnectBroker(FakeBroker):
    def connect(self) -> bool:
        return False


def test_manage_trades_runs_full_buy_and_close_cycle(monkeypatch):
    signals = iter(["buy"])  # buy once, then hold for the rest of the session
    monkeypatch.setattr(runner, "process_market_data",
                        lambda df, ml_filter=None, strategy="ema": next(signals, "hold"))

    broker = FakeBroker(price=100.0)
    summary = runner.manage_trades(broker, FakeSettings())

    assert isinstance(summary, dict)
    assert summary["total_trades"] == 1
    assert ("buy", "NSE_FO|100CE" + runner.get_current_expiry(), 1) in broker.orders
    assert any(o[0] == "sell" for o in broker.orders)  # position squared off at session end


def test_manage_trades_aborts_when_connect_fails():
    assert runner.manage_trades(NoConnectBroker(), FakeSettings()) == {}


def test_manage_trades_survives_none_underlying_price(monkeypatch):
    # H1: get_price returning None must not crash the loop.
    monkeypatch.setattr(runner, "process_market_data", lambda df, ml_filter=None, strategy="ema": "buy")
    summary = runner.manage_trades(FakeBroker(price=None), FakeSettings())
    assert isinstance(summary, dict)
    assert summary["total_trades"] == 0  # no trade opened because price was unavailable


def test_close_position_records_trade_normally():
    broker = FakeBroker(price=120.0)
    history: list[dict] = []
    pos, instrument, _, pnl = runner.close_position(broker, "OPT", 100.0, "CE", history, 0.0, 2)
    assert pos is None and instrument is None
    assert pnl == 40.0  # (120 - 100) * 2
    assert len(history) == 1 and history[0]["pnl"] == 40.0


def test_close_position_handles_none_exit_price(monkeypatch):
    # H1: no price after retries -> no crash, trade not fabricated.
    monkeypatch.setattr(runner, "EXIT_PRICE_RETRY_DELAY", 0)
    broker = FakeBroker(price=None)
    history: list[dict] = []
    result = runner.close_position(broker, "OPT", 100.0, "CE", history, 0.0, 1)
    assert result == (None, None, 0.0, 0.0)
    assert history == []
