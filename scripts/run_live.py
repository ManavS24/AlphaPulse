"""Run the bot in LIVE mode (real orders, real money). Use run_paper.py for a risk-free run.

    python scripts/run_live.py
"""

from alphapulse.engine.runner import main

if __name__ == "__main__":
    main(mode="live")
