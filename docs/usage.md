# Usage

All commands assume the virtual environment is active (`source .venv/bin/activate`).

## Backtesting (offline, no credentials)

```bash
python scripts/run_backtest.py                       # EMA strategy, bundled sample data
python scripts/run_backtest.py --strategy rsi        # rsi | macd | bollinger | ema
python scripts/run_backtest.py --data my_candles.csv --quantity 15 --stop-loss 1000
```

Set the live/paper strategy with `STRATEGY=ema|rsi|macd|bollinger` in `.env`.

Prints total trades, win rate, net P&L, profit factor, max drawdown, and Sharpe, plus the most
recent trades.

## Training the ML model

```bash
python scripts/train_model.py                # trains on sample data, saves models/signal_model.pkl
python scripts/train_model.py --data my_candles.csv
```

Reports accuracy, precision, and recall on a time-ordered holdout (no shuffle, so no leakage).

## Comparing rule-only vs. rule + ML

```bash
python scripts/compare_strategies.py
```

Runs both backtests and prints a side-by-side metrics table — the clearest illustration of the ML
filter's effect.

## Dashboard

```bash
streamlit run app/dashboard.py
```

Opens at `http://localhost:8501`. Tabs: **Overview**, **Backtest** (interactive), **Rule vs ML**,
**Trade log**. Runs fully offline.

## Live and paper trading

```bash
python scripts/run_paper.py    # real live prices, simulated fills — no real money
python scripts/run_live.py     # real orders with real money
```

Both require a configured `.env` and an interactive Upstox login (you paste the redirect URL once).

## A note on the results

The bundled sample data is **synthetic**, generated with a mild momentum component
(`scripts/generate_sample_data.py`) so the ML model has a learnable signal (~69% accuracy). This
demonstrates the full pipeline end-to-end.

**Real markets are far closer to random at the 5-minute horizon.** Expect next-candle accuracy
around 52–55% and a much smaller (or zero) edge. To evaluate honestly, replace the sample CSV with
real historical candles and re-run `train_model.py` and `compare_strategies.py`. The point of the
project is a correct, reusable, well-tested pipeline — not a claim of profitability.
