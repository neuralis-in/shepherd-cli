"""Tests for CLI commands."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from shepherd.cli.main import app
from shepherd.models import SessionsResponse
from shepherd.models.langfuse import LangfuseSessionsResponse, LangfuseTrace, LangfuseTracesResponse

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
        assert "traces" in result.stdout
        assert "langfuse" in result.stdout
        assert "aiobs" in result.stdout

    def test_sessions_help(self):
        result = runner.invoke(app, ["sessions", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout
        assert "get" in result.stdout
        assert "search" in result.stdout
        assert "diff" in result.stdout

    def test_traces_help(self):
        result = runner.invoke(app, ["traces", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout
        assert "get" in result.stdout
        assert "search" in result.stdout

    def test_config_help(self):
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "init" in result.stdout
        assert "show" in result.stdout
        assert "set" in result.stdout
        assert "get" in result.stdout

    def test_langfuse_help(self):
        result = runner.invoke(app, ["langfuse", "--help"])
        assert result.exit_code == 0
        assert "traces" in result.stdout
        assert "sessions" in result.stdout

    def test_aiobs_help(self):
        result = runner.invoke(app, ["aiobs", "--help"])
        assert result.exit_code == 0
        assert "sessions" in result.stdout


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
        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value=None):
                result = runner.invoke(app, ["sessions", "list"])
                assert result.exit_code == 1
                assert "No API key configured" in result.stdout

    def test_sessions_list_success(self, sample_sessions_response):
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
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

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
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

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
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

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
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

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
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
        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
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

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
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

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "get", "nonexistent"])

        assert result.exit_code == 1
        assert "Session not found" in result.stdout


class TestSessionsSearchCommand:
    """Tests for sessions search command."""

    def test_sessions_search_no_api_key(self):
        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value=None):
                result = runner.invoke(app, ["sessions", "search"])
                assert result.exit_code == 1
                assert "No API key configured" in result.stdout

    def test_sessions_search_no_filters(self, search_sessions_response):
        """Search with no filters returns all sessions."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search"])

        assert result.exit_code == 0
        # Check for truncated names (table truncates long names)
        assert "prod-ses" in result.stdout
        assert "dev-sess" in result.stdout

    def test_sessions_search_by_query(self, search_sessions_response):
        """Search by text query matches session name."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "production"])

        assert result.exit_code == 0
        assert "prod-ses" in result.stdout
        # dev-agent should be filtered out
        assert "dev-sess" not in result.stdout

    def test_sessions_search_by_label(self, search_sessions_response):
        """Search by label filters correctly."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "-l", "env=production"])

        assert result.exit_code == 0
        assert "prod-ses" in result.stdout
        assert "dev-sess" not in result.stdout

    def test_sessions_search_by_multiple_labels(self, search_sessions_response):
        """Search by multiple labels."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "search", "-l", "env=production", "-l", "user=alice"]
                    )

        assert result.exit_code == 0
        assert "prod-ses" in result.stdout

    def test_sessions_search_by_provider(self, search_sessions_response):
        """Search by provider filters correctly."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "-p", "anthropic"])

        assert result.exit_code == 0
        assert "prod-ses" in result.stdout
        assert "dev-sess" not in result.stdout

    def test_sessions_search_by_model(self, search_sessions_response):
        """Search by model filters correctly."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "-m", "claude-3"])

        assert result.exit_code == 0
        assert "prod-ses" in result.stdout

    def test_sessions_search_by_function(self, search_sessions_response):
        """Search by function name filters correctly."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "-f", "process_data"])

        assert result.exit_code == 0
        assert "prod-ses" in result.stdout

    def test_sessions_search_has_errors(self, search_sessions_response):
        """Search for sessions with errors using explicit aiobs command."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["aiobs", "sessions", "search", "--has-errors"])

        assert result.exit_code == 0
        # Table truncates names, check for partial match
        assert "dev" in result.stdout
        assert "production" not in result.stdout

    def test_sessions_search_evals_failed(self, search_sessions_with_failed_evals):
        """Search for sessions with failed evaluations using explicit aiobs command."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(
            **search_sessions_with_failed_evals
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["aiobs", "sessions", "search", "--evals-failed"])

        assert result.exit_code == 0
        assert "prod" in result.stdout

    def test_sessions_search_by_date_after(self, search_sessions_response):
        """Search for sessions after a date."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    # dev-session has earlier date (1733490000 = 2024-12-06)
                    # prod-session has later date (1733580000 = 2024-12-07)
                    result = runner.invoke(app, ["sessions", "search", "--after", "2024-12-07"])

        assert result.exit_code == 0
        assert "prod-ses" in result.stdout
        assert "dev-sess" not in result.stdout

    def test_sessions_search_combined_filters(self, search_sessions_response):
        """Search with combined filters."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "search", "-p", "anthropic", "-l", "env=production"]
                    )

        assert result.exit_code == 0
        assert "prod-ses" in result.stdout

    def test_sessions_search_json_output(self, search_sessions_response):
        """Search with JSON output format."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "-o", "json"])

        assert result.exit_code == 0
        assert "sessions" in result.stdout

    def test_sessions_search_ids_only(self, search_sessions_response):
        """Search with IDs only output."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "--ids"])

        assert result.exit_code == 0
        assert "prod-session-001" in result.stdout
        assert "dev-session-002" in result.stdout
        # Should not contain table elements
        assert "Search Results" not in result.stdout

    def test_sessions_search_with_limit(self, search_sessions_response):
        """Search with limit option."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "-n", "1"])

        assert result.exit_code == 0

    def test_sessions_search_no_results(self, search_sessions_response):
        """Search returns no results."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "nonexistent-query"])

        assert result.exit_code == 0
        assert "No sessions match" in result.stdout

    def test_sessions_search_invalid_label_format(self):
        """Search with invalid label format shows error."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "-l", "invalid"])

        assert result.exit_code != 0
        assert "Invalid label format" in result.output

    def test_sessions_search_invalid_date_format(self):
        """Search with invalid date format shows error."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search", "--after", "not-a-date"])

        assert result.exit_code != 0
        assert "Invalid date format" in result.output


