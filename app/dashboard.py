"""Streamlit dashboard: runs entirely offline on the bundled sample data and trained model.

    streamlit run app/dashboard.py
"""

import sys
from pathlib import Path

# Make the package importable whether or not it is pip-installed (e.g. on Streamlit Cloud).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st

from alphapulse.data.loader import load_candles_csv
from alphapulse.engine.backtest import run_backtest
from alphapulse.risk import RiskParams
from alphapulse.storage import load_trades, save_trades
from alphapulse.strategy import STRATEGIES
from alphapulse.strategy.ml_filter import MLSignalFilter

DATA_PATH = ROOT / "data" / "sample" / "banknifty_5m.csv"

# Defaults shared by the Strategies and Rule-vs-ML tabs so every tab compares like with like.
BASELINE_QUANTITY = 15
BASELINE_STOP_LOSS = 1_000.0
BASELINE_TAKE_PROFIT = 2_000.0
BASELINE = (BASELINE_QUANTITY, BASELINE_STOP_LOSS, BASELINE_TAKE_PROFIT)

STRATEGY_LABELS = {
    "ema": "EMA crossover (trend)",
    "rsi": "RSI (mean reversion)",
    "macd": "MACD (trend)",
    "bollinger": "Bollinger Bands (mean reversion)",
}

st.set_page_config(page_title="AlphaPulse", page_icon="📈", layout="wide")


@st.cache_data(show_spinner=False)
def _load_candles() -> pd.DataFrame:
    return load_candles_csv(DATA_PATH)


@st.cache_resource
def _load_filter() -> MLSignalFilter:
    return MLSignalFilter.load()


@st.cache_data(show_spinner=False)
def _run(strategy: str, quantity: int, stop_loss: float, take_profit: float, use_ml: bool):
    """Cached backtest. Keyed on the parameters, so repeat views are instant."""
    limits = RiskParams(stop_loss=stop_loss, take_profit=take_profit)
    ml_filter = _load_filter() if use_ml else None
    return run_backtest(
        _load_candles(), limits, quantity=quantity, ml_filter=ml_filter, strategy=strategy
    )


def _settings_caption(strategy: str, quantity: int, stop_loss: float,
                      take_profit: float, use_ml: bool) -> str:
    """Human-readable description of the run that produced a set of results."""
    return (
        f"{STRATEGY_LABELS.get(strategy, strategy)} · qty {quantity} · "
        f"SL ₹{stop_loss:,.0f} · TP ₹{take_profit:,.0f} · "
        f"ML filter {'on' if use_ml else 'off'}"
    )


def _metric_row(metrics: dict) -> None:
    c = st.columns(4)
    c[0].metric("Net P&L", f"₹{metrics['net_pnl']:,.0f}")
    c[1].metric("Win rate", f"{metrics['win_rate_pct']}%")
    c[2].metric("Total trades", metrics["total_trades"])
    c[3].metric("Sharpe", metrics["sharpe"])
    c = st.columns(4)
    c[0].metric("Total return", f"{metrics['total_return_pct']}%")
    c[1].metric("Profit factor", metrics["profit_factor"])
    c[2].metric("Max drawdown", f"{metrics['max_drawdown_pct']}%")
    c[3].metric("Avg win / loss", f"{metrics['avg_win']:,.0f} / {metrics['avg_loss']:,.0f}")


st.title("📈 AlphaPulse")
st.caption(
    "Multi-strategy options trading bot (EMA, RSI, MACD, Bollinger) with ML signal filtering, "
    "risk management, and offline backtesting. Educational project — not financial advice."
)

candles = _load_candles()
ml_ready = _load_filter().enabled

# The ML filter is the project's headline feature; if the model is missing, say so plainly
# rather than silently passing every signal through and reporting "no effect".
if not ml_ready:
    st.warning(
        "**ML model not found** — the signal filter is inactive, so the ML results below are "
        "identical to the rule-only results. Run `python scripts/train_model.py` to create "
        "`models/signal_model.pkl`.",
        icon="⚠️",
    )

