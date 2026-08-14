"""ML signal filter: gates rule signals by predicted direction; a no-op when no model is loaded."""

from pathlib import Path

import joblib
import pandas as pd

from alphapulse.logging_setup import get_logger
from alphapulse.paths import models_dir
from alphapulse.strategy.features import latest_feature_row

logger = get_logger(__name__)

DEFAULT_MODEL_PATH = models_dir() / "signal_model.pkl"


class MLSignalFilter:
    """Gates signals by P(next candle up): buy needs P(up) >= buy_threshold, sell needs P(up) <= sell_threshold."""

    def __init__(self, model=None, buy_threshold: float = 0.58, sell_threshold: float = 0.42):
        self.model = model
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    @classmethod
    def load(cls, path: str | Path = DEFAULT_MODEL_PATH, **kwargs) -> "MLSignalFilter":
        path = Path(path)
        if not path.exists():
            logger.warning("ML model not found at %s — filter disabled (rule signals pass through).", path)
            return cls(model=None, **kwargs)
        try:
            return cls(model=joblib.load(path), **kwargs)
        except Exception as e:  # noqa: BLE001 - a corrupt/incompatible model must not crash the app
            logger.warning("Failed to load ML model (%s) — filter disabled.", e)
            return cls(model=None, **kwargs)

    @property
    def enabled(self) -> bool:
        return self.model is not None

    def prob_up(self, candles: pd.DataFrame) -> float | None:
        if self.model is None:
            return None
        row = latest_feature_row(candles)
        if row is None:
            return None
        return float(self.model.predict_proba(row)[0][1])

    def apply(self, signal: str, candles: pd.DataFrame) -> str:
        if self.model is None or signal not in ("buy", "sell"):
            return signal
        p_up = self.prob_up(candles)
        if p_up is None:
            return signal
        if signal == "buy" and p_up < self.buy_threshold:
            return "hold"
        if signal == "sell" and p_up > self.sell_threshold:
            return "hold"
        return signal
