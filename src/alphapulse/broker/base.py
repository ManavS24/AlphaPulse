"""Broker interface the engine depends on, so live and paper execution share one code path."""

from abc import ABC, abstractmethod

import pandas as pd


class Broker(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Establish a session. Returns True on success."""

    @abstractmethod
    def get_candles(self, instrument_key: str, unit: str, interval: str) -> pd.DataFrame:
        """Return recent OHLCV candles, or an empty DataFrame if unavailable."""

    @abstractmethod
    def get_price(self, instrument_key: str) -> float | None:
        """Return the latest traded price, or None on failure."""

    @abstractmethod
    def buy(self, instrument_key: str, quantity: int) -> bool:
        """Place a market BUY order. Returns True if accepted."""

    @abstractmethod
    def sell(self, instrument_key: str, quantity: int) -> bool:
        """Place a market SELL order. Returns True if accepted."""
