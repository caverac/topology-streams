"""SigV4-signed HTTP client for the TopoStreams API."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSPreparedRequest
from explore._config import ApiConfig


class ApiClient:
    """Client for the TopoStreams API with IAM (SigV4) authentication."""

    def __init__(self, config: ApiConfig | None = None) -> None:
        """Initialize the client with optional config."""
        self.config = config or ApiConfig.from_env()
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            raise RuntimeError("No AWS credentials found. Configure boto3 credentials.")
        self._credentials = credentials.get_frozen_credentials()
        self._region = self.config.region

    def _sign_request(self, method: str, url: str, body: str | None = None) -> dict[str, str]:
        """Sign a request with SigV4 and return headers."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        request = AWSPreparedRequest(
            method=method,
            url=url,
            headers=headers,
            body=body or "",
            stream_output=False,
        )
        SigV4Auth(self._credentials, "execute-api", self._region).add_auth(request)
        return dict(request.headers)

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a signed request to the API."""
        url = f"{self.config.api_url}{path}"
        body_str = json.dumps(body) if body else None
        headers = self._sign_request(method, url, body_str)

        req = Request(url, method=method, headers=headers)
        if body_str:
            req.data = body_str.encode("utf-8")

        try:
            with urlopen(req) as resp:
                result: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
                return result
        except HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"API request failed ({e.code}): {error_body}") from e

    def submit_job(self, stream_key: str, n_neighbors: int = 32, sigma_threshold: float = 3.0) -> dict[str, Any]:
        """Submit a new recovery job.

        Returns
        -------
        dict
            Response with jobId and status.

        """
        return self._request(
            "POST",
            "/jobs",
            {
                "streamKey": stream_key,
                "nNeighbors": n_neighbors,
                "sigmaThreshold": sigma_threshold,
            },
        )

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get the status of a job.

        Returns
        -------
        dict
            Job record with status, timestamps, etc.

        """
        return self._request("GET", f"/jobs/{job_id}")

    def get_job_results(self, job_id: str) -> dict[str, Any]:
        """Get presigned URLs for job results.

        Returns
        -------
        dict
            Response with jobId and files mapping.

        """
        return self._request("GET", f"/jobs/{job_id}/results")

    def get_catalog(self) -> dict[str, Any]:
        """Get the stream catalog.

        Returns
        -------
        dict
            Response with streams list.

        """
        return self._request("GET", "/catalog")
