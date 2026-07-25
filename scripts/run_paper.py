"""Run the bot in PAPER mode: real live prices, simulated fills, no real money.

    python scripts/run_paper.py
"""

from alphapulse.engine.runner import main

if __name__ == "__main__":
    main(mode="paper")
