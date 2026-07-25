"""Technical features for the ML filter; all use only data up to the current candle (no look-ahead)."""

import pandas as pd

FEATURE_COLUMNS = [
    "ema_gap",
    "close_vs_ema9",
    "rsi_14",
    "return_1",
    "return_3",
    "volume_ratio",
    "hl_range",
]


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - 100 / (1 + rs)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ema_9 = df["Close"].ewm(span=9, adjust=False).mean()
    ema_15 = df["Close"].ewm(span=15, adjust=False).mean()

    df["ema_gap"] = (ema_9 - ema_15) / df["Close"]
    df["close_vs_ema9"] = (df["Close"] - ema_9) / df["Close"]
    df["rsi_14"] = _rsi(df["Close"], 14)
    df["return_1"] = df["Close"].pct_change(1)
    df["return_3"] = df["Close"].pct_change(3)
    df["volume_ratio"] = df["Volume"] / df["Volume"].rolling(10).mean()
    df["hl_range"] = (df["High"] - df["Low"]) / df["Close"]
    return df


def build_training_set(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) where y=1 if the next close is higher; drops NaN rows and the last row."""
    featured = add_features(df)
    featured["target"] = (featured["Close"].shift(-1) > featured["Close"]).astype(int)
    featured = featured.iloc[:-1]
    featured = featured.dropna(subset=[*FEATURE_COLUMNS, "target"])
    return featured[FEATURE_COLUMNS], featured["target"]


def latest_feature_row(df: pd.DataFrame) -> pd.DataFrame | None:
    """Return a single-row feature frame for the most recent candle, or None if not ready."""
    featured = add_features(df)
    row = featured[FEATURE_COLUMNS].iloc[[-1]]
    if row.isna().any(axis=None):
        return None
    return row
