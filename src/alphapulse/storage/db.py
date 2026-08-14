"""A minimal SQLite trade log (stdlib sqlite3, single file)."""

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from alphapulse.paths import data_dir

if TYPE_CHECKING:
    from alphapulse.engine.backtest import Trade

DEFAULT_DB_PATH = data_dir() / "trades.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    entry_time  TEXT,
    entry_price REAL,
    exit_time   TEXT,
    exit_price  REAL,
    direction   TEXT,
    quantity    INTEGER,
    pnl         REAL,
    exit_reason TEXT,
    created_at  TEXT NOT NULL
)
"""


def init_db(path: str | Path = DEFAULT_DB_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(_SCHEMA)


def save_trades(trades: "list[Trade]", source: str, path: str | Path = DEFAULT_DB_PATH) -> int:
    """Append trades tagged with source (backtest / paper / live); returns the count written."""
    init_db(path)
    now = datetime.now().isoformat(timespec="seconds")
    rows = [
        (
            source,
            str(t.entry_time),
            t.entry_price,
            str(t.exit_time),
            t.exit_price,
            t.direction,
            t.quantity,
            t.pnl,
            t.exit_reason,
            now,
        )
        for t in trades
    ]
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.executemany(
            """INSERT INTO trades
               (source, entry_time, entry_price, exit_time, exit_price,
                direction, quantity, pnl, exit_reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
    return len(rows)


def load_trades(path: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    with closing(sqlite3.connect(path)) as conn:
        return pd.read_sql_query("SELECT * FROM trades ORDER BY entry_time", conn)


def clear_trades(path: str | Path = DEFAULT_DB_PATH) -> None:
    if not Path(path).exists():
        return
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("DELETE FROM trades")
