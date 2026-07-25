"""RSI mean-reversion: buy on recovery from oversold, sell on drop from overbought."""

import pandas as pd

from alphapulse.strategy.indicators import rsi

MIN_CANDLES = 20
OVERSOLD = 30
OVERBOUGHT = 70


def generate_signal(df: pd.DataFrame, period: int = 14) -> str:
    if df is None or df.empty or len(df) < MIN_CANDLES:
        return "hold"
    r = rsi(df["Close"], period)
    prev, cur = r.iloc[-2], r.iloc[-1]
    if pd.isna(prev) or pd.isna(cur):
        return "hold"
    if prev <= OVERSOLD and cur > OVERSOLD:
        return "buy"
    if prev >= OVERBOUGHT and cur < OVERBOUGHT:
        return "sell"
    return "hold"
