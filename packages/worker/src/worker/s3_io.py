"""S3 result upload utilities."""

from __future__ import annotations

import io
from typing import Any

import boto3
import numpy as np


def upload_results(
    bucket_name: str,
    job_id: str,
    results: dict[str, bytes | str],
) -> None:
    """Upload result files to S3 under jobs/{jobId}/.

    Parameters
    ----------
    bucket_name : str
        S3 bucket name.
    job_id : str
        Job identifier.
    results : dict
        Mapping of filename to content (bytes or str).

    """
    s3 = boto3.client("s3")
    for filename, content in results.items():
        key = f"jobs/{job_id}/{filename}"
        if isinstance(content, str):
            content = content.encode("utf-8")
        s3.put_object(Bucket=bucket_name, Key=key, Body=content)


def save_npz_to_bytes(**arrays: Any) -> bytes:
    """Save numpy arrays to an in-memory NPZ file and return bytes."""
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    buf.seek(0)
    return buf.read()


def save_table_to_bytes(table: Any) -> bytes:
    """Save an astropy Table to ECSV bytes."""
    buf = io.StringIO()
    table.write(buf, format="ascii.ecsv")
    return buf.getvalue().encode("utf-8")
