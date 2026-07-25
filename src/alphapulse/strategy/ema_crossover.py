"""9/15 EMA crossover with volume and momentum confirmation; emits buy / sell / hold."""

import pandas as pd

from alphapulse.strategy.indicators import ema as calculate_ema

MIN_CANDLES = 20


def generate_signal(req_market_data: pd.DataFrame) -> str:
    """Return buy / sell / hold; needs >= MIN_CANDLES rows and adds EMA columns in place."""
    if req_market_data is None or req_market_data.empty:
        return "hold"

    if len(req_market_data) < MIN_CANDLES:
        return "hold"

    req_market_data["EMA_9"] = calculate_ema(req_market_data["Close"], 9)
    req_market_data["EMA_15"] = calculate_ema(req_market_data["Close"], 15)
    req_market_data["Avg_Volume_10"] = req_market_data["Volume"].rolling(window=10).mean()

    current = req_market_data.iloc[-1]
    previous = req_market_data.iloc[-2]

    current_close = current["Close"]
    current_ema_9 = current["EMA_9"]
    current_ema_15 = current["EMA_15"]
    current_volume = current["Volume"]
    current_avg_volume = current["Avg_Volume_10"]

    previous_ema_9 = previous["EMA_9"]
    previous_ema_15 = previous["EMA_15"]
    previous_close = previous["Close"]

    bullish_crossover = previous_ema_9 <= previous_ema_15 and current_ema_9 > current_ema_15
    bearish_crossover = previous_ema_9 >= previous_ema_15 and current_ema_9 < current_ema_15

    price_above_emas = current_close > current_ema_9 and current_close > current_ema_15
    price_below_emas = current_close < current_ema_9 and current_close < current_ema_15

    volume_confirmation = current_volume > current_avg_volume
    bullish_momentum = current_close > previous_close
    bearish_momentum = current_close < previous_close

    ema_9_rising = current_ema_9 > req_market_data.iloc[-3]["EMA_9"]
    ema_9_falling = current_ema_9 < req_market_data.iloc[-3]["EMA_9"]

    if bullish_crossover and price_above_emas and volume_confirmation and bullish_momentum and ema_9_rising:
        return "buy"

    if bearish_crossover and price_below_emas and volume_confirmation and bearish_momentum and ema_9_falling:
        return "sell"

    # Uptrend continuation: EMA gap widening.
    if (
        current_ema_9 > current_ema_15
        and previous_ema_9 > previous_ema_15
        and price_above_emas
        and bullish_momentum
        and volume_confirmation
        and (current_ema_9 - current_ema_15) > (previous_ema_9 - previous_ema_15)
    ):
        return "buy"

    # Downtrend continuation: EMA gap widening.
    if (
        current_ema_9 < current_ema_15
        and previous_ema_9 < previous_ema_15
        and price_below_emas
        and bearish_momentum
        and volume_confirmation
        and (current_ema_15 - current_ema_9) > (previous_ema_15 - previous_ema_9)
    ):
        return "sell"

    return "hold"
