# Demo guide

A 4–5 minute walkthrough for a project evaluation or interview. Everything runs offline, so it
works with the market closed and needs no live credentials.

## Before you start

```bash
source .venv/bin/activate
streamlit run app/dashboard.py
```

Have the public Streamlit URL open as a backup in case of local issues, and keep a screen recording
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

5. **Rule vs ML tab (60s)** — the money slide. The ML filter takes fewer, higher-conviction trades
   and improves win rate, profit factor, and Sharpe. Explain: *the model predicts next-candle
   direction and vetoes low-confidence signals.*

6. **Trade log tab (20s)** — every trade persisted to SQLite, with exit reasons (TAKE_PROFIT,
   STOP_LOSS, DAY_CLOSE, MAX_TRADES_PER_DAY) that show the risk rules firing.

7. **Honesty + future work (30s)** — the sample data is synthetic with built-in momentum; real
   markets are near-random intraday, so the edge would shrink. Future work: real historical data,
   more strategies, richer features.

## Recording screenshots / GIFs

- Capture a 60–90s screen recording of steps 4–5 (QuickTime on macOS: File → New Screen Recording).
- Convert to GIF for the README hero (e.g. `ffmpeg -i demo.mov -vf "fps=10,scale=900:-1" demo.gif`).
- Grab still screenshots of: the equity curve, the Rule-vs-ML table, and the trade log.

## Fallback if anything fails

The demo has no external dependencies at runtime, so an API outage or closed market changes nothing.
If the local app misbehaves, switch to the deployed Streamlit URL; if that fails, play the recording.