class TestSessionsDiffCommand:
    """Tests for sessions diff command."""

    def test_sessions_diff_help(self):
        """Diff help shows correct information."""
        result = runner.invoke(app, ["sessions", "diff", "--help"])
        assert result.exit_code == 0
        assert "Compare two sessions" in result.stdout
        assert "SESSION_ID1" in result.stdout
        assert "SESSION_ID2" in result.stdout

    def test_sessions_diff_no_api_key(self):
        """Diff without API key shows error."""
        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value=None):
                result = runner.invoke(app, ["sessions", "diff", "session1", "session2"])
                assert result.exit_code == 1
                assert "No API key configured" in result.stdout

    def test_sessions_diff_success(self, diff_session_response_1, diff_session_response_2):
        """Diff with valid sessions shows comparison."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "diff", "session-diff-001", "session-diff-002"]
                    )

        assert result.exit_code == 0
        assert "Session Diff" in result.stdout
        assert "baseline-agent" in result.stdout
        assert "updated-agent" in result.stdout
        assert "LLM Calls Summary" in result.stdout

    def test_sessions_diff_json_output(self, diff_session_response_1, diff_session_response_2):
        """Diff with JSON output returns valid JSON."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app,
                        ["sessions", "diff", "session-diff-001", "session-diff-002", "-o", "json"],
                    )

        assert result.exit_code == 0
        # Check JSON structure
        assert '"metadata"' in result.stdout
        assert '"llm_calls"' in result.stdout
        assert '"functions"' in result.stdout
        assert '"delta"' in result.stdout

    def test_sessions_diff_session_not_found(self, diff_session_response_1):
        """Diff with non-existent session shows error."""
        from shepherd.providers.aiobs import SessionNotFoundError

        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            raise SessionNotFoundError("Session not found: nonexistent")

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "diff", "session-diff-001", "nonexistent"]
                    )

        assert result.exit_code == 1
        assert "Session not found" in result.stdout

    def test_sessions_diff_shows_token_comparison(
        self, diff_session_response_1, diff_session_response_2
    ):
        """Diff shows token usage comparison."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "diff", "session-diff-001", "session-diff-002"]
                    )

        assert result.exit_code == 0
        assert "Total Tokens" in result.stdout
        assert "Input Tokens" in result.stdout
        assert "Output Tokens" in result.stdout

    def test_sessions_diff_shows_provider_distribution(
        self, diff_session_response_1, diff_session_response_2
    ):
        """Diff shows provider distribution comparison."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "diff", "session-diff-001", "session-diff-002"]
                    )

        assert result.exit_code == 0
        assert "Provider Distribution" in result.stdout
        assert "openai" in result.stdout
        assert "anthropic" in result.stdout

    def test_sessions_diff_shows_function_differences(
        self, diff_session_response_1, diff_session_response_2
    ):
        """Diff shows function event comparison."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "diff", "session-diff-001", "session-diff-002"]
                    )

        assert result.exit_code == 0
        assert "Function Events Summary" in result.stdout
        # Check for function-only-in comparisons
        assert "process" in result.stdout
        assert "new_process" in result.stdout

    def test_sessions_diff_shows_system_prompts(
        self, diff_session_response_1, diff_session_response_2
    ):
        """Diff shows system prompt comparison."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "diff", "session-diff-001", "session-diff-002"]
                    )

        assert result.exit_code == 0
        assert "System Prompts Comparison" in result.stdout
        # Check system prompt content is shown
        assert "helpful assistant" in result.stdout or "code review" in result.stdout

    def test_sessions_diff_shows_request_params(
        self, diff_session_response_1, diff_session_response_2
    ):
        """Diff shows request parameter comparison."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "diff", "session-diff-001", "session-diff-002"]
                    )

        assert result.exit_code == 0
        assert "Request Parameters Summary" in result.stdout
        assert "Temperature" in result.stdout

    def test_sessions_diff_shows_response_summary(
        self, diff_session_response_1, diff_session_response_2
    ):
        """Diff shows response summary comparison."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "diff", "session-diff-001", "session-diff-002"]
                    )

        assert result.exit_code == 0
        assert "Response Summary" in result.stdout
        assert "Response Length" in result.stdout

    def test_sessions_diff_shows_tools_comparison(
        self, diff_session_response_1, diff_session_response_2
    ):
        """Diff shows tools used comparison."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["sessions", "diff", "session-diff-001", "session-diff-002"]
                    )

        assert result.exit_code == 0
        assert "Tools Used" in result.stdout

    def test_sessions_diff_json_includes_new_fields(
        self, diff_session_response_1, diff_session_response_2
    ):
        """Diff JSON output includes system prompts, requests, and responses."""
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.main._get_provider", return_value="aiobs"):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(
                        app,
                        ["sessions", "diff", "session-diff-001", "session-diff-002", "-o", "json"],
                    )

        assert result.exit_code == 0
        assert '"system_prompts"' in result.stdout
        assert '"request_params"' in result.stdout
        assert '"responses"' in result.stdout


# ============================================================================
# Provider-Aware Routing Tests
# ============================================================================


class TestProviderAwareRouting:
    """Tests for provider-aware command routing."""

    def test_traces_list_with_langfuse_provider(self, sample_langfuse_traces_response):
        """Traces list works with langfuse provider."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **sample_langfuse_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
                with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                    with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                        result = runner.invoke(app, ["traces", "list"])

        assert result.exit_code == 0
        mock_client.list_traces.assert_called_once()

    def test_traces_list_with_aiobs_provider_shows_error(self):
        """Traces list with aiobs provider shows unsupported error."""
        mock_config = MagicMock()
        mock_config.default_provider = "aiobs"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            result = runner.invoke(app, ["traces", "list"])

        assert result.exit_code == 1
        assert "does not support traces" in result.stdout

    def test_sessions_list_with_aiobs_provider(self, sample_sessions_response):
        """Sessions list routes to aiobs when provider is aiobs."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        mock_config = MagicMock()
        mock_config.default_provider = "aiobs"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "list"])

        assert result.exit_code == 0
        mock_client.list_sessions.assert_called_once()

    def test_sessions_list_with_langfuse_provider(self, sample_langfuse_sessions_response):
        """Sessions list routes to langfuse when provider is langfuse."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **sample_langfuse_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
                with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                    with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                        result = runner.invoke(app, ["sessions", "list"])

        assert result.exit_code == 0
        mock_client.list_sessions.assert_called_once()

    def test_sessions_search_with_aiobs_provider(self, search_sessions_response):
        """Sessions search works with aiobs provider."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        mock_config = MagicMock()
        mock_config.default_provider = "aiobs"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = runner.invoke(app, ["sessions", "search"])

        assert result.exit_code == 0

    def test_sessions_search_with_langfuse_provider(self, langfuse_search_sessions_response):
        """Sessions search routes to langfuse when provider is langfuse."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
                with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                    with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                        result = runner.invoke(app, ["sessions", "search"])

        assert result.exit_code == 0
        assert "Search Results" in result.stdout

    def test_sessions_diff_with_langfuse_provider_shows_error(self):
        """Sessions diff with langfuse provider shows unsupported error."""
        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            result = runner.invoke(app, ["sessions", "diff", "id1", "id2"])

        assert result.exit_code == 1
        assert "does not support session diff" in result.stdout


