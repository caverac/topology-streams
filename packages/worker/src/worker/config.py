"""Worker configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkerConfig:
    """Configuration loaded from environment variables."""

    queue_url: str
    bucket_name: str
    table_name: str
    region: str
    poll_interval: int = 20  # seconds
    visibility_timeout: int = 3600  # 60 minutes

    @classmethod
    def from_env(cls) -> WorkerConfig:
        """Load configuration from environment variables."""
        return cls(
            queue_url=os.environ["QUEUE_URL"],
            bucket_name=os.environ["BUCKET_NAME"],
            table_name=os.environ["TABLE_NAME"],
            region=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            poll_interval=int(os.environ.get("POLL_INTERVAL", "20")),
            visibility_timeout=int(os.environ.get("VISIBILITY_TIMEOUT", "3600")),
        )
