# 📈 AlphaPulse

A multi-strategy algorithmic options trading bot for the [Upstox](https://upstox.com/) platform — EMA, RSI, MACD, and Bollinger Band strategies with **machine-learning signal filtering**, **risk management**, an **offline backtesting engine**, and an interactive **Streamlit dashboard**.

> ⚠️ **Educational project — not financial advice.** Live trading places real orders with real money. Use paper mode and backtesting to explore the system safely.

> **Live demo:** a hosted instance runs on Streamlit Community Cloud with access restricted — available on request. The dashboard is fully self-contained and needs no credentials, so the fastest way to try it is the [Quickstart](#quickstart) below (about 30 seconds), or deploy your own via [docs/deployment.md](docs/deployment.md).

---

## Highlights

- **Four selectable strategies** — EMA crossover, RSI, MACD, and Bollinger Bands — optionally gated by a scikit-learn classifier that predicts next-candle direction and vetoes low-confidence trades.
- **Offline backtester** — evaluate the exact same strategy and risk rules on historical candles with no broker connection. Reports win rate, return, profit factor, max drawdown, and Sharpe.
- **One interface, three modes** — the same trading loop runs **live** (Upstox), **paper** (simulated fills, real prices), or **backtest** (fully offline).
- **Risk management** — stop-loss, take-profit, max trades/day, max daily loss, with intraday square-off.
- **Dashboard** — Streamlit app with an interactive backtest, equity curve, a four-strategy comparison, a rule-vs-ML breakdown, and a SQLite trade log.

## Results (bundled sample data)

The ML filter takes fewer, higher-conviction trades — improving every metric:

| Metric | Rule-only | Rule + ML |
|---|---:|---:|
| Total trades | 82 | 78 |
| Win rate | 67.1% | **70.5%** |
| Net P&L | 76,513 | **80,458** |
| Profit factor | 4.92 | **5.81** |
| Max drawdown | 3.20% | **2.93%** |
| Sharpe | 6.29 | **6.88** |

Reproduce with `python scripts/compare_strategies.py`.

> These figures use **synthetic sample data** with built-in momentum so the model has a learnable signal (69.4% accuracy vs. a 44.6% always-up baseline). On real market data, expect a smaller edge — see [docs/usage.md](docs/usage.md).

---

## Quickstart

```bash
git clone https://github.com/ManavS24/AlphaPulse.git && cd AlphaPulse
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 1. Backtest offline — no credentials, no network
python scripts/run_backtest.py
python scripts/compare_strategies.py

# 2. Launch the dashboard
streamlit run app/dashboard.py
```

The sample candles and the trained model are committed, so all of the above works on a fresh
clone. To regenerate them from scratch:

```bash
python scripts/generate_sample_data.py   # rewrites data/sample/banknifty_5m.csv
python scripts/train_model.py            # rewrites models/signal_model.pkl
```

For live/paper trading, copy `.env.example` to `.env` and fill in your Upstox API credentials:

```bash
cp .env.example .env
python scripts/run_paper.py   # simulated fills, no real money
python scripts/run_live.py    # real orders — use with care
```

## Project layout

```
src/alphapulse/       # the package
├── config.py          # typed settings (pydantic-settings)
├── paths.py           # project-root / data / model path resolution
├── broker/            # Broker interface + Upstox (live) and Paper brokers
├── data/              # market data + CSV loader
├── strategy/          # EMA/RSI/MACD/Bollinger strategies, indicators, features, ML filter
├── risk/              # risk management rules
├── engine/            # backtest engine + live/paper runner
└── storage/           # SQLite trade log
app/dashboard.py       # Streamlit dashboard
scripts/               # backtest, train, compare, seed, run entry points
tests/                 # pytest suite (54 tests)
data/sample/           # committed sample candles
models/                # committed trained model
docs/                  # architecture, installation, usage, deployment, demo
```

## Documentation

- [Architecture](docs/architecture.md) · [Installation](docs/installation.md) · [Usage](docs/usage.md) · [Deployment](docs/deployment.md) · [Demo guide](docs/demo.md)

## Tech stack

Python · pandas · scikit-learn · Streamlit · SQLite · Upstox SDK · pytest · ruff

## Known limitations

- **The bundled data is synthetic.** It is generated with a mild momentum component so the ML
  model has something learnable. Real intraday markets are far closer to random — the edge shown
  here would shrink substantially on live data.
- **Live trading is the least-exercised path.** It requires an interactive Upstox OAuth login and
  a funded account, so it cannot be covered by the automated tests; the loop is tested against a
  fake broker instead. The ATM option instrument key is constructed from a strike/expiry
  convention that should be checked against the current Upstox contract master before real use.
- **The trade log is ephemeral on Streamlit Cloud** — it resets on redeploy.

## License

[MIT](LICENSE)