overview_tab, backtest_tab, strategies_tab, compare_tab, log_tab = st.tabs(
    ["Overview", "Backtest", "Strategies", "Rule vs ML", "Trade log"]
)

with overview_tab:
    st.subheader("How it works")
    st.markdown(
        """
        1. **Market data** — historical / live OHLCV candles.
        2. **Strategy** — choose EMA crossover, RSI, MACD, or Bollinger Bands; each proposes
           `buy` / `sell` / `hold`.
        3. **ML filter** — a logistic-regression model predicts the next candle's direction and
           vetoes low-confidence signals.
        4. **Risk management** — stop-loss, take-profit, max trades/day and max daily loss, with
           intraday square-off.
        5. **Execution** — live (Upstox, real money) or paper (simulated) via one broker interface.
        """
    )
    st.subheader("Sample underlying price")
    st.line_chart(candles.set_index("Timestamp")["Close"], height=280)
    st.caption(f"{len(candles)} candles · {DATA_PATH.name} (synthetic sample data)")

    st.info(
        "**About this demo.** The bundled candles are *synthetic*, generated with a mild momentum "
        "component so the model has a learnable signal. Real intraday markets are far closer to "
        "random, so the edge shown here would shrink substantially on live data. This dashboard "
        "runs fully offline and places no orders.",
        icon="ℹ️",
    )

with backtest_tab:
    st.subheader("Backtest")
    strategy = st.selectbox(
        "Strategy",
        sorted(STRATEGIES),
        index=sorted(STRATEGIES).index("ema"),
        format_func=lambda name: STRATEGY_LABELS.get(name, name),
    )
    col1, col2, col3 = st.columns(3)
    quantity = col1.number_input("Quantity", 1, 500, BASELINE_QUANTITY)
    stop_loss = col2.number_input("Stop loss (₹)", 100, 100_000, int(BASELINE_STOP_LOSS), step=100)
    take_profit = col3.number_input(
        "Take profit (₹)", 100, 100_000, int(BASELINE_TAKE_PROFIT), step=100
    )
    use_ml = st.toggle("Apply ML signal filter", value=True, disabled=not ml_ready)

    current_params = (strategy, quantity, float(stop_loss), float(take_profit), use_ml)

    if st.button("Run backtest", type="primary"):
        with st.spinner("Running backtest…"):
            st.session_state["last_result"] = _run(*current_params)
            st.session_state["last_params"] = current_params
            st.session_state["saved_params"] = None

    result = st.session_state.get("last_result")
    shown_params = st.session_state.get("last_params")

    if result is not None and shown_params is not None:
        # Results are pinned to the settings that produced them, so changing a control without
        # re-running can never make old numbers look like they belong to the new settings.
        if shown_params != current_params:
            st.warning(
                "Settings changed since this backtest ran. The results below are still for "
                f"**{_settings_caption(*shown_params)}** — click **Run backtest** to update.",
                icon="⚠️",
            )
        st.caption(f"Results for {_settings_caption(*shown_params)}")
        _metric_row(result.metrics)
        st.markdown("**Equity curve**")
        st.line_chart(result.equity_curve.set_index("Timestamp")["Equity"], height=320)

        already_saved = st.session_state.get("saved_params") == shown_params
        if st.button(
            "💾 Save these trades to the log",
            disabled=already_saved or not result.trades,
            help="Already saved" if already_saved else None,
        ):
            n = save_trades(result.trades, source="backtest")
            st.session_state["saved_params"] = shown_params
            st.toast(f"Saved {n} trades to the log.", icon="💾")
            st.rerun()
        if already_saved:
            st.caption("These trades are already in the log.")
    else:
        st.info("Set parameters and click **Run backtest**.")

