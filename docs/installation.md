# Installation

## Requirements

- Python 3.11+
- (Optional, for live/paper trading) an [Upstox](https://upstox.com/developer/apps) developer app
  with API key, secret, and redirect URI.

## Steps

```bash
# 1. Clone
git clone <your-repo-url>
cd alphapulse

# 2. Virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install (with dev tools: pytest, ruff)
pip install -e ".[dev]"
```

## Verify

```bash
pytest -q            # all tests should pass
ruff check src/      # lint should be clean
python scripts/run_backtest.py   # runs offline, prints metrics
```

If the backtest prints a metrics table, the installation works — no credentials required.

## Configuration (only for live/paper trading)

```bash
cp .env.example .env
```

Fill in the values in `.env`:

| Variable | Meaning |
|---|---|
| `UPSTOX_API_KEY` / `UPSTOX_API_SECRET` / `UPSTOX_REDIRECT_URI` | Upstox app credentials. |
| `INSTRUMENT_KEY` | Underlying to trade, e.g. `NSE_INDEX\|Nifty Bank`. |
| `UNIT` / `INTERVAL` | Candle unit and interval, e.g. `minutes` / `5`. |
| `QUANTITY` | Position size (lot). |
| `STOP_LOSS` / `TAKE_PROFIT` | Per-position P&L limits (₹). |
| `MAX_TRADES_PER_DAY` / `MAX_DAILY_LOSS` | Daily risk caps. |
| `TRADE_CHECK_INTERVAL` / `MAX_RUNTIME` | Loop interval and session length (seconds). |

`.env` is gitignored — never commit real credentials.
