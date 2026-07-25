"""Tests for the broker abstraction and the paper-trading broker."""

import pandas as pd

from alphapulse.broker.base import Broker
from alphapulse.broker.paper import PaperBroker


class FakeDataBroker(Broker):
    """A deterministic in-memory broker used to drive PaperBroker in tests (no network)."""

    def __init__(self, price: float = 100.0):
        self.price = price
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def get_candles(self, instrument_key, unit, interval) -> pd.DataFrame:
        return pd.DataFrame({"Close": [self.price], "Volume": [1]})

    def get_price(self, instrument_key) -> float:
        return self.price

    def buy(self, instrument_key, quantity) -> bool:
        return True

    def sell(self, instrument_key, quantity) -> bool:
        return True


def test_paper_broker_connect_delegates():
    data = FakeDataBroker()
    paper = PaperBroker(data)
    assert paper.connect() is True
    assert data.connected is True


def test_paper_buy_updates_position_and_records_fill():
    paper = PaperBroker(FakeDataBroker(price=250.0))
    assert paper.buy("NSE_FO|48000CE", 15) is True
    assert paper.positions["NSE_FO|48000CE"] == 15
    assert len(paper.fills) == 1
    assert paper.fills[0].price == 250.0
    assert paper.fills[0].side == "BUY"


def test_paper_sell_reduces_position():
    paper = PaperBroker(FakeDataBroker())
    paper.buy("X", 10)
    paper.sell("X", 4)
    assert paper.positions["X"] == 6


def test_paper_get_price_and_candles_delegate():
    paper = PaperBroker(FakeDataBroker(price=123.0))
    assert paper.get_price("X") == 123.0
    assert not paper.get_candles("X", "minutes", "5").empty


def test_paper_broker_is_a_broker():
    assert isinstance(PaperBroker(FakeDataBroker()), Broker)
