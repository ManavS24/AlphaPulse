"""Bollinger Band mean-reversion: buy when price re-enters from below the lower band, sell from above the upper."""

import pandas as pd

from alphapulse.strategy.indicators import bollinger_bands

MIN_CANDLES = 25


def generate_signal(df: pd.DataFrame, period: int = 20, num_std: float = 2.0) -> str:
    if df is None or df.empty or len(df) < MIN_CANDLES:
        return "hold"
    _, upper, lower = bollinger_bands(df["Close"], period, num_std)
    prev_close, cur_close = df["Close"].iloc[-2], df["Close"].iloc[-1]
    prev_lower, cur_lower = lower.iloc[-2], lower.iloc[-1]
    prev_upper, cur_upper = upper.iloc[-2], upper.iloc[-1]
    if any(pd.isna(x) for x in (prev_lower, cur_lower, prev_upper, cur_upper)):
        return "hold"
    if prev_close <= prev_lower and cur_close > cur_lower:
        return "buy"
    if prev_close >= prev_upper and cur_close < cur_upper:
        return "sell"
    return "hold"
