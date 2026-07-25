"""Fetch historical / intraday candle data from Upstox as a pandas DataFrame."""

import pandas as pd
import upstox_client

from alphapulse.logging_setup import get_logger

logger = get_logger(__name__)

CANDLE_COLUMNS = ["Timestamp", "Open", "High", "Low", "Close", "Volume", "Open Interest"]


def market_data(access_token: str, instrument_key: str, unit: str, interval: str) -> pd.DataFrame:
    """Return intraday OHLCV candles for an instrument, or an empty DataFrame if unavailable."""
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token
    api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))

    try:
        response = api_instance.get_intra_day_candle_data(
            instrument_key=instrument_key, unit=unit, interval=interval
        )
    except Exception as e:  # noqa: BLE001 - Upstox SDK raises varied exceptions
        logger.error("Failed to fetch market data: %s", e)
        return pd.DataFrame()

    if response.status == "success" and response.data and response.data.candles:
        df = pd.DataFrame(response.data.candles, columns=CANDLE_COLUMNS)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        return df

    return pd.DataFrame()
