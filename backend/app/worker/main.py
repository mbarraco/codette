import time

from sqlalchemy import text

from app.core.db import SessionLocal
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def main() -> None:
    logger.info("Starting worker...")

    # Test database connection
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
        logger.info("Connected to DB")

    logger.info("Waiting for jobs...")

    # Idle loop placeholder
    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
