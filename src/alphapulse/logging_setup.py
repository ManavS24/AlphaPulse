"""Rich-based logging configuration."""

import logging

from rich.logging import RichHandler


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False, markup=True)],
    )
    return logging.getLogger("alphapulse")


def get_logger(name: str = "alphapulse") -> logging.Logger:
    return logging.getLogger(name)
