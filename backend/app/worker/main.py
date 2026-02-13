import time

from sqlalchemy import text

from app.adapters.db import SessionLocal
from app.adapters.repository.run import RunRepository
from app.adapters.repository.submission_evaluation import SubmissionEvaluationRepository
from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.adapters.storage import StorageAdapter
from app.adapters.task_run import GcpTaskRunAdapter
from app.core.logging import get_logger, setup_logging
from app.core.settings import get_settings
from app.worker.request_factory import ExecutionRequestFactory
from app.worker.sea import SeaWorker

setup_logging()
logger = get_logger(__name__)

_POLL_INTERVAL_S = 5


def main() -> None:
    logger.info("Starting worker...")
    settings = get_settings()

    # Test database connection
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
        logger.info("Connected to DB")

    if settings.gcp_project is None:
        logger.warning(
            "GCP_PROJECT not set — worker cannot launch Cloud Run Jobs. "
            "Set GCP_PROJECT to enable the SEA pipeline."
        )
        # Idle loop when GCP is not configured
        while True:
            time.sleep(10)

    storage = StorageAdapter(settings.storage_bucket)
    runner_adapter = GcpTaskRunAdapter(
        project=settings.gcp_project,
        location=settings.gcp_location,
        job_name=settings.runner_job_name,
    )
    grader_adapter = GcpTaskRunAdapter(
        project=settings.gcp_project,
        location=settings.gcp_location,
        job_name=settings.grader_job_name,
    )
    request_factory = ExecutionRequestFactory(
        storage_bucket=settings.storage_bucket,
        storage=storage,
    )

    logger.info("Worker ready — polling for jobs...")

    while True:
        try:
            with SessionLocal() as db:
                worker = SeaWorker(
                    db=db,
                    queue_repo=SubmissionQueueRepository(),
                    run_repo=RunRepository(),
                    eval_repo=SubmissionEvaluationRepository(),
                    storage=storage,
                    runner_adapter=runner_adapter,
                    grader_adapter=grader_adapter,
                    request_factory=request_factory,
                )
                entry = worker.process_next()
                if entry is not None:
                    logger.info("Processed queue entry %s", entry.id)
                    db.commit()
        except Exception:
            logger.exception("Error processing queue entry")

        time.sleep(_POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
