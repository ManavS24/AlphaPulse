"""MACD crossover: buy when the MACD line crosses above its signal line, sell when below."""

import pandas as pd

from alphapulse.strategy.indicators import macd

MIN_CANDLES = 35


def generate_signal(df: pd.DataFrame) -> str:
    if df is None or df.empty or len(df) < MIN_CANDLES:
        return "hold"
    macd_line, signal_line, _ = macd(df["Close"])
    prev_macd, prev_signal = macd_line.iloc[-2], signal_line.iloc[-2]
    cur_macd, cur_signal = macd_line.iloc[-1], signal_line.iloc[-1]
    if any(pd.isna(x) for x in (prev_macd, prev_signal, cur_macd, cur_signal)):
        return "hold"
    if prev_macd <= prev_signal and cur_macd > cur_signal:
        return "buy"
    if prev_macd >= prev_signal and cur_macd < cur_signal:
        return "sell"
    return "hold"