class TestExplicitProviderCommands:
    """Tests for explicit provider commands that bypass routing."""

    def test_langfuse_traces_list(self, sample_langfuse_traces_response):
        """Explicit langfuse traces list works."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **sample_langfuse_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "traces", "list"])

        assert result.exit_code == 0
        mock_client.list_traces.assert_called_once()

    def test_langfuse_traces_get(self, sample_langfuse_trace_detail):
        """Explicit langfuse traces get works."""
        mock_client = MagicMock()
        mock_client.get_trace.return_value = LangfuseTrace(**sample_langfuse_trace_detail)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "traces", "get", "trace-001"])

        assert result.exit_code == 0
        mock_client.get_trace.assert_called_once_with("trace-001")

    def test_langfuse_sessions_list(self, sample_langfuse_sessions_response):
        """Explicit langfuse sessions list works."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **sample_langfuse_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "sessions", "list"])

        assert result.exit_code == 0
        mock_client.list_sessions.assert_called_once()

    def test_aiobs_sessions_list(self, sample_sessions_response):
        """Explicit aiobs sessions list works."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["aiobs", "sessions", "list"])

        assert result.exit_code == 0
        mock_client.list_sessions.assert_called_once()

    def test_aiobs_sessions_search(self, search_sessions_response):
        """Explicit aiobs sessions search works."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = runner.invoke(app, ["aiobs", "sessions", "search"])

        assert result.exit_code == 0


