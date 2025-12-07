"""AIOBS provider client."""

from __future__ import annotations

import httpx

from shepherd.models import SessionsResponse


class AIOBSError(Exception):
    """Base exception for AIOBS errors."""

    pass


class AuthenticationError(AIOBSError):
    """Authentication failed."""

    pass


class SessionNotFoundError(AIOBSError):
    """Session not found."""

    pass


class AIOBSClient:
    """Client for AIOBS API."""

    def __init__(self, api_key: str, endpoint: str) -> None:
        """Initialize the client.

        Args:
            api_key: AIOBS API key.
            endpoint: AIOBS API endpoint URL.
        """
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API."""
        if response.status_code == 401:
            try:
                detail = response.json().get("detail", "Authentication failed")
            except Exception:
                detail = "Authentication failed"
            raise AuthenticationError(detail)

        if response.status_code == 404:
            try:
                detail = response.json().get("detail", "Not found")
            except Exception:
                detail = "Not found"
            raise SessionNotFoundError(detail)

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", f"HTTP {response.status_code}")
            except Exception:
                detail = f"HTTP {response.status_code}"
            raise AIOBSError(detail)

    def list_sessions(self) -> SessionsResponse:
        """List all sessions.

        Returns:
            SessionsResponse with all sessions and their events.
        """
        response = self._client.post(
            f"{self.endpoint}/v1/sessions",
            json={"api_key": self.api_key},
        )

        self._handle_error_response(response)
        return SessionsResponse(**response.json())

    def get_session(self, session_id: str) -> SessionsResponse:
        """Get a specific session with its trace tree.

        Args:
            session_id: The session ID to fetch.

        Returns:
            SessionsResponse with the session data.
        """
        response = self._client.post(
            f"{self.endpoint}/v1/sessions/{session_id}/tree",
            json={"api_key": self.api_key},
        )

        self._handle_error_response(response)
        return SessionsResponse(**response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> AIOBSClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()
