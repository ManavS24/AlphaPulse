"""Backtest a strategy over historical candles and print results (offline, no credentials).

    python scripts/run_backtest.py [--strategy ema|rsi|macd|bollinger --data candles.csv]
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table

from alphapulse.data.loader import load_candles_csv
from alphapulse.engine.backtest import run_backtest
from alphapulse.risk import RiskParams
from alphapulse.strategy import STRATEGIES

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "sample" / "banknifty_5m.csv"
console = Console()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backtest a trading strategy.")
    p.add_argument("--data", type=Path, default=DEFAULT_DATA, help="Path to OHLCV candle CSV.")
    p.add_argument("--strategy", choices=sorted(STRATEGIES), default="ema", help="Strategy to run.")
    p.add_argument("--quantity", type=int, default=15, help="Position size (lot).")
    p.add_argument("--capital", type=float, default=100_000.0, help="Initial capital.")
    p.add_argument("--stop-loss", type=float, default=1_000.0)
    p.add_argument("--take-profit", type=float, default=2_000.0)
    p.add_argument("--max-daily-loss", type=float, default=3_000.0)
    p.add_argument("--max-trades-per-day", type=int, default=5)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    candles = load_candles_csv(args.data)
    limits = RiskParams(
        stop_loss=args.stop_loss,
        take_profit=args.take_profit,
        max_daily_loss=args.max_daily_loss,
        max_trades_per_day=args.max_trades_per_day,
    )

    result = run_backtest(
        candles, limits, quantity=args.quantity, initial_capital=args.capital, strategy=args.strategy
    )

    console.rule(f"[bold]Backtest: {args.strategy}  ({args.data.name}, {len(candles)} candles)")

    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column(style="cyan")
    table.add_column(justify="right", style="bold")
    m = result.metrics
    table.add_row("Total trades", str(m["total_trades"]))
    table.add_row("Win rate", f"{m['win_rate_pct']}%")
    table.add_row("Net P&L", f"{m['net_pnl']:,.2f}")
    table.add_row("Total return", f"{m['total_return_pct']}%")
    table.add_row("Profit factor", str(m["profit_factor"]))
    table.add_row("Max drawdown", f"{m['max_drawdown_pct']}%")
    table.add_row("Sharpe", str(m["sharpe"]))
    table.add_row("Avg win / loss", f"{m['avg_win']:,.2f} / {m['avg_loss']:,.2f}")
    console.print(table)

    console.rule("[dim]Recent trades")
    for t in result.trades[-8:]:
        colour = "green" if t.pnl > 0 else "red"
        console.print(
            f"  {t.entry_time:%m-%d %H:%M} {t.direction:>5} "
            f"@ {t.entry_price:>9,.2f} -> {t.exit_price:>9,.2f}  "
            f"[{colour}]{t.pnl:>+10,.2f}[/{colour}]  ({t.exit_reason})"
        )


if __name__ == "__main__":
    main()
