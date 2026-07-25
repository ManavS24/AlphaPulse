# 📈 AlphaPulse

A multi-strategy algorithmic options trading bot for the [Upstox](https://upstox.com/) platform — EMA, RSI, MACD, and Bollinger Band strategies with **machine-learning signal filtering**, **risk management**, an **offline backtesting engine**, and an interactive **Streamlit dashboard**.

> ⚠️ **Educational project — not financial advice.** Live trading places real orders with real money. Use paper mode and backtesting to explore the system safely.

---

## Highlights

- **Four selectable strategies** — EMA crossover, RSI, MACD, and Bollinger Bands — optionally gated by a scikit-learn classifier that predicts next-candle direction and vetoes low-confidence trades.
- **Offline backtester** — evaluate the exact same strategy and risk rules on historical candles with no broker connection. Reports win rate, return, profit factor, max drawdown, and Sharpe.
- **One interface, three modes** — the same trading loop runs **live** (Upstox), **paper** (simulated fills, real prices), or **backtest** (fully offline).
- **Risk management** — stop-loss, take-profit, max trades/day, max daily loss, with intraday square-off.
- **Dashboard** — Streamlit app with an interactive backtest, equity curve, rule-vs-ML comparison, and a SQLite trade log.

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

> These figures use **synthetic sample data** with built-in momentum so the model has a learnable signal (69% accuracy vs. 44.6% baseline). On real market data, expect a smaller edge — see [docs/usage.md](docs/usage.md).

---

## Quickstart

```bash
git clone <your-repo-url> && cd alphapulse
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 1. Generate sample data and train the model (already committed, but reproducible)
python scripts/generate_sample_data.py
python scripts/train_model.py

# 2. Backtest offline (no credentials needed)
python scripts/run_backtest.py
python scripts/compare_strategies.py

# 3. Launch the dashboard
streamlit run app/dashboard.py
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
├── broker/            # Broker interface + Upstox (live) and Paper brokers
├── data/              # market data + CSV loader
├── strategy/          # EMA/RSI/MACD/Bollinger strategies, indicators, features, ML filter
├── risk/              # risk management rules
├── engine/            # backtest engine + live/paper runner
└── storage/           # SQLite trade log
app/dashboard.py       # Streamlit dashboard
scripts/               # backtest, train, compare, seed, run entry points
tests/                 # pytest suite
data/sample/           # committed sample candles
models/                # committed trained model
docs/                  # architecture, installation, usage, deployment, demo
```

## Documentation

- [Architecture](docs/architecture.md) · [Installation](docs/installation.md) · [Usage](docs/usage.md) · [Deployment](docs/deployment.md) · [Demo guide](docs/demo.md)

## Tech stack

Python · pandas · scikit-learn · Streamlit · SQLite · Upstox SDK · pytest · ruff

## License

[MIT](LICENSE)
