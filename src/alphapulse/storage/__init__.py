"""Persistence: a small SQLite trade log."""

from alphapulse.storage.db import (
    DEFAULT_DB_PATH,
    clear_trades,
    init_db,
    load_trades,
    save_trades,
)

__all__ = ["DEFAULT_DB_PATH", "clear_trades", "init_db", "load_trades", "save_trades"]
