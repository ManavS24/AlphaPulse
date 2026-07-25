"""Trading strategies: EMA, RSI, MACD, Bollinger — selectable, with an optional ML signal filter."""

import pandas as pd

from alphapulse.strategy import bollinger_strategy, ema_crossover, macd_strategy, rsi_strategy

STRATEGIES = {
    "ema": ema_crossover.generate_signal,
    "rsi": rsi_strategy.generate_signal,
    "macd": macd_strategy.generate_signal,
    "bollinger": bollinger_strategy.generate_signal,
}
DEFAULT_STRATEGY = "ema"


def get_strategy(name: str):
    """Return the signal function for a strategy name, or raise ValueError if unknown."""
    try:
        return STRATEGIES[name]
    except KeyError:
        raise ValueError(f"Unknown strategy '{name}'. Choose from {sorted(STRATEGIES)}") from None


def process_market_data(
    market_data_df: pd.DataFrame, ml_filter=None, strategy: str = DEFAULT_STRATEGY
) -> str:
    """Return buy / sell / hold from the chosen strategy; if an ml_filter is given, signals it vetoes become hold."""
    if market_data_df is None or market_data_df.empty:
        return "hold"
    signal = get_strategy(strategy)(market_data_df)
    if ml_filter is not None:
        signal = ml_filter.apply(signal, market_data_df)
    return signal
