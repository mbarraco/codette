import logging
import sys

from app.core.settings import get_settings


def setup_logging() -> None:
    logging.basicConfig(
        level=get_settings().log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
