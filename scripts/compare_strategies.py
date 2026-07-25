"""Backtest rule-only vs. rule + ML filter, side by side (needs a trained model).

    python scripts/compare_strategies.py
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from alphapulse.data.loader import load_candles_csv
from alphapulse.engine.backtest import run_backtest
from alphapulse.risk import RiskParams
from alphapulse.strategy.ml_filter import MLSignalFilter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "sample" / "banknifty_5m.csv"
console = Console()

ROWS = [
    ("Total trades", "total_trades", "{}"),
    ("Win rate", "win_rate_pct", "{}%"),
    ("Net P&L", "net_pnl", "{:,.2f}"),
    ("Total return", "total_return_pct", "{}%"),
    ("Profit factor", "profit_factor", "{}"),
    ("Max drawdown", "max_drawdown_pct", "{}%"),
    ("Sharpe", "sharpe", "{}"),
]


def main() -> None:
    candles = load_candles_csv(DEFAULT_DATA)
    limits = RiskParams()
    quantity = 15

    rule = run_backtest(candles, limits, quantity=quantity)
    ml = run_backtest(candles, limits, quantity=quantity, ml_filter=MLSignalFilter.load())

    table = Table(title="Rule-only vs. Rule + ML filter")
    table.add_column("Metric", style="cyan")
    table.add_column("Rule-only", justify="right")
    table.add_column("Rule + ML", justify="right", style="bold")

    for label, key, fmt in ROWS:
        table.add_row(label, fmt.format(rule.metrics[key]), fmt.format(ml.metrics[key]))

    console.print(table)


if __name__ == "__main__":
    main()
