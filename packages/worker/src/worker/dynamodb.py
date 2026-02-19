"""DynamoDB job status management."""

from __future__ import annotations

from datetime import datetime, timezone

import boto3


def update_job_status(
    table_name: str,
    job_id: str,
    status: str,
    error: str | None = None,
) -> None:
    """Update job status in DynamoDB.

    Parameters
    ----------
    table_name : str
        DynamoDB table name.
    job_id : str
        Job identifier.
    status : str
        New status (PENDING, RUNNING, COMPLETED, FAILED).
    error : str, optional
        Error message if status is FAILED.

    """
    ddb = boto3.resource("dynamodb")
    table = ddb.Table(table_name)

    update_expr = "SET #s = :status, updatedAt = :now"
    expr_values: dict[str, str] = {
        ":status": status,
        ":now": datetime.now(tz=timezone.utc).isoformat(),
    }
    expr_names = {"#s": "status"}

    if error:
        update_expr += ", #e = :error"
        expr_values[":error"] = error
        expr_names["#e"] = "error"

    table.update_item(
        Key={"jobId": job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        ExpressionAttributeNames=expr_names,
    )