class TestLangfuseTracesCommand:
    """Tests for langfuse traces commands."""

    def test_traces_list_no_credentials(self):
        """Traces list without credentials shows error."""
        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value=None):
            result = runner.invoke(app, ["langfuse", "traces", "list"])

        assert result.exit_code == 1
        assert (
            "No Langfuse credentials" in result.stdout or "not configured" in result.stdout.lower()
        )

    def test_traces_list_empty(self, empty_langfuse_traces_response):
        """Traces list with no results shows message."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **empty_langfuse_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "traces", "list"])

        assert result.exit_code == 0
        assert "No traces found" in result.stdout

    def test_traces_list_with_limit(self, sample_langfuse_traces_response):
        """Traces list respects limit parameter."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **sample_langfuse_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "traces", "list", "-n", "10"])

        assert result.exit_code == 0
        mock_client.list_traces.assert_called_once()
        call_kwargs = mock_client.list_traces.call_args[1]
        assert call_kwargs["limit"] == 10

    def test_traces_list_ids_only(self, sample_langfuse_traces_response):
        """Traces list with --ids only shows IDs."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **sample_langfuse_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "traces", "list", "--ids"])

        assert result.exit_code == 0
        assert "trace-001" in result.stdout
        # Should not contain table headers
        assert "Traces" not in result.stdout


class TestLangfuseSessionsCommand:
    """Tests for langfuse sessions commands."""

    def test_sessions_list_empty(self, empty_langfuse_sessions_response):
        """Sessions list with no results shows message."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **empty_langfuse_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "sessions", "list"])

        assert result.exit_code == 0
        assert "No sessions found" in result.stdout


