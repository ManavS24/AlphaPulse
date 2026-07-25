"""Train the ML signal classifier and save it to models/signal_model.pkl.

    python scripts/train_model.py [--data candles.csv]

Uses a time-ordered (non-shuffled) split so reported metrics don't leak future information.
"""

import argparse
from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from alphapulse.data.loader import load_candles_csv
from alphapulse.strategy.features import build_training_set

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "sample" / "banknifty_5m.csv"
MODEL_PATH = ROOT / "models" / "signal_model.pkl"
TEST_FRACTION = 0.25


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the ML signal filter.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()

    candles = load_candles_csv(args.data)
    X, y = build_training_set(candles)

    split = int(len(X) * (1 - TEST_FRACTION))
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(f"Training samples: {len(X_train)} | Test samples: {len(X_test)}")
    print(f"Baseline (always-up): {y_test.mean():.3f}")
    print(f"Accuracy : {accuracy_score(y_test, preds):.3f}")
    print(f"Precision: {precision_score(y_test, preds, zero_division=0):.3f}")
    print(f"Recall   : {recall_score(y_test, preds, zero_division=0):.3f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Saved model -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
