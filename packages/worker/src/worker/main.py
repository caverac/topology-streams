"""SQS poll loop — main entry point for the worker process."""

from __future__ import annotations

import json
import logging
import signal
import traceback

import boto3
from worker.config import WorkerConfig
from worker.dynamodb import update_job_status
from worker.pipeline import STREAM_CATALOG, run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Module-level mutable container for graceful shutdown state.
_shutdown_state = {"should_stop": False}


class ProcessingError(Exception):
    """Raised when a pipeline message cannot be processed successfully."""


def _shutdown_handler(signum: int, _frame: object) -> None:
    """Handle SIGTERM/SIGINT by setting the shutdown flag."""
    logger.info("Received signal %d, shutting down gracefully...", signum)
    _shutdown_state["should_stop"] = True


def _install_signal_handlers() -> None:
    """Register signal handlers for graceful shutdown."""
    signal.signal(signal.SIGTERM, _shutdown_handler)
    signal.signal(signal.SIGINT, _shutdown_handler)


def process_message(config: WorkerConfig, body: dict[str, object]) -> None:
    """Process a single SQS message.

    Raises
    ------
    ProcessingError
        If the message is invalid or the pipeline fails.

    """
    try:
        job_id = str(body["jobId"])
        stream_key = str(body["streamKey"])
    except KeyError as exc:
        raise ProcessingError(f"Missing required field in message: {exc}") from exc

    raw_neighbors = body.get("nNeighbors", 32)
    n_neighbors = raw_neighbors if isinstance(raw_neighbors, int) else 32
    raw_sigma = body.get("sigmaThreshold", 3.0)
    sigma_threshold = raw_sigma if isinstance(raw_sigma, float) else 3.0

    if stream_key not in STREAM_CATALOG:
        raise ProcessingError(f"Unknown stream key: {stream_key}")

    update_job_status(config.table_name, job_id, "RUNNING")

    try:
        run_pipeline(
            bucket_name=config.bucket_name,
            job_id=job_id,
            stream_key=stream_key,
            n_neighbors=n_neighbors,
            sigma_threshold=sigma_threshold,
        )
        update_job_status(config.table_name, job_id, "COMPLETED")
    except ProcessingError:
        raise
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        logger.error("Job %s failed: %s", job_id, error_msg)
        update_job_status(config.table_name, job_id, "FAILED", error=error_msg[:1000])
        raise ProcessingError(f"Pipeline failed for job {job_id}: {exc}") from exc


def main() -> None:
    """Run the SQS poll loop."""
    config = WorkerConfig.from_env()
    _install_signal_handlers()
    sqs = boto3.client("sqs", region_name=config.region)

    logger.info("Worker started. Polling %s", config.queue_url)

    while not _shutdown_state["should_stop"]:
        response = sqs.receive_message(
            QueueUrl=config.queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=config.poll_interval,
            VisibilityTimeout=config.visibility_timeout,
        )

        messages = response.get("Messages", [])
        if not messages:
            continue

        msg = messages[0]
        receipt_handle = msg["ReceiptHandle"]

        try:
            body = json.loads(msg["Body"])
            logger.info("Processing job: %s", body.get("jobId"))
            process_message(config, body)
            sqs.delete_message(QueueUrl=config.queue_url, ReceiptHandle=receipt_handle)
            logger.info("Message deleted successfully")
        except (ProcessingError, json.JSONDecodeError, KeyError):
            logger.exception("Failed to process message")
            # Message will return to queue after visibility timeout

    logger.info("Worker shutdown complete")


if __name__ == "__main__":
    main()