# ============================================================================
# Langfuse Sessions Search Tests
# ============================================================================


class TestLangfuseSessionsSearchCommand:
    """Tests for langfuse sessions search command."""

    def test_sessions_search_no_filters(self, langfuse_search_sessions_response):
        """Search sessions without filters returns all."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "sessions", "search"])

        assert result.exit_code == 0
        assert "Search Results" in result.stdout
        assert "3 sessions" in result.stdout

    def test_sessions_search_by_query(self, langfuse_search_sessions_response):
        """Search sessions by text query."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "sessions", "search", "prod"])

        assert result.exit_code == 0
        # Should match "session-prod-001" (displayed truncated in table)
        assert "1 sessions" in result.stdout
        assert "session-pr" in result.stdout  # Truncated ID

    def test_sessions_search_by_user_id(self, langfuse_search_sessions_response):
        """Search sessions by user ID."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["langfuse", "sessions", "search", "--user-id", "alice"]
                    )

        assert result.exit_code == 0
        # Should only show session with alice
        assert "1 sessions" in result.stdout

    def test_sessions_search_by_min_traces(self, langfuse_search_sessions_response):
        """Search sessions with minimum traces filter."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["langfuse", "sessions", "search", "--min-traces", "5"]
                    )

        assert result.exit_code == 0
        # Only session with 10 traces should match
        assert "1 sessions" in result.stdout

    def test_sessions_search_by_cost_range(self, langfuse_search_sessions_response):
        """Search sessions with cost filters."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["langfuse", "sessions", "search", "--min-cost", "0.01"]
                    )

        assert result.exit_code == 0
        # Only the prod session with cost 0.015 should match
        assert "1 sessions" in result.stdout

    def test_sessions_search_ids_only(self, langfuse_search_sessions_response):
        """Search sessions with --ids flag shows only IDs."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "sessions", "search", "--ids"])

        assert result.exit_code == 0
        assert "session-prod-001" in result.stdout
        assert "session-dev-002" in result.stdout
        # Should not have table formatting
        assert "Search Results" not in result.stdout

    def test_sessions_search_json_output(self, langfuse_search_sessions_response):
        """Search sessions with JSON output."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "sessions", "search", "-o", "json"])

        assert result.exit_code == 0
        assert '"sessions"' in result.stdout
        assert '"session-prod-001"' in result.stdout

    def test_sessions_search_no_results(self, langfuse_search_sessions_response):
        """Search sessions with no matching results."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "sessions", "search", "nonexistent"])

        assert result.exit_code == 0
        assert "No sessions match" in result.stdout


# ============================================================================
# Langfuse Traces Search Tests
# ============================================================================


