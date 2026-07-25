"""Offline backtesting engine: runs the live strategy and risk rules over historical candles.

The strategy's directional view is expressed on the underlying (buy=long, sell=short); live
trading expresses the same view via ATM options. Signals use only candles up to the current bar
(no look-ahead). Per-day risk limits reset each day and open positions are squared off at day end.
"""

import math
from dataclasses import dataclass, field

import pandas as pd

from alphapulse.risk import RiskLimits, check_risk
from alphapulse.strategy import DEFAULT_STRATEGY, process_market_data
from alphapulse.strategy.ema_crossover import MIN_CANDLES

DEFAULT_INITIAL_CAPITAL = 100_000.0


@dataclass
class Trade:
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp
    exit_price: float
    direction: str  # "long" or "short"
    quantity: int
    pnl: float
    exit_reason: str  # SIGNAL_REVERSE | STOP_LOSS | TAKE_PROFIT | DAY_CLOSE | MAX_DAILY_LOSS ...


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)  # columns: Timestamp, Equity
    initial_capital: float = DEFAULT_INITIAL_CAPITAL
    metrics: dict = field(default_factory=dict)


def _compute_metrics(
    trades: list[Trade], equity: pd.Series, initial_capital: float
) -> dict:
    n = len(trades)
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    net_pnl = sum(t.pnl for t in trades)

    running_peak = equity.cummax()
    drawdown = (running_peak - equity) / running_peak
    max_drawdown_pct = float(drawdown.max() * 100) if not equity.empty else 0.0

    # Trade-based Sharpe: mean / std of per-trade returns, scaled by sqrt(#trades).
    if n > 1:
        returns = pd.Series([t.pnl / initial_capital for t in trades])
        std = returns.std()
        sharpe = float(returns.mean() / std * math.sqrt(n)) if std > 0 else 0.0
    else:
        sharpe = 0.0

    return {
        "total_trades": n,
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate_pct": round(len(wins) / n * 100, 2) if n else 0.0,
        "net_pnl": round(net_pnl, 2),
        "total_return_pct": round(net_pnl / initial_capital * 100, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else float("inf"),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "sharpe": round(sharpe, 2),
        "avg_win": round(gross_profit / len(wins), 2) if wins else 0.0,
        "avg_loss": round(-gross_loss / len(losses), 2) if losses else 0.0,
    }


def run_backtest(
    candles: pd.DataFrame,
    limits: RiskLimits,
    quantity: int = 1,
    initial_capital: float = DEFAULT_INITIAL_CAPITAL,
    ml_filter=None,
    strategy: str = DEFAULT_STRATEGY,
) -> BacktestResult:
    """Backtest a strategy over candles; if ml_filter is given, signals must pass it to fire."""
    candles = candles.reset_index(drop=True)
    trades: list[Trade] = []
    equity_points: list[tuple] = []

    realized_pnl = 0.0  # cumulative across the run
    day_pnl = 0.0
    day_trades: list[dict] = []
    current_day = None
    trading_enabled = True
    last_signal: str | None = None

    direction = 0  # +1 long, -1 short, 0 flat
    entry_price = 0.0
    entry_time = None

    def close_position(exit_price, exit_time, reason):
        nonlocal direction, entry_price, entry_time, realized_pnl, day_pnl
        pnl = direction * (exit_price - entry_price) * quantity
        trades.append(Trade(
            entry_time=entry_time, entry_price=entry_price,
            exit_time=exit_time, exit_price=exit_price,
            direction="long" if direction > 0 else "short",
            quantity=quantity, pnl=pnl, exit_reason=reason,
        ))
        realized_pnl += pnl
        day_pnl += pnl
        day_trades.append({"pnl": pnl})
        direction = 0
        entry_price = 0.0
        entry_time = None

    for i in range(len(candles)):
        row = candles.iloc[i]
        price = row["Close"]
        ts = row["Timestamp"]
        day = ts.date() if hasattr(ts, "date") else ts

        # New trading day: square off and reset per-day risk state.
        if current_day is not None and day != current_day:
            if direction != 0:
                close_position(candles.iloc[i - 1]["Close"], candles.iloc[i - 1]["Timestamp"], "DAY_CLOSE")
            day_pnl = 0.0
            day_trades = []
            trading_enabled = True
            last_signal = None
        current_day = day

        if i < MIN_CANDLES:
            equity_points.append((ts, initial_capital + realized_pnl))
            continue

        window = candles.iloc[: i + 1].copy()
        signal = process_market_data(window, ml_filter=ml_filter, strategy=strategy)

        if direction != 0:
            unrealized = direction * (price - entry_price) * quantity
            decision = check_risk(limits, day_trades, day_pnl, unrealized)
            if not decision.continue_trading:
                if decision.reason in ("STOP_LOSS", "TAKE_PROFIT"):
                    close_position(price, ts, decision.reason)
                elif decision.reason in ("MAX_DAILY_LOSS", "MAX_TRADES_PER_DAY"):
                    close_position(price, ts, decision.reason)
                    trading_enabled = False
        elif not trading_enabled:
            # Flat and halted: re-check whether the day can resume.
            decision = check_risk(limits, day_trades, day_pnl, 0.0)
            trading_enabled = decision.continue_trading

        # Enter/reverse only on a fresh signal (mirrors the live runner).
        if trading_enabled and signal in ("buy", "sell") and signal != last_signal:
            new_dir = 1 if signal == "buy" else -1
            if direction != 0 and direction != new_dir:
                close_position(price, ts, "SIGNAL_REVERSE")
            if direction == 0:
                direction = new_dir
                entry_price = price
                entry_time = ts
        last_signal = signal

        unrealized = direction * (price - entry_price) * quantity if direction != 0 else 0.0
        equity_points.append((ts, initial_capital + realized_pnl + unrealized))

    if direction != 0:
        last = candles.iloc[-1]
        close_position(last["Close"], last["Timestamp"], "END_OF_DATA")

    equity_df = pd.DataFrame(equity_points, columns=["Timestamp", "Equity"])
    metrics = _compute_metrics(trades, equity_df["Equity"], initial_capital)

    return BacktestResult(
        trades=trades,
        equity_curve=equity_df,
        initial_capital=initial_capital,
        metrics=metrics,
    )
