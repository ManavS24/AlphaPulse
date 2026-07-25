"""Trading loop for ATM options; the same loop runs live or paper — only the broker differs."""

import time
from datetime import datetime, timedelta

from alphapulse.broker import Broker, PaperBroker, UpstoxBroker
from alphapulse.config import Settings, get_settings
from alphapulse.logging_setup import get_logger, setup_logging
from alphapulse.risk import check_risk
from alphapulse.strategy import process_market_data
from alphapulse.strategy.ml_filter import MLSignalFilter

logger = get_logger(__name__)

SEPARATOR = "=" * 80
EXIT_PRICE_RETRIES = 3
EXIT_PRICE_RETRY_DELAY = 1.0


def get_current_expiry() -> str:
    """Return the current weekly expiry (nearest Thursday) formatted like 31JUL."""
    today = datetime.now()
    days_until_thursday = (3 - today.weekday()) % 7
    expiry_date = today + timedelta(days=days_until_thursday)
    return expiry_date.strftime("%d%b").upper()


def get_atm_option_instrument(underlying_price: float, expiry_date: str, option_type: str) -> str:
    """Build an ATM option instrument key (option_type CE=call, PE=put)."""
    atm_strike = round(underlying_price / 50) * 50
    return f"NSE_FO|{atm_strike}{option_type}{expiry_date}"


def close_position(
    broker, position_instrument, position_entry_price, current_position,
    trade_history, current_pnl, quantity,
):
    """Close the position, record the trade, and return reset position state with updated pnl."""
    logger.info("%s", SEPARATOR)
    logger.info("📊 CLOSING POSITION: %s at %s", current_position, datetime.now().strftime("%H:%M:%S"))
    logger.info("%s", SEPARATOR)

    sell_result = broker.sell(position_instrument, quantity)

    if sell_result:
        exit_price = broker.get_price(position_instrument)
        for _ in range(EXIT_PRICE_RETRIES - 1):
            if exit_price is not None:
                break
            time.sleep(EXIT_PRICE_RETRY_DELAY)
            exit_price = broker.get_price(position_instrument)
        if exit_price is None or position_entry_price is None:
            logger.warning("✅ Closed %s but price unavailable; P&L not recorded", position_instrument)
            return None, None, 0.0, current_pnl
        trade_pnl = (exit_price - position_entry_price) * quantity
        current_pnl += trade_pnl

        trade_history.append({
            "entry_time": datetime.now(),
            "entry_price": position_entry_price,
            "exit_price": exit_price,
            "quantity": quantity,
            "pnl": trade_pnl,
            "signal": current_position,
            "instrument": position_instrument,
        })

        logger.info("✅ Position closed | %s | entry %.2f exit %.2f qty %d | P&L %s %.2f",
                    position_instrument, position_entry_price, exit_price, quantity,
                    "📈" if trade_pnl > 0 else "📉", trade_pnl)
    else:
        logger.error("❌ Failed to close position")

    return None, None, 0.0, current_pnl


def print_trading_summary(trade_history, current_pnl, runtime):
    logger.info("%s", SEPARATOR)
    logger.info("📈 TRADING SESSION SUMMARY - %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("  ⏱️  Runtime: %.2f minutes | 💰 P&L: %.2f | 🔢 Trades: %d",
                runtime, current_pnl, len(trade_history))

    if trade_history:
        profitable = len([t for t in trade_history if t["pnl"] > 0])
        losing = len([t for t in trade_history if t["pnl"] < 0])
        win_rate = profitable / len(trade_history) * 100
        logger.info("  ✅ Wins: %d | ❌ Losses: %d | 📊 Win rate: %.2f%%", profitable, losing, win_rate)
        logger.info("  Recent trades:")
        for i, trade in enumerate(trade_history[-3:]):
            logger.info("   %d. %s - %s %.2f", i + 1, trade["instrument"],
                        "📈" if trade["pnl"] > 0 else "📉", trade["pnl"])
    logger.info("%s", SEPARATOR)