with strategies_tab:
    st.subheader("Strategy comparison")
    st.caption(
        f"All four strategies on the same data and risk limits — qty {BASELINE_QUANTITY}, "
        f"SL ₹{BASELINE_STOP_LOSS:,.0f}, TP ₹{BASELINE_TAKE_PROFIT:,.0f}, rule-only (no ML filter)."
    )
    rows = []
    for name in sorted(STRATEGIES):
        m = _run(name, BASELINE_QUANTITY, BASELINE_STOP_LOSS, BASELINE_TAKE_PROFIT, False).metrics
        rows.append({
            "Strategy": STRATEGY_LABELS.get(name, name), "Trades": m["total_trades"],
            "Win %": m["win_rate_pct"], "Net P&L": m["net_pnl"],
            "Return %": m["total_return_pct"], "Profit factor": m["profit_factor"],
            "Max DD %": m["max_drawdown_pct"], "Sharpe": m["sharpe"],
        })
    st.dataframe(pd.DataFrame(rows).set_index("Strategy"), width="stretch")
    st.caption("Trend strategies (EMA, MACD) and mean-reversion strategies (RSI, Bollinger) "
               "behave differently on the same market.")

with compare_tab:
    st.subheader("Rule-only vs. Rule + ML filter")
    st.caption(
        "Same data, same risk limits — the ML filter only changes which signals fire. "
        f"EMA crossover, qty {BASELINE_QUANTITY}, SL ₹{BASELINE_STOP_LOSS:,.0f}, "
        f"TP ₹{BASELINE_TAKE_PROFIT:,.0f}."
    )
    rule = _run("ema", *BASELINE, False)
    ml = _run("ema", *BASELINE, True)
    keys = [
        ("Total trades", "total_trades"), ("Win rate %", "win_rate_pct"),
        ("Net P&L", "net_pnl"), ("Total return %", "total_return_pct"),
        ("Profit factor", "profit_factor"), ("Max drawdown %", "max_drawdown_pct"),
        ("Sharpe", "sharpe"),
    ]
    comparison = pd.DataFrame(
        {"Rule-only": [rule.metrics[k] for _, k in keys],
         "Rule + ML": [ml.metrics[k] for _, k in keys]},
        index=[label for label, _ in keys],
    )
    st.dataframe(comparison, width="stretch")
    delta = ml.metrics["net_pnl"] - rule.metrics["net_pnl"]
    st.metric("ML filter net P&L impact", f"₹{delta:,.0f}", delta=f"{delta:,.0f}")
    if ml_ready:
        st.caption(
            f"The filter took {rule.metrics['total_trades'] - ml.metrics['total_trades']} fewer "
            "trades by vetoing low-confidence signals."
        )

with log_tab:
    st.subheader("Trade log (SQLite)")
    trades = load_trades()
    seeded = False
    if trades.empty:
        # Auto-seed on a fresh deploy so the log is never empty.
        seed = _run("ema", *BASELINE, ml_ready)
        save_trades(seed.trades, source="auto-seed")
        trades = load_trades()
        seeded = True
    if trades.empty:
        st.info("No trades yet. Run a backtest and save it to populate the log.")
    else:
        if seeded:
            st.caption(
                "Populated automatically from a baseline EMA backtest on first load — these rows "
                "are tagged `auto-seed`. Trades you save from the **Backtest** tab appear as "
                "`backtest`."
            )
        st.caption(f"{len(trades)} trades · net P&L ₹{trades['pnl'].sum():,.0f}")
        st.dataframe(
            trades[["source", "entry_time", "direction", "entry_price",
                    "exit_price", "quantity", "pnl", "exit_reason"]],
            width="stretch", height=460,
        )
        st.caption(
            "Written by the same code path the live and paper runners use. `exit_reason` shows "
            "which rule closed each position — TAKE_PROFIT, STOP_LOSS, SIGNAL_REVERSE, "
            "DAY_CLOSE, or a daily risk cap."
        )