class TestLangfuseTracesSearchCommand:
    """Tests for langfuse traces search command."""

    def test_traces_search_no_filters(self, langfuse_search_traces_response):
        """Search traces without filters returns all."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "traces", "search"])

        assert result.exit_code == 0
        assert "Search Results" in result.stdout
        assert "3 traces" in result.stdout

    def test_traces_search_by_query(self, langfuse_search_traces_response):
        """Search traces by text query."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "traces", "search", "production"])

        assert result.exit_code == 0
        # Should match traces with "production" in name or tags
        # Note: 2 traces match - production-pipeline and heavy-workload (has production tag)
        assert "2 traces" in result.stdout
        assert "productio" in result.stdout  # Truncated in table display

    def test_traces_search_by_user_id(self, langfuse_search_traces_response):
        """Search traces by user ID."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["langfuse", "traces", "search", "--user-id", "bob"]
                    )

        assert result.exit_code == 0
        # API filter applied, so mock will return all but client shows results
        mock_client.list_traces.assert_called_once()
        call_kwargs = mock_client.list_traces.call_args[1]
        assert call_kwargs["user_id"] == "bob"

    def test_traces_search_by_tag(self, langfuse_search_traces_response):
        """Search traces by tag."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["langfuse", "traces", "search", "-t", "production"]
                    )

        assert result.exit_code == 0
        mock_client.list_traces.assert_called_once()
        call_kwargs = mock_client.list_traces.call_args[1]
        assert call_kwargs["tags"] == ["production"]

    def test_traces_search_by_cost_range(self, langfuse_search_traces_response):
        """Search traces with cost filters."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["langfuse", "traces", "search", "--min-cost", "0.01"]
                    )

        assert result.exit_code == 0
        # Only the expensive trace should match
        assert "1 traces" in result.stdout

    def test_traces_search_by_latency_range(self, langfuse_search_traces_response):
        """Search traces with latency filters."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["langfuse", "traces", "search", "--max-latency", "2.0"]
                    )

        assert result.exit_code == 0
        # Only dev trace with latency 1.2s should match
        assert "1 traces" in result.stdout

    def test_traces_search_by_release(self, langfuse_search_traces_response):
        """Search traces by release."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(
                        app, ["langfuse", "traces", "search", "--release", "v2.1.0"]
                    )

        assert result.exit_code == 0
        # Two traces have v2.1.0 release
        assert "2 traces" in result.stdout

    def test_traces_search_ids_only(self, langfuse_search_traces_response):
        """Search traces with --ids flag shows only IDs."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "traces", "search", "--ids"])

        assert result.exit_code == 0
        assert "trace-prod-001" in result.stdout
        assert "trace-dev-002" in result.stdout
        assert "trace-expensive-003" in result.stdout
        # Should not have table formatting
        assert "Search Results" not in result.stdout

    def test_traces_search_json_output(self, langfuse_search_traces_response):
        """Search traces with JSON output."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(app, ["langfuse", "traces", "search", "-o", "json"])

        assert result.exit_code == 0
        assert '"traces"' in result.stdout
        assert '"trace-prod-001"' in result.stdout

    def test_traces_search_combined_filters(self, langfuse_search_traces_response):
        """Search traces with multiple filters."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = runner.invoke(
                        app,
                        [
                            "langfuse",
                            "traces",
                            "search",
                            "--release",
                            "v2.1.0",
                            "--max-latency",
                            "10.0",
                        ],
                    )

        assert result.exit_code == 0
        # Only prod trace matches (v2.1.0 and latency 3.5s < 10)
        assert "1 traces" in result.stdout


# ============================================================================
# Provider-Aware Search Routing Tests
# ============================================================================


class TestProviderAwareSearchRouting:
    """Tests for provider-aware search command routing."""

    def test_sessions_search_routes_to_langfuse(self, langfuse_search_sessions_response):
        """Sessions search routes to langfuse when provider is langfuse."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **langfuse_search_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
                with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                    with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                        result = runner.invoke(app, ["sessions", "search"])

        assert result.exit_code == 0
        assert "Search Results" in result.stdout

    def test_traces_search_routes_to_langfuse(self, langfuse_search_traces_response):
        """Traces search routes to langfuse when provider is langfuse."""
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **langfuse_search_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
                with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                    with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                        result = runner.invoke(app, ["traces", "search"])

        assert result.exit_code == 0
        assert "Search Results" in result.stdout

    def test_traces_search_with_aiobs_provider_shows_error(self):
        """Traces search with aiobs provider shows unsupported error."""
        mock_config = MagicMock()
        mock_config.default_provider = "aiobs"

        with patch("shepherd.cli.main.load_config", return_value=mock_config):
            result = runner.invoke(app, ["traces", "search"])

        assert result.exit_code == 1
        assert "does not support trace search" in result.stdout
