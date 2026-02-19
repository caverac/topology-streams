"""Tests for DynamoDB job status updates."""

from collections.abc import Generator
from typing import Any

import boto3
import pytest

try:
    from moto import mock_aws

    MOTO_AVAILABLE = True
except ImportError:
    MOTO_AVAILABLE = False

from worker.dynamodb import update_job_status

pytestmark = pytest.mark.skipif(not MOTO_AVAILABLE, reason="moto not available")


@pytest.fixture
def ddb_table() -> Generator[Any, None, None]:
    """Create a mock DynamoDB table with a single pending job."""
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        table = ddb.create_table(
            TableName="test-jobs",
            KeySchema=[{"AttributeName": "jobId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "jobId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.put_item(Item={"jobId": "job-1", "status": "PENDING"})
        yield table


@pytest.mark.usefixtures("ddb_table")
def test_update_status() -> None:
    """Verify that update_job_status transitions a job to RUNNING and sets updatedAt."""
    with mock_aws():
        # Re-create table in the mock context
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        table = ddb.create_table(
            TableName="test-jobs",
            KeySchema=[{"AttributeName": "jobId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "jobId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.put_item(Item={"jobId": "job-1", "status": "PENDING"})

        update_job_status("test-jobs", "job-1", "RUNNING")
        item = table.get_item(Key={"jobId": "job-1"})["Item"]
        assert item["status"] == "RUNNING"
        assert "updatedAt" in item


@pytest.mark.usefixtures("ddb_table")
def test_update_status_with_error() -> None:
    """Verify that update_job_status sets FAILED status and stores the error message."""
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        table = ddb.create_table(
            TableName="test-jobs",
            KeySchema=[{"AttributeName": "jobId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "jobId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.put_item(Item={"jobId": "job-2", "status": "RUNNING"})

        update_job_status("test-jobs", "job-2", "FAILED", error="Something went wrong")
        item = table.get_item(Key={"jobId": "job-2"})["Item"]
        assert item["status"] == "FAILED"
        assert item["error"] == "Something went wrong"
