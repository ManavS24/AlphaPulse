"""Tests for the SQLite trade log."""

from datetime import datetime

from alphapulse.engine.backtest import Trade
from alphapulse.storage import init_db, load_trades, save_trades
from alphapulse.storage.db import clear_trades


def _trade(pnl: float) -> Trade:
    now = datetime(2025, 6, 2, 10, 0)
    return Trade(
        entry_time=now, entry_price=100.0, exit_time=now, exit_price=100 + pnl,
        direction="long", quantity=1, pnl=pnl, exit_reason="TAKE_PROFIT",
    )


def test_load_trades_empty_when_no_db(tmp_path):
    assert load_trades(tmp_path / "none.db").empty


def test_save_and_load_roundtrip(tmp_path):
    db = tmp_path / "trades.db"
    n = save_trades([_trade(50), _trade(-20)], source="backtest", path=db)
    assert n == 2
    df = load_trades(db)
    assert len(df) == 2
    assert set(df["source"]) == {"backtest"}
    assert round(df["pnl"].sum(), 2) == 30.0


def test_init_db_creates_table(tmp_path):
    db = tmp_path / "trades.db"
    init_db(db)
    assert load_trades(db).empty


def test_clear_trades(tmp_path):
    db = tmp_path / "trades.db"
    save_trades([_trade(10)], source="paper", path=db)
    clear_trades(db)
    assert load_trades(db).empty
