"""Tests for worker configuration."""

import pytest
from worker.config import WorkerConfig


def test_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify WorkerConfig loads all environment variables correctly."""
    monkeypatch.setenv("QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123/queue")
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("TABLE_NAME", "test-table")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")

    config = WorkerConfig.from_env()
    assert config.queue_url == "https://sqs.us-east-1.amazonaws.com/123/queue"
    assert config.bucket_name == "test-bucket"
    assert config.table_name == "test-table"
    assert config.region == "us-west-2"
    assert config.poll_interval == 20
    assert config.visibility_timeout == 3600


def test_from_env_missing_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify WorkerConfig raises KeyError when required variables are missing."""
    monkeypatch.delenv("QUEUE_URL", raising=False)
    monkeypatch.delenv("BUCKET_NAME", raising=False)
    monkeypatch.delenv("TABLE_NAME", raising=False)

    with pytest.raises(KeyError):
        WorkerConfig.from_env()


def test_from_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify WorkerConfig uses default values when optional variables are absent."""
    monkeypatch.setenv("QUEUE_URL", "https://sqs.example.com/queue")
    monkeypatch.setenv("BUCKET_NAME", "bucket")
    monkeypatch.setenv("TABLE_NAME", "table")
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

    config = WorkerConfig.from_env()
    assert config.region == "us-east-1"
