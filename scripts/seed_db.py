"""Seed the SQLite trade log from a backtest so the dashboard has data.

    python scripts/seed_db.py
"""

from pathlib import Path

from alphapulse.data.loader import load_candles_csv
from alphapulse.engine.backtest import run_backtest
from alphapulse.risk import RiskParams
from alphapulse.storage import clear_trades, save_trades
from alphapulse.strategy.ml_filter import MLSignalFilter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sample" / "banknifty_5m.csv"


def main() -> None:
    candles = load_candles_csv(DATA)
    result = run_backtest(candles, RiskParams(), quantity=15, ml_filter=MLSignalFilter.load())
    clear_trades()
    n = save_trades(result.trades, source="backtest")
    print(f"Seeded {n} trades into the trade log.")


if __name__ == "__main__":
    main()
