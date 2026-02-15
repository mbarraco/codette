import time

from sqlalchemy import text

from app.adapters.db import SessionLocal
from app.adapters.local_task_run import LocalGraderAdapter, LocalRunnerAdapter
from app.adapters.repository.run import RunRepository
from app.adapters.repository.submission_evaluation import SubmissionEvaluationRepository
from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.adapters.storage import StorageAdapter
from app.adapters.task_run import GcpGraderAdapter, GcpRunnerAdapter
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

    if settings.gcp_project is not None:
        # Production: GCP Cloud Run Jobs
        runner_adapter = GcpRunnerAdapter(
            project=settings.gcp_project,
            location=settings.gcp_location,
            job_name=settings.runner_job_name,
        )
        grader_adapter = GcpGraderAdapter(
            project=settings.gcp_project,
            location=settings.gcp_location,
            job_name=settings.grader_job_name,
        )
    elif settings.storage_emulator_host:
        # Local mode: Docker sibling containers
        logger.info("Local mode — using Docker containers for runner/grader")
        runner_adapter = LocalRunnerAdapter(
            image_name=settings.runner_image,
            network=settings.docker_network,
            storage_bucket=settings.storage_bucket,
            storage_emulator_host=settings.storage_emulator_host,
        )
        grader_adapter = LocalGraderAdapter(
            image_name=settings.grader_image,
            network=settings.docker_network,
            storage_bucket=settings.storage_bucket,
            storage_emulator_host=settings.storage_emulator_host,
        )
    else:
        logger.warning(
            "Neither GCP_PROJECT nor STORAGE_EMULATOR_HOST set — worker idling. "
            "Set GCP_PROJECT for production or STORAGE_EMULATOR_HOST for local dev."
        )
        while True:
            time.sleep(10)

    storage = StorageAdapter(settings.storage_bucket)
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
