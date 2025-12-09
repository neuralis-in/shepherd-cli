"""Langfuse provider client."""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Any

import httpx

from shepherd.models.langfuse import (
    LangfuseObservation,
    LangfuseObservationsResponse,
    LangfuseScore,
    LangfuseScoresResponse,
    LangfuseSession,
    LangfuseSessionsResponse,
    LangfuseTrace,
    LangfuseTracesResponse,
)


class LangfuseError(Exception):
    """Base exception for Langfuse errors."""

    pass


class AuthenticationError(LangfuseError):
    """Authentication failed."""

    pass


class NotFoundError(LangfuseError):
    """Resource not found."""

    pass


class RateLimitError(LangfuseError):
    """Rate limit exceeded."""

    pass


class LangfuseClient:
    """Client for Langfuse API.

    Uses Basic Auth with public_key:secret_key.
    API Reference: https://api.reference.langfuse.com/
    """

    DEFAULT_HOST = "https://cloud.langfuse.com"

    def __init__(self, public_key: str, secret_key: str, host: str | None = None) -> None:
        """Initialize the client.

        Args:
            public_key: Langfuse public API key.
            secret_key: Langfuse secret API key.
            host: Langfuse host URL (defaults to cloud.langfuse.com).
        """
        self.public_key = public_key
        self.secret_key = secret_key
        self.host = (host or self.DEFAULT_HOST).rstrip("/")

        # Create Basic Auth header
        credentials = f"{public_key}:{secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self._auth_header = f"Basic {encoded}"

        self._client = httpx.Client(
            timeout=30.0,
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json",
            },
        )

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API."""
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed. Check your API keys.")

        if response.status_code == 404:
            try:
                detail = response.json().get("message", "Resource not found")
            except Exception:
                detail = "Resource not found"
            raise NotFoundError(detail)

        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded. Please try again later.")

        if response.status_code >= 400:
            try:
                detail = response.json().get("message", f"HTTP {response.status_code}")
            except Exception:
                detail = f"HTTP {response.status_code}"
            raise LangfuseError(detail)

    def _parse_timestamp(self, timestamp: str | None) -> str | None:
        """Parse timestamp to ISO 8601 format."""
        if not timestamp:
            return None

        # If already in ISO format, return as-is
        if "T" in timestamp:
            return timestamp

        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp, fmt)
                return dt.isoformat() + "Z"
            except ValueError:
                continue

        # Return as-is if no format matches
        return timestamp

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request."""
        response = self._client.get(f"{self.host}{path}", params=params)
        self._handle_error_response(response)
        return response.json()

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a POST request."""
        response = self._client.post(f"{self.host}{path}", json=json)
        self._handle_error_response(response)
        return response.json()

    # Traces API
    def list_traces(
        self,
        limit: int = 50,
        page: int = 1,
        user_id: str | None = None,
        name: str | None = None,
        session_id: str | None = None,
        tags: list[str] | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
    ) -> LangfuseTracesResponse:
        """List traces with pagination and filters.

        Args:
            limit: Maximum number of results per page.
            page: Page number (1-indexed).
            user_id: Filter by user ID.
            name: Filter by trace name.
            session_id: Filter by session ID.
            tags: Filter by tags.
            from_timestamp: Filter by start timestamp.
            to_timestamp: Filter by end timestamp.

        Returns:
            LangfuseTracesResponse with traces data and pagination meta.
        """
        params: dict[str, Any] = {
            "limit": limit,
            "page": page,
        }

        if user_id:
            params["userId"] = user_id
        if name:
            params["name"] = name
        if session_id:
            params["sessionId"] = session_id
        if tags:
            params["tags"] = tags
        if from_timestamp:
            params["fromTimestamp"] = self._parse_timestamp(from_timestamp)
        if to_timestamp:
            params["toTimestamp"] = self._parse_timestamp(to_timestamp)

        data = self._get("/api/public/traces", params)
        return LangfuseTracesResponse(**data)

    def get_trace(self, trace_id: str) -> LangfuseTrace:
        """Get a specific trace with its observations.

        Args:
            trace_id: The trace ID to fetch.

        Returns:
            LangfuseTrace with full trace data including observations.
        """
        data = self._get(f"/api/public/traces/{trace_id}")
        return LangfuseTrace(**data)

    # Sessions API
    def list_sessions(
        self,
        limit: int = 50,
        page: int = 1,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
    ) -> LangfuseSessionsResponse:
        """List sessions with pagination.

        Args:
            limit: Maximum number of results per page.
            page: Page number (1-indexed).
            from_timestamp: Filter by start timestamp.
            to_timestamp: Filter by end timestamp.

        Returns:
            LangfuseSessionsResponse with sessions data and pagination meta.
        """
        params: dict[str, Any] = {
            "limit": limit,
            "page": page,
        }

        if from_timestamp:
            params["fromTimestamp"] = self._parse_timestamp(from_timestamp)
        if to_timestamp:
            params["toTimestamp"] = self._parse_timestamp(to_timestamp)

        data = self._get("/api/public/sessions", params)
        return LangfuseSessionsResponse(**data)

    def get_session(self, session_id: str) -> LangfuseSession:
        """Get a specific session.

        Args:
            session_id: The session ID to fetch.

        Returns:
            LangfuseSession with session data.
        """
        data = self._get(f"/api/public/sessions/{session_id}")
        return LangfuseSession(**data)

    # Observations API
    def list_observations(
        self,
        limit: int = 50,
        page: int = 1,
        name: str | None = None,
        user_id: str | None = None,
        trace_id: str | None = None,
        obs_type: str | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
    ) -> LangfuseObservationsResponse:
        """List observations with pagination and filters.

        Args:
            limit: Maximum number of results per page.
            page: Page number (1-indexed).
            name: Filter by observation name.
            user_id: Filter by user ID.
            trace_id: Filter by trace ID.
            obs_type: Filter by type (GENERATION, SPAN, EVENT).
            from_timestamp: Filter by start timestamp.
            to_timestamp: Filter by end timestamp.

        Returns:
            LangfuseObservationsResponse with observations data.
        """
        params: dict[str, Any] = {
            "limit": limit,
            "page": page,
        }

        if name:
            params["name"] = name
        if user_id:
            params["userId"] = user_id
        if trace_id:
            params["traceId"] = trace_id
        if obs_type:
            params["type"] = obs_type
        if from_timestamp:
            params["fromTimestamp"] = self._parse_timestamp(from_timestamp)
        if to_timestamp:
            params["toTimestamp"] = self._parse_timestamp(to_timestamp)

        data = self._get("/api/public/observations", params)
        return LangfuseObservationsResponse(**data)

    def get_observation(self, observation_id: str) -> LangfuseObservation:
        """Get a specific observation.

        Args:
            observation_id: The observation ID to fetch.

        Returns:
            LangfuseObservation with observation data.
        """
        data = self._get(f"/api/public/observations/{observation_id}")
        return LangfuseObservation(**data)

    # Scores API
    def list_scores(
        self,
        limit: int = 50,
        page: int = 1,
        name: str | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
    ) -> LangfuseScoresResponse:
        """List scores with pagination and filters.

        Args:
            limit: Maximum number of results per page.
            page: Page number (1-indexed).
            name: Filter by score name.
            from_timestamp: Filter by start timestamp.
            to_timestamp: Filter by end timestamp.

        Returns:
            LangfuseScoresResponse with scores data.
        """
        params: dict[str, Any] = {
            "limit": limit,
            "page": page,
        }

        if name:
            params["name"] = name
        if from_timestamp:
            params["fromTimestamp"] = self._parse_timestamp(from_timestamp)
        if to_timestamp:
            params["toTimestamp"] = self._parse_timestamp(to_timestamp)

        data = self._get("/api/public/scores", params)
        return LangfuseScoresResponse(**data)

    def get_score(self, score_id: str) -> LangfuseScore:
        """Get a specific score.

        Args:
            score_id: The score ID to fetch.

        Returns:
            LangfuseScore with score data.
        """
        data = self._get(f"/api/public/scores/{score_id}")
        return LangfuseScore(**data)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> LangfuseClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()

