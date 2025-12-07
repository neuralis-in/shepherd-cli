"""Tests for AIOBS client."""

import pytest

from shepherd.providers.aiobs import (
    AIOBSClient,
    AIOBSError,
    AuthenticationError,
    SessionNotFoundError,
)


class TestAIOBSClient:
    """Tests for AIOBS client."""

    def test_client_initialization(self):
        client = AIOBSClient(
            api_key="test_key",
            endpoint="https://api.example.com",
        )
        assert client.api_key == "test_key"
        assert client.endpoint == "https://api.example.com"
        client.close()

    def test_client_strips_trailing_slash(self):
        client = AIOBSClient(
            api_key="test_key",
            endpoint="https://api.example.com/",
        )
        assert client.endpoint == "https://api.example.com"
        client.close()

    def test_client_context_manager(self):
        with AIOBSClient(api_key="test_key", endpoint="https://api.example.com") as client:
            assert client.api_key == "test_key"

    def test_list_sessions_success(self, httpx_mock, sample_sessions_response):
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/v1/sessions",
            json=sample_sessions_response,
        )

        with AIOBSClient(api_key="test_key", endpoint="https://api.example.com") as client:
            response = client.list_sessions()

        assert len(response.sessions) == 1
        assert response.sessions[0].id == "550e8400-e29b-41d4-a716-446655440000"

    def test_list_sessions_empty(self, httpx_mock, empty_sessions_response):
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/v1/sessions",
            json=empty_sessions_response,
        )

        with AIOBSClient(api_key="test_key", endpoint="https://api.example.com") as client:
            response = client.list_sessions()

        assert len(response.sessions) == 0

    def test_list_sessions_invalid_api_key(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/v1/sessions",
            status_code=401,
            json={"detail": "Invalid API key"},
        )

        with AIOBSClient(api_key="bad_key", endpoint="https://api.example.com") as client:
            with pytest.raises(AuthenticationError) as exc_info:
                client.list_sessions()

        assert "Invalid API key" in str(exc_info.value)

    def test_list_sessions_revoked_api_key(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/v1/sessions",
            status_code=401,
            json={"detail": "API key has been revoked"},
        )

        with AIOBSClient(api_key="revoked_key", endpoint="https://api.example.com") as client:
            with pytest.raises(AuthenticationError) as exc_info:
                client.list_sessions()

        assert "revoked" in str(exc_info.value)

    def test_get_session_success(self, httpx_mock, sample_sessions_response):
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        httpx_mock.add_response(
            method="POST",
            url=f"https://api.example.com/v1/sessions/{session_id}/tree",
            json=sample_sessions_response,
        )

        with AIOBSClient(api_key="test_key", endpoint="https://api.example.com") as client:
            response = client.get_session(session_id)

        assert len(response.sessions) == 1
        assert response.sessions[0].id == session_id

    def test_get_session_not_found(self, httpx_mock):
        session_id = "nonexistent-session-id"
        httpx_mock.add_response(
            method="POST",
            url=f"https://api.example.com/v1/sessions/{session_id}/tree",
            status_code=404,
            json={"detail": f"Session not found: {session_id}"},
        )

        with AIOBSClient(api_key="test_key", endpoint="https://api.example.com") as client:
            with pytest.raises(SessionNotFoundError) as exc_info:
                client.get_session(session_id)

        assert "Session not found" in str(exc_info.value)

    def test_generic_error(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/v1/sessions",
            status_code=500,
            json={"detail": "Internal server error"},
        )

        with AIOBSClient(api_key="test_key", endpoint="https://api.example.com") as client:
            with pytest.raises(AIOBSError) as exc_info:
                client.list_sessions()

        assert "Internal server error" in str(exc_info.value)

    def test_request_includes_api_key(self, httpx_mock, sample_sessions_response):
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/v1/sessions",
            json=sample_sessions_response,
        )

        with AIOBSClient(api_key="my_secret_key", endpoint="https://api.example.com") as client:
            client.list_sessions()

        # Verify the request was made with the API key in the body
        request = httpx_mock.get_request()
        assert request is not None
        import json

        body = json.loads(request.content)
        assert body["api_key"] == "my_secret_key"
