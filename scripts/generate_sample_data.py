"""Generate a synthetic Bank Nifty-like 5-minute candle dataset for offline demos.

    python scripts/generate_sample_data.py

Writes data/sample/banknifty_5m.csv. Data is synthetic; replace with real candles for real results.
"""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "sample" / "banknifty_5m.csv"

CANDLES_PER_DAY = 75  # ~6.25h of 5-minute candles
N_DAYS = 20
START_PRICE = 48_000.0
SEED = 42
MOMENTUM = 0.25  # AR(1) coefficient: markets show mild short-term momentum


def generate() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    price = START_PRICE
    prev_move = 0.0
    start_day = datetime(2025, 6, 2, 9, 15)

    for day in range(N_DAYS):
        day_start = start_day + timedelta(days=day)
        # Per-day drift/volatility regime.
        drift = rng.normal(0, 6)
        vol = rng.uniform(8, 22)

        for c in range(CANDLES_PER_DAY):
            ts = day_start + timedelta(minutes=5 * c)
            open_price = price
            # AR(1): carry forward part of the previous move (learnable momentum) plus noise.
            move = drift + MOMENTUM * prev_move + rng.normal(0, vol)
            prev_move = move
            close_price = max(open_price + move, 1.0)
            high = max(open_price, close_price) + abs(rng.normal(0, vol / 2))
            low = min(open_price, close_price) - abs(rng.normal(0, vol / 2))
            volume = int(abs(rng.normal(1_000_000, 300_000)) + abs(move) * 5_000)
            rows.append({
                "Timestamp": ts,
                "Open": round(open_price, 2),
                "High": round(high, 2),
                "Low": round(low, 2),
                "Close": round(close_price, 2),
                "Volume": volume,
                "Open Interest": 0,
            })
            price = close_price

    return pd.DataFrame(rows)


def main() -> None:
    df = generate()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} candles to {OUT_PATH}")


if __name__ == "__main__":
    main()
