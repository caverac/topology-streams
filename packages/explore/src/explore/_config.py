"""Configuration for the AWS API backend."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiConfig:
    """API configuration loaded from environment variables.

    Attributes
    ----------
    api_url : str
        Base URL of the TopoStreams API Gateway.
    region : str
        AWS region for SigV4 signing.

    """

    api_url: str
    region: str

    @classmethod
    def from_env(cls) -> ApiConfig:
        """Load configuration from environment variables.

        Raises
        ------
        RuntimeError
            If TOPOSTREAMS_API_URL is not set.

        """
        api_url = os.environ.get("TOPOSTREAMS_API_URL")
        if not api_url:
            raise RuntimeError(
                "TOPOSTREAMS_API_URL environment variable is not set. "
                "Set it to the API Gateway URL (e.g. https://xxx.execute-api.us-east-1.amazonaws.com/prod)."
            )
        region = os.environ.get("TOPOSTREAMS_REGION", "us-east-1")
        return cls(api_url=api_url.rstrip("/"), region=region)
