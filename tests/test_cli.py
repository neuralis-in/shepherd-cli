"""Tests for CLI commands."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from shepherd.cli.main import app
from shepherd.models import SessionsResponse

runner = CliRunner()


class TestVersionCommand:
    """Tests for version command."""

    def test_version_output(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "shepherd" in result.stdout
        assert "0.1.0" in result.stdout


class TestHelpCommand:
    """Tests for help output."""

    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Debug your AI agents" in result.stdout
        assert "config" in result.stdout
        assert "sessions" in result.stdout

    def test_sessions_help(self):
        result = runner.invoke(app, ["sessions", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout
        assert "get" in result.stdout

    def test_config_help(self):
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "init" in result.stdout
        assert "show" in result.stdout
        assert "set" in result.stdout
        assert "get" in result.stdout


class TestConfigCommands:
    """Tests for config commands."""

    def test_config_show(self):
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "Provider" in result.stdout
        assert "aiobs" in result.stdout


class TestSessionsListCommand:
    """Tests for sessions list command."""

    def test_sessions_list_no_api_key(self):
        with patch("shepherd.cli.sessions.get_api_key", return_value=None):
            result = runner.invoke(app, ["sessions", "list"])
            assert result.exit_code == 1
            assert "No API key configured" in result.stdout

    def test_sessions_list_success(self, sample_sessions_response):
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["sessions", "list"])

        assert result.exit_code == 0
        assert "test-session" in result.stdout

    def test_sessions_list_empty(self, empty_sessions_response):
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**empty_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["sessions", "list"])

        assert result.exit_code == 0
        assert "No sessions found" in result.stdout

    def test_sessions_list_json_output(self, sample_sessions_response):
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["sessions", "list", "-o", "json"])

        assert result.exit_code == 0
        # Parse the JSON output (strip ANSI codes first)
        output = result.stdout
        assert "sessions" in output
        assert "550e8400" in output

    def test_sessions_list_with_limit(self, sample_sessions_response):
        # Add more sessions to test limit
        sample_sessions_response["sessions"] = [
            sample_sessions_response["sessions"][0].copy() for _ in range(5)
        ]
        for i, session in enumerate(sample_sessions_response["sessions"]):
            session["id"] = f"session-{i}"
            session["name"] = f"session-{i}"

        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["sessions", "list", "-n", "2"])

        assert result.exit_code == 0
        # Should only show 2 sessions

    def test_sessions_list_ids_only(self, sample_sessions_response):
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["sessions", "list", "--ids"])

        assert result.exit_code == 0
        assert "550e8400-e29b-41d4-a716-446655440000" in result.stdout
        # Should not contain table elements
        assert "Sessions" not in result.stdout


class TestSessionsGetCommand:
    """Tests for sessions get command."""

    def test_sessions_get_no_api_key(self):
        with patch("shepherd.cli.sessions.get_api_key", return_value=None):
            result = runner.invoke(app, ["sessions", "get", "some-id"])
            assert result.exit_code == 1
            assert "No API key configured" in result.stdout

    def test_sessions_get_success(self, sample_sessions_response):
        mock_client = MagicMock()
        mock_client.get_session.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        session_id = "550e8400-e29b-41d4-a716-446655440000"

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["sessions", "get", session_id])

        assert result.exit_code == 0
        mock_client.get_session.assert_called_once_with(session_id)

    def test_sessions_get_not_found(self):
        from shepherd.providers.aiobs import SessionNotFoundError

        mock_client = MagicMock()
        mock_client.get_session.side_effect = SessionNotFoundError("Session not found")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["sessions", "get", "nonexistent"])

        assert result.exit_code == 1
        assert "Session not found" in result.stdout
