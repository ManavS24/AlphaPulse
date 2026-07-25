"""Load historical candle data from CSV for offline backtesting."""

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"Timestamp", "Open", "High", "Low", "Close", "Volume"}


def load_candles_csv(path: str | Path) -> pd.DataFrame:
    """Load OHLCV candles from CSV (requires Timestamp/OHLCV columns), sorted by timestamp."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Candle data file not found: {path}")

    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")

    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    return df.sort_values("Timestamp").reset_index(drop=True)