def manage_trades(broker: Broker, settings: Settings | None = None, ml_filter=None) -> dict:
    """Run the ATM-options trading loop via broker and return a session summary."""
    settings = settings or get_settings()
    if not broker.connect():
        logger.error("Could not connect broker. Aborting.")
        return {}

    instrument_key = settings.instrument_key
    unit = settings.unit
    interval = settings.interval
    quantity = settings.quantity
    trade_check_interval = settings.trade_check_interval
    max_runtime = settings.max_runtime

    trade_history: list[dict] = []
    current_pnl = 0.0
    start_time = time.time()
    last_signal = None
    iteration = 0
    current_position = None
    position_entry_price = 0.0
    position_instrument = None

    logger.info("%s", SEPARATOR)
    logger.info("🚀 TRADING SESSION STARTED - %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("  📈 Instrument: %s | 📊 %s %s | 🔢 Qty: %d | ⏱️ Check: %ss | ⏰ Max: %.2fh",
                instrument_key, interval, unit, quantity, trade_check_interval, max_runtime / 3600)
    logger.info("%s", SEPARATOR)

    while time.time() - start_time < max_runtime:
        iteration += 1
        elapsed_minutes = (time.time() - start_time) / 60

        logger.info("%s", "*" * 80)
        logger.info("ITERATION %d - %s (Runtime: %.2f min)",
                    iteration, datetime.now().strftime("%H:%M:%S"), elapsed_minutes)

        if iteration % 10 == 0:
            print_trading_summary(trade_history, current_pnl, elapsed_minutes)

        current_position_pnl = 0.0
        if current_position:
            current_price = broker.get_price(position_instrument)
            if current_price is None or position_entry_price is None:
                logger.warning("❌ Could not fetch price for %s; skipping P&L update", position_instrument)
            else:
                current_position_pnl = (current_price - position_entry_price) * quantity
                logger.info("📍 Position: %s | %s | entry %.2f cur %.2f | uP&L %s %.2f",
                            current_position, position_instrument, position_entry_price, current_price,
                            "📈" if current_position_pnl > 0 else "📉", current_position_pnl)
        else:
            logger.info("📍 No active position")

        risk = check_risk(settings, trade_history, current_pnl, current_position_pnl)
        if not risk.continue_trading:
            logger.warning("⚠️ RISK LIMIT REACHED: %s", risk.reason)

            if risk.reason in ("STOP_LOSS", "TAKE_PROFIT") and current_position:
                logger.info("⏰ %s triggered. Closing position immediately.", risk.reason)
                current_position, position_instrument, position_entry_price, current_pnl = close_position(
                    broker, position_instrument, position_entry_price, current_position,
                    trade_history, current_pnl, quantity,
                )

            if risk.reason in ("MAX_TRADES_PER_DAY", "MAX_DAILY_LOSS"):
                logger.warning("⛔ %s limit hit. Stopping trading.", risk.reason)
                if current_position:
                    current_position, position_instrument, position_entry_price, current_pnl = close_position(
                        broker, position_instrument, position_entry_price, current_position,
                        trade_history, current_pnl, quantity,
                    )
                break

        logger.info("📊 Fetching market data...")
        req_market_data = broker.get_candles(instrument_key, unit, interval)

        if req_market_data is None or req_market_data.empty:
            logger.warning("❌ No market data available")
            time.sleep(trade_check_interval)
            continue

        signal = process_market_data(req_market_data, ml_filter=ml_filter, strategy=settings.strategy)
        logger.info("🔍 Signal generated: %s", signal)

        underlying_price = broker.get_price(instrument_key)
        if underlying_price is None:
            logger.warning("❌ Could not fetch underlying price")
            time.sleep(trade_check_interval)
            continue
        logger.info("💹 Underlying price: %.2f", underlying_price)

        expiry_date = get_current_expiry()

        if signal not in ("hold", last_signal):
            logger.info("🔄 New signal detected: %s", signal)

            if current_position is not None:
                logger.info("🔄 Closing current position before taking new position")
                current_position, position_instrument, position_entry_price, current_pnl = close_position(
                    broker, position_instrument, position_entry_price, current_position,
                    trade_history, current_pnl, quantity,
                )

            if signal == "buy":
                atm_ce = get_atm_option_instrument(underlying_price, expiry_date, "CE")
                logger.info("🔷 BUY signal | ATM CE: %s", atm_ce)
                if broker.buy(atm_ce, quantity):
                    current_position = "CE"
                    position_instrument = atm_ce
                    position_entry_price = broker.get_price(atm_ce)
                    if position_entry_price is None:
                        logger.warning("✅ Bought ATM CE: %s (entry price unavailable)", atm_ce)
                    else:
                        logger.info("✅ Bought ATM CE: %s at %.2f", atm_ce, position_entry_price)
                else:
                    logger.error("❌ Failed to execute buy order")

            elif signal == "sell":
                atm_pe = get_atm_option_instrument(underlying_price, expiry_date, "PE")
                logger.info("🔶 SELL signal | ATM PE: %s", atm_pe)
                if broker.buy(atm_pe, quantity):
                    current_position = "PE"
                    position_instrument = atm_pe
                    position_entry_price = broker.get_price(atm_pe)
                    if position_entry_price is None:
                        logger.warning("✅ Bought ATM PE: %s (entry price unavailable)", atm_pe)
                    else:
                        logger.info("✅ Bought ATM PE: %s at %.2f", atm_pe, position_entry_price)
                else:
                    logger.error("❌ Failed to execute buy order")

        last_signal = signal
        logger.info("💰 P&L: %.2f | 📝 Trades: %d", current_pnl, len(trade_history))
        logger.info("⏱️ Waiting %s seconds until next check...", trade_check_interval)
        time.sleep(trade_check_interval)

    if current_position is not None:
        logger.info("⏰ Maximum runtime reached. Closing final position before session end.")
        current_position, position_instrument, position_entry_price, current_pnl = close_position(
            broker, position_instrument, position_entry_price, current_position,
            trade_history, current_pnl, quantity,
        )

    profitable = len([t for t in trade_history if t["pnl"] > 0])
    losing = len([t for t in trade_history if t["pnl"] < 0])
    win_rate = (profitable / len(trade_history) * 100) if trade_history else 0.0

    summary = {
        "total_trades": len(trade_history),
        "profitable_trades": profitable,
        "losing_trades": losing,
        "net_pnl": current_pnl,
        "win_rate": win_rate,
    }

    logger.info("%s", SEPARATOR)
    logger.info("🏁 TRADING SESSION ENDED - %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("  📈 Trades: %d | ✅ Wins: %d | ❌ Losses: %d | 💰 Net P&L: %.2f | 📊 Win rate: %.2f%%",
                summary["total_trades"], summary["profitable_trades"], summary["losing_trades"],
                summary["net_pnl"], summary["win_rate"])
    logger.info("%s", SEPARATOR)

    return summary


def main(mode: str = "live", use_ml: bool = True) -> None:
    """Entry point. ``mode`` is ``live`` (real orders) or ``paper`` (simulated fills)."""
    setup_logging()
    settings = get_settings()
    if mode == "paper":
        broker: Broker = PaperBroker(UpstoxBroker(settings))
    else:
        broker = UpstoxBroker(settings)
    ml_filter = MLSignalFilter.load() if use_ml else None
    summary = manage_trades(broker, settings, ml_filter=ml_filter)
    logger.info("Final Summary: %s", summary)


if __name__ == "__main__":
    main()
