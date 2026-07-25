"""Upstox broker: authentication, order execution, and live price quotes."""

import pandas as pd
import upstox_client
from upstox_client.rest import ApiException

from alphapulse.broker.base import Broker
from alphapulse.config import Settings
from alphapulse.data.market_data import market_data
from alphapulse.logging_setup import get_logger

logger = get_logger(__name__)


def account_connect(settings: Settings) -> dict | None:
    """Interactive Upstox OAuth flow (live only); returns account details, or None on failure."""
    url = (
        "https://api.upstox.com/v2/login/authorization/dialog"
        f"?response_type=code&client_id={settings.upstox_api_key}"
        f"&redirect_uri={settings.upstox_redirect_uri}&state=aback"
    )

    logger.info("Please visit the following URL to authorize the application:")
    logger.info(url)

    output_url = input("After authorizing, please enter the URL you were redirected to: ")

    if settings.upstox_redirect_uri not in output_url:
        logger.error("The URL does not match the expected redirect URI.")
        return None

    code = output_url.split("code=")[-1].split("&")[0]
    api_instance = upstox_client.LoginApi()
    try:
        api_response = api_instance.token(
            "2.0",
            code=code,
            client_id=settings.upstox_api_key,
            client_secret=settings.upstox_api_secret,
            redirect_uri=settings.upstox_redirect_uri,
            grant_type="authorization_code",
        )
        return {
            "email": api_response.email,
            "exchanges": api_response.exchanges,
            "products": api_response.products,
            "broker": api_response.broker,
            "user_id": api_response.user_id,
            "user_name": api_response.user_name,
            "order_types": api_response.order_types,
            "user_type": api_response.user_type,
            "poa": api_response.poa,
            "is_active": api_response.is_active,
            "access_token": api_response.access_token,
            "extended_token": api_response.extended_token,
        }
    except ApiException as e:
        logger.error("Exception when calling LoginApi->token: %s", e)
        return None


def _order_api(access_token: str) -> "upstox_client.OrderApiV3":
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token
    return upstox_client.OrderApiV3(upstox_client.ApiClient(configuration))


def _place_order(access_token: str, instrument_key: str, quantity: int, side: str):
    api_instance = _order_api(access_token)
    body = upstox_client.PlaceOrderV3Request(
        quantity=quantity,
        product="D",
        validity="DAY",
        price=0,
        tag="algo-bot",
        instrument_token=instrument_key,
        order_type="MARKET",
        transaction_type=side,
        disclosed_quantity=0,
        trigger_price=0.0,
        is_amo=False,
        slice=True,
    )
    try:
        return api_instance.place_order(body)
    except ApiException as e:
        logger.error("Exception when calling OrderApiV3->place_order (%s): %s", side, e)
        return None


def execute_buy_order(access_token: str, instrument_key: str, quantity: int):
    return _place_order(access_token, instrument_key, quantity, "BUY")


def execute_sell_order(access_token: str, instrument_key: str, quantity: int):
    return _place_order(access_token, instrument_key, quantity, "SELL")


def get_live_price(access_token: str, instrument_key: str) -> float | None:
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token
    api_instance = upstox_client.MarketQuoteApi(upstox_client.ApiClient(configuration))
    try:
        api_response = api_instance.get_full_market_quote(instrument_key, "2.0")
        if api_response.data:
            for quote in api_response.data.values():
                return quote.last_price
        return None
    except ApiException as e:
        logger.error("Exception when calling MarketQuoteApi->get_full_market_quote: %s", e)
        return None


class UpstoxBroker(Broker):
    """Real Upstox broker — places live orders with real money."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.access_token: str | None = None
        self.account: dict | None = None

    def connect(self) -> bool:
        self.account = account_connect(self.settings)
        if not self.account:
            return False
        self.access_token = self.account.get("access_token")
        logger.info("🔴 LIVE MODE — connected as %s", self.account.get("user_name", "unknown"))
        return self.access_token is not None

    def get_candles(self, instrument_key: str, unit: str, interval: str) -> pd.DataFrame:
        return market_data(self.access_token, instrument_key, unit, interval)

    def get_price(self, instrument_key: str) -> float | None:
        return get_live_price(self.access_token, instrument_key)

    def buy(self, instrument_key: str, quantity: int) -> bool:
        return execute_buy_order(self.access_token, instrument_key, quantity) is not None

    def sell(self, instrument_key: str, quantity: int) -> bool:
        return execute_sell_order(self.access_token, instrument_key, quantity) is not None
