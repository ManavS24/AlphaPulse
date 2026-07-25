"""Paper-trading broker: real live market data, simulated order fills, zero real money."""

from dataclasses import dataclass, field

import pandas as pd

from alphapulse.broker.base import Broker
from alphapulse.logging_setup import get_logger

logger = get_logger(__name__)


@dataclass
class Fill:
    instrument_key: str
    side: str  # BUY | SELL
    quantity: int
    price: float


@dataclass
class PaperBroker(Broker):
    """Delegates market data to a real broker but fills orders in memory at the live price."""

    data_broker: Broker
    positions: dict[str, int] = field(default_factory=dict)
    fills: list[Fill] = field(default_factory=list)

    def connect(self) -> bool:
        logger.info("📝 PAPER MODE — no real orders will be placed.")
        return self.data_broker.connect()

    def get_candles(self, instrument_key: str, unit: str, interval: str) -> pd.DataFrame:
        return self.data_broker.get_candles(instrument_key, unit, interval)

    def get_price(self, instrument_key: str) -> float | None:
        return self.data_broker.get_price(instrument_key)

    def _fill(self, instrument_key: str, quantity: int, side: str) -> bool:
        price = self.get_price(instrument_key)
        if price is None:
            logger.warning("📝 Paper %s rejected: no price for %s", side, instrument_key)
            return False
        signed = quantity if side == "BUY" else -quantity
        self.positions[instrument_key] = self.positions.get(instrument_key, 0) + signed
        self.fills.append(Fill(instrument_key, side, quantity, price))
        logger.info("📝 Paper %s %d %s @ %.2f", side, quantity, instrument_key, price)
        return True

    def buy(self, instrument_key: str, quantity: int) -> bool:
        return self._fill(instrument_key, quantity, "BUY")

    def sell(self, instrument_key: str, quantity: int) -> bool:
        return self._fill(instrument_key, quantity, "SELL")
