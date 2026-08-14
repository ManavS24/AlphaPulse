# Demo guide

A 5–6 minute walkthrough for a project evaluation or interview. Everything runs offline, so it
works with the market closed and needs no live credentials.

## Before you start

```bash
source .venv/bin/activate
streamlit run app/dashboard.py
```

Everything runs locally with no credentials. If you have also deployed the dashboard
(see [deployment.md](deployment.md)), keep that URL open as a backup, and keep a screen recording
of the flow (below) in reserve.

## Presentation flow

1. **Problem (30s)** — "I built an algorithmic options trading bot that combines a rule-based
   strategy with a machine-learning filter and strict risk management, and made it fully testable
   and demonstrable offline."

2. **Architecture (45s)** — show the diagram in [architecture.md](architecture.md). Emphasise the
   one design idea: the strategy and risk logic are written once and reused by live, paper, and
   backtest — only the broker differs.

3. **Dashboard — Overview tab (30s)** — the pipeline steps and the sample price chart.

4. **Backtest tab (60s)** — set quantity/SL/TP, toggle the ML filter, click **Run backtest**. Point
   at the equity curve and the metric tiles (win rate, Sharpe, drawdown). Note there is no
   look-ahead — signals use only past candles.

5. **Strategies tab (30s)** — all four strategies on identical data and risk limits. Trend
   strategies (EMA, MACD) and mean-reversion strategies (RSI, Bollinger) behave differently on the
   same market — evidence the strategy layer is genuinely pluggable, not hardcoded.

6. **Rule vs ML tab (60s)** — the money slide. The ML filter takes fewer, higher-conviction trades
   and improves win rate, profit factor, and Sharpe. Explain: *the model predicts next-candle
   direction and vetoes low-confidence signals.*

7. **Trade log tab (20s)** — every trade persisted to SQLite, with exit reasons (TAKE_PROFIT,
   STOP_LOSS, DAY_CLOSE, MAX_TRADES_PER_DAY) that show the risk rules firing.

8. **Honesty + future work (30s)** — the sample data is synthetic with built-in momentum; real
   markets are near-random intraday, so the edge would shrink. Future work: real historical data,
   more strategies, richer features.

## Recording screenshots / GIFs

- Capture a 60–90s screen recording of steps 4–5 (QuickTime on macOS: File → New Screen Recording).
- Convert to GIF for the README hero (e.g. `ffmpeg -i demo.mov -vf "fps=10,scale=900:-1" demo.gif`).
- Grab still screenshots of: the equity curve, the Rule-vs-ML table, and the trade log.

## Fallback if anything fails

The demo has no external dependencies at runtime, so an API outage or closed market changes nothing.
If the local app misbehaves, switch to your deployed Streamlit URL if you have one; failing that,
play the recording. `python scripts/compare_strategies.py` reproduces the headline result in the
terminal in about two seconds and makes a reliable last resort.
