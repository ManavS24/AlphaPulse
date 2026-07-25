"""Broker integrations: a common interface with real (Upstox) and simulated (paper) backends."""

from alphapulse.broker.base import Broker
from alphapulse.broker.paper import PaperBroker
from alphapulse.broker.upstox import UpstoxBroker

__all__ = ["Broker", "PaperBroker", "UpstoxBroker"]
