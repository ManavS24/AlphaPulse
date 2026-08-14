# Deployment

The **dashboard** deploys for free on [Streamlit Community Cloud](https://share.streamlit.io/). It
runs entirely on the committed sample data and trained model, so it needs no broker credentials and
no secrets.

> **Do not deploy live trading.** Live mode needs Upstox OAuth and places real orders — keep it a
> local-only script. Only the offline dashboard is deployed.

## Steps

1. Push the repository to GitHub (public). Confirm `models/signal_model.pkl` and
   `data/sample/banknifty_5m.csv` are actually tracked — `git ls-files models data` should list
   both. Without the model the app still runs, but the ML filter silently disables and the
   Rule-vs-ML tab shows no difference.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
3. **New app** → select your repo, branch `main`, main file path **`app/dashboard.py`**.
4. (Optional) **Advanced settings** → Python version `3.11`.
5. **Deploy.** Streamlit installs from `requirements.txt` and builds the app.
6. You get a public URL like `https://<your-app>.streamlit.app` — put it in the README and on your
   resume.

## Why a separate `requirements.txt`?

Streamlit Community Cloud installs from `requirements.txt`. It lists only the packages the
**dashboard** actually imports — deliberately **excluding `upstox-python-sdk`**, since the deployed
app never touches the broker (it only backtests offline). This keeps the build small and fast. The
full dependency set (including Upstox) lives in `pyproject.toml` for local development.

Two pins matter there:

- `scikit-learn` and `joblib` are pinned exactly. The committed model is a pickled scikit-learn
  pipeline, and unpickling is not guaranteed across major versions. If you bump either, retrain
  with `python scripts/train_model.py` and commit the new model.
- `streamlit>=1.50` is a floor, required for the `width=` argument used by the dashboard tables.

## Environment variables & secrets

None are required for the deployed dashboard. If you later add read-only live data, use Streamlit's
encrypted **Secrets** manager (App → Settings → Secrets) — never commit credentials.

## Data & model

- `data/sample/banknifty_5m.csv` and `models/signal_model.pkl` are committed, so the app has
  everything it needs at startup.
- The SQLite trade log (`data/trades.db`) is **not** committed; the dashboard auto-seeds it from a
  baseline backtest on first load, tagging those rows `auto-seed` so they are distinguishable from
  runs a visitor saves themselves (`backtest`). The log is ephemeral — it resets on redeploy.

## Cost & maintenance

- **Cost:** free on the Community Cloud tier.
- **Maintenance:** push to `main` and the app redeploys automatically. Refresh the sample data or
  retrain the model whenever you like.
