"""Typed application configuration loaded from the environment / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime config; env var names map case-insensitively (UPSTOX_API_KEY -> upstox_api_key)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    upstox_redirect_uri: str
    upstox_api_key: str
    upstox_api_secret: str

    instrument_key: str
    unit: str = "minutes"
    interval: str = "5"
    strategy: str = "ema"  # ema | rsi | macd | bollinger

    quantity: int
    stop_loss: float
    take_profit: float
    max_trades_per_day: int
    max_daily_loss: float
    trade_check_interval: float = 60.0
    max_runtime: float = 3600.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


if __name__ == "__main__":
    for key, value in get_settings().model_dump().items():
        if any(s in key for s in ("secret", "key", "token")):
            value = "***"
        print(f"{key}: {value}")
