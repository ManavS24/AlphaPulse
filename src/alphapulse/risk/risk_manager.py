"""Risk management: enforce stop-loss, take-profit, max trades per day, and max daily loss."""

from dataclasses import dataclass
from typing import Protocol


class RiskLimits(Protocol):
    """The four risk thresholds; satisfied by both Settings and RiskParams."""

    stop_loss: float
    take_profit: float
    max_daily_loss: float
    max_trades_per_day: int


@dataclass
class RiskParams:
    stop_loss: float = 1000.0
    take_profit: float = 2000.0
    max_daily_loss: float = 3000.0
    max_trades_per_day: int = 5


@dataclass
class RiskDecision:
    """reason is STOP_LOSS / TAKE_PROFIT / MAX_TRADES_PER_DAY / MAX_DAILY_LOSS, or None when continuing."""

    continue_trading: bool
    reason: str | None = None


def check_risk(
    limits: RiskLimits,
    trade_history: list[dict],
    current_pnl: float,
    current_position_pnl: float = 0.0,
) -> RiskDecision:
    """Return a RiskDecision; checks daily loss, then trade count, then stop-loss / take-profit."""
    if current_pnl <= -limits.max_daily_loss:
        return RiskDecision(False, "MAX_DAILY_LOSS")

    if len(trade_history) >= limits.max_trades_per_day:
        return RiskDecision(False, "MAX_TRADES_PER_DAY")

    if current_position_pnl <= -limits.stop_loss:
        return RiskDecision(False, "STOP_LOSS")

    if current_position_pnl >= limits.take_profit:
        return RiskDecision(False, "TAKE_PROFIT")

    return RiskDecision(True, None)
