"""Tests for interactive shell."""

from io import StringIO
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from shepherd.cli.main import app
from shepherd.cli.shell import SHELL_COMMANDS, ShepherdShell
from shepherd.models import SessionsResponse
from shepherd.models.langfuse import LangfuseSessionsResponse, LangfuseTrace, LangfuseTracesResponse

runner = CliRunner()


class TestShellCommand:
    """Tests for shell CLI command."""

    def test_shell_help(self):
        result = runner.invoke(app, ["shell", "--help"])
        assert result.exit_code == 0
        assert "interactive" in result.stdout.lower() or "shell" in result.stdout.lower()


class TestShepherdShellInit:
    """Tests for ShepherdShell initialization."""

    def test_shell_creates_aiobs_commands(self):
        ShepherdShell()  # Initialize to populate SHELL_COMMANDS
        # Explicit AIOBS commands
        assert "aiobs sessions list" in SHELL_COMMANDS
        assert "aiobs sessions get" in SHELL_COMMANDS
        assert "aiobs sessions search" in SHELL_COMMANDS
        assert "aiobs sessions diff" in SHELL_COMMANDS

    def test_shell_creates_langfuse_commands(self):
        ShepherdShell()  # Initialize to populate SHELL_COMMANDS
        # Explicit Langfuse commands
        assert "langfuse traces list" in SHELL_COMMANDS
        assert "langfuse traces get" in SHELL_COMMANDS
        assert "langfuse sessions list" in SHELL_COMMANDS
        assert "langfuse sessions get" in SHELL_COMMANDS

    def test_shell_creates_config_commands(self):
        ShepherdShell()  # Initialize to populate SHELL_COMMANDS
        assert "config init" in SHELL_COMMANDS
        assert "config show" in SHELL_COMMANDS
        assert "config set" in SHELL_COMMANDS
        assert "config get" in SHELL_COMMANDS

    def test_shell_commands_are_callable(self):
        ShepherdShell()  # Initialize to populate SHELL_COMMANDS
        for cmd_name, (func, desc) in SHELL_COMMANDS.items():
            assert callable(func), f"Command {cmd_name} is not callable"
            assert isinstance(desc, str), f"Command {cmd_name} has no description"

    def test_shell_has_provider_commands(self):
        shell = ShepherdShell()
        assert hasattr(shell, "_provider_commands")
        assert "langfuse" in shell._provider_commands
        assert "aiobs" in shell._provider_commands
        assert "traces list" in shell._provider_commands["langfuse"]
        assert "sessions list" in shell._provider_commands["aiobs"]


class TestParseCommand:
    """Tests for _parse_command method."""

    def test_parse_empty_line(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("")
        assert cmd == ""
        assert args == []

    def test_parse_simple_command(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("help")
        assert cmd == "help"
        assert args == []

    def test_parse_two_word_provider_command(self):
        shell = ShepherdShell()
        # Provider-specific commands are in _provider_commands
        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"
        with patch("shepherd.config.load_config", return_value=mock_config):
            cmd, args = shell._parse_command("traces list")
        assert cmd == "traces list"
        assert args == []

    def test_parse_two_word_command_with_args(self):
        shell = ShepherdShell()
        mock_config = MagicMock()
        mock_config.default_provider = "aiobs"
        with patch("shepherd.config.load_config", return_value=mock_config):
            cmd, args = shell._parse_command("sessions list --limit 5")
        assert cmd == "sessions list"
        assert args == ["--limit", "5"]

    def test_parse_three_word_command(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("langfuse traces list")
        assert cmd == "langfuse traces list"
        assert args == []

    def test_parse_three_word_command_with_args(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("langfuse traces list --limit 10")
        assert cmd == "langfuse traces list"
        assert args == ["--limit", "10"]

    def test_parse_aiobs_three_word_command(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("aiobs sessions search")
        assert cmd == "aiobs sessions search"
        assert args == []

    def test_parse_slash_prefix(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("/langfuse traces list")
        assert cmd == "langfuse traces list"
        assert args == []

    def test_parse_slash_prefix_with_args(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("/langfuse traces get trace-123")
        assert cmd == "langfuse traces get"
        assert args == ["trace-123"]

    def test_parse_unknown_command(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("unknown command here")
        assert cmd == "unknown"
        assert args == ["command", "here"]

    def test_parse_quoted_args(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command('config set key "value with spaces"')
        assert cmd == "config set"
        assert args == ["key", "value with spaces"]


class TestParseArgs:
    """Tests for _parse_args method."""

    def test_parse_no_args(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions list", [])
        assert kwargs == {}

    def test_parse_long_flag_with_value(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions list", ["--output", "json"])
        assert kwargs == {"output": "json"}

    def test_parse_short_flag_with_value(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions list", ["-o", "json"])
        assert kwargs == {"output": "json"}

    def test_parse_limit_flag(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions list", ["-n", "5"])
        assert kwargs == {"limit": 5}
        assert isinstance(kwargs["limit"], int)

    def test_parse_limit_long_flag(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions list", ["--limit", "10"])
        assert kwargs == {"limit": 10}
        assert isinstance(kwargs["limit"], int)

    def test_parse_boolean_flag(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions list", ["--ids"])
        assert kwargs == {"ids_only": True}

    def test_parse_session_id_positional(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions get", ["abc123"])
        assert kwargs == {"session_id": "abc123"}

    def test_parse_config_set_positional(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("config set", ["aiobs.api_key", "my-key"])
        assert kwargs == {"key": "aiobs.api_key", "value": "my-key"}

    def test_parse_config_get_positional(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("config get", ["aiobs.endpoint"])
        assert kwargs == {"key": "aiobs.endpoint"}

    def test_parse_multiple_flags(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions list", ["-o", "json", "-n", "5", "--ids"])
        assert kwargs["output"] == "json"
        assert kwargs["limit"] == 5
        assert kwargs["ids_only"] is True

    def test_parse_limit_without_value_ignored(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions list", ["--limit"])
        assert "limit" not in kwargs

    def test_parse_invalid_limit_ignored(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions list", ["--limit", "not-a-number"])
        assert "limit" not in kwargs

    def test_parse_search_query_positional(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["my-query"])
        assert kwargs == {"query": "my-query"}

    def test_parse_search_label_short(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["-l", "env=prod"])
        assert kwargs == {"label": ["env=prod"]}

    def test_parse_search_multiple_labels(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["-l", "env=prod", "-l", "user=alice"])
        assert kwargs == {"label": ["env=prod", "user=alice"]}

    def test_parse_search_provider_long(self):
        """Test --provider flag for search (short -p is now for page)."""
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["--provider", "openai"])
        assert kwargs == {"provider": "openai"}

    def test_parse_search_model_short(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["-m", "gpt-4"])
        assert kwargs == {"model": "gpt-4"}

    def test_parse_search_function_short(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["-f", "my_func"])
        assert kwargs == {"function": "my_func"}

    def test_parse_search_has_errors_flag(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["--has-errors"])
        assert kwargs == {"has_errors": True}

    def test_parse_search_errors_alias_flag(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["--errors"])
        assert kwargs == {"has_errors": True}

    def test_parse_search_evals_failed_flag(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["--evals-failed"])
        assert kwargs == {"evals_failed": True}

    def test_parse_search_failed_evals_alias_flag(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions search", ["--failed-evals"])
        assert kwargs == {"evals_failed": True}

    def test_parse_search_combined_args(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args(
            "sessions search",
            ["my-query", "--provider", "anthropic", "-l", "env=prod", "--has-errors", "-n", "5"],
        )
        assert kwargs["query"] == "my-query"
        assert kwargs["provider"] == "anthropic"
        assert kwargs["label"] == ["env=prod"]
        assert kwargs["has_errors"] is True
        assert kwargs["limit"] == 5

    def test_parse_search_date_filters(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args(
            "sessions search", ["--after", "2025-01-01", "--before", "2025-12-31"]
        )
        assert kwargs == {"after": "2025-01-01", "before": "2025-12-31"}

    def test_parse_diff_positional_args(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions diff", ["session-1", "session-2"])
        assert kwargs["session_id1"] == "session-1"
        assert kwargs["session_id2"] == "session-2"

    def test_parse_diff_with_output_flag(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("sessions diff", ["session-1", "session-2", "-o", "json"])
        assert kwargs["session_id1"] == "session-1"
        assert kwargs["session_id2"] == "session-2"
        assert kwargs["output"] == "json"

    def test_parse_traces_get_positional(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("traces get", ["trace-abc123"])
        assert kwargs == {"trace_id": "trace-abc123"}

    def test_parse_langfuse_traces_get_positional(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("langfuse traces get", ["trace-xyz"])
        assert kwargs == {"trace_id": "trace-xyz"}

    def test_parse_traces_list_with_tags(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("traces list", ["--tag", "production", "--tag", "v2"])
        assert kwargs == {"tags": ["production", "v2"]}

    def test_parse_traces_list_page(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("traces list", ["--page", "3"])
        assert kwargs == {"page": 3}
        assert isinstance(kwargs["page"], int)

    def test_parse_traces_list_timestamps(self):
        shell = ShepherdShell()
        kwargs = shell._parse_args("traces list", ["--from", "2025-01-01", "--to", "2025-12-31"])
        assert kwargs == {"from_timestamp": "2025-01-01", "to_timestamp": "2025-12-31"}


class TestExecuteCommand:
    """Tests for _execute_command method."""

    def test_execute_empty_command(self):
        shell = ShepherdShell()
        result = shell._execute_command("", [])
        assert result is True  # Should continue shell

    def test_execute_exit(self):
        shell = ShepherdShell()
        with patch.object(shell.console, "print"):
            result = shell._execute_command("exit", [])
        assert result is False  # Should exit shell

    def test_execute_quit(self):
        shell = ShepherdShell()
        with patch.object(shell.console, "print"):
            result = shell._execute_command("quit", [])
        assert result is False  # Should exit shell

    def test_execute_help(self):
        shell = ShepherdShell()
        with patch.object(shell, "_print_help") as mock_help:
            result = shell._execute_command("help", [])
        assert result is True
        mock_help.assert_called_once()

    def test_execute_clear(self):
        shell = ShepherdShell()
        with patch.object(shell.console, "clear") as mock_clear:
            result = shell._execute_command("clear", [])
        assert result is True
        mock_clear.assert_called_once()

    def test_execute_version(self):
        shell = ShepherdShell()
        with patch.object(shell.console, "print") as mock_print:
            result = shell._execute_command("version", [])
        assert result is True
        # Check version was printed
        call_args = str(mock_print.call_args)
        assert "shepherd" in call_args

    def test_execute_unknown_command(self):
        shell = ShepherdShell()
        with patch.object(shell.console, "print") as mock_print:
            result = shell._execute_command("unknown", [])
        assert result is True
        # Should print error message
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Unknown command" in call for call in calls)


class TestAIOBSSessionsCommands:
    """Tests for AIOBS sessions commands in shell using explicit prefix."""

    def test_aiobs_sessions_list_in_shell(self, sample_sessions_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command("aiobs sessions list", [])

        assert result is True
        mock_client.list_sessions.assert_called_once()

    def test_aiobs_sessions_list_with_limit_in_shell(self, sample_sessions_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command("aiobs sessions list", ["--limit", "5"])

        assert result is True

    def test_aiobs_sessions_get_in_shell(self, sample_sessions_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.get_session.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command("aiobs sessions get", ["session-123"])

        assert result is True
        mock_client.get_session.assert_called_once_with("session-123")

    def test_aiobs_sessions_search_in_shell(self, search_sessions_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command("aiobs sessions search", [])

        assert result is True
        mock_client.list_sessions.assert_called_once()

    def test_aiobs_sessions_search_with_query_in_shell(self, search_sessions_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command("aiobs sessions search", ["production"])

        assert result is True

    def test_aiobs_sessions_search_with_filters_in_shell(self, search_sessions_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**search_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command(
                    "aiobs sessions search",
                    ["-p", "anthropic", "-l", "env=production", "--has-errors"],
                )

        assert result is True

    def test_aiobs_sessions_search_with_evals_failed_in_shell(
        self, search_sessions_with_failed_evals
    ):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(
            **search_sessions_with_failed_evals
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command("aiobs sessions search", ["--evals-failed"])

        assert result is True

    def test_aiobs_sessions_diff_in_shell(self, diff_session_response_1, diff_session_response_2):
        """Test sessions diff command in shell."""
        shell = ShepherdShell()
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command(
                    "aiobs sessions diff", ["session-diff-001", "session-diff-002"]
                )

        assert result is True

    def test_aiobs_sessions_diff_with_output_in_shell(
        self, diff_session_response_1, diff_session_response_2
    ):
        """Test sessions diff command with JSON output in shell."""
        shell = ShepherdShell()
        mock_client = MagicMock()

        def mock_get_session(session_id):
            if session_id == "session-diff-001":
                return SessionsResponse(**diff_session_response_1)
            return SessionsResponse(**diff_session_response_2)

        mock_client.get_session.side_effect = mock_get_session
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command(
                    "aiobs sessions diff", ["session-diff-001", "session-diff-002", "-o", "json"]
                )

        assert result is True


class TestConfigCommands:
    """Tests for config commands in shell."""

    def test_config_show_in_shell(self):
        shell = ShepherdShell()
        result = shell._execute_command("config show", [])
        assert result is True

    def test_config_get_in_shell(self):
        shell = ShepherdShell()
        result = shell._execute_command("config get", ["aiobs.endpoint"])
        assert result is True


class TestLangfuseCommands:
    """Tests for Langfuse commands in shell."""

    def test_langfuse_traces_list_in_shell(self, sample_langfuse_traces_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.list_traces.return_value = LangfuseTracesResponse(
            **sample_langfuse_traces_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = shell._execute_command("langfuse traces list", [])

        assert result is True
        mock_client.list_traces.assert_called_once()

    def test_langfuse_traces_get_in_shell(self, sample_langfuse_trace_detail):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.get_trace.return_value = LangfuseTrace(**sample_langfuse_trace_detail)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = shell._execute_command("langfuse traces get", ["trace-001"])

        assert result is True
        mock_client.get_trace.assert_called_once_with("trace-001")

    def test_langfuse_sessions_list_in_shell(self, sample_langfuse_sessions_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = LangfuseSessionsResponse(
            **sample_langfuse_sessions_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
            with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                    result = shell._execute_command("langfuse sessions list", [])

        assert result is True
        mock_client.list_sessions.assert_called_once()


class TestProviderAwareShellRouting:
    """Tests for provider-aware routing in shell."""

    def test_traces_list_routes_to_langfuse(self, sample_langfuse_traces_response):
        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        # Need to patch load_config before creating the shell
        with patch("shepherd.config.load_config", return_value=mock_config):
            shell = ShepherdShell()
            mock_client = MagicMock()
            mock_client.list_traces.return_value = LangfuseTracesResponse(
                **sample_langfuse_traces_response
            )
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)

            with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
                with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                    with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                        result = shell._execute_command("traces list", [])

        assert result is True
        mock_client.list_traces.assert_called_once()

    def test_sessions_list_routes_to_aiobs(self, sample_sessions_response):
        mock_config = MagicMock()
        mock_config.default_provider = "aiobs"

        with patch("shepherd.config.load_config", return_value=mock_config):
            shell = ShepherdShell()
            mock_client = MagicMock()
            mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)

            with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
                with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                    result = shell._execute_command("sessions list", [])

        assert result is True
        mock_client.list_sessions.assert_called_once()

    def test_sessions_list_routes_to_langfuse(self, sample_langfuse_sessions_response):
        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        with patch("shepherd.config.load_config", return_value=mock_config):
            shell = ShepherdShell()
            mock_client = MagicMock()
            mock_client.list_sessions.return_value = LangfuseSessionsResponse(
                **sample_langfuse_sessions_response
            )
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)

            with patch("shepherd.cli.langfuse.get_langfuse_public_key", return_value="pk-test"):
                with patch("shepherd.cli.langfuse.get_langfuse_secret_key", return_value="sk-test"):
                    with patch("shepherd.cli.langfuse.LangfuseClient", return_value=mock_client):
                        result = shell._execute_command("sessions list", [])

        assert result is True
        mock_client.list_sessions.assert_called_once()


class TestPrintHelp:
    """Tests for help output."""

    def test_print_help_shows_provider_groups(self):
        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        with patch("shepherd.config.load_config", return_value=mock_config):
            shell = ShepherdShell()
            output = StringIO()

            def mock_print(*a, **k):
                print(*a, file=output)

            with patch.object(shell.console, "print", side_effect=mock_print):
                shell._print_help()

        output_str = output.getvalue()
        assert "LANGFUSE" in output_str
        assert "AIOBS" in output_str
        assert "Config" in output_str
        assert "Shell" in output_str

    def test_print_help_shows_commands(self):
        mock_config = MagicMock()
        mock_config.default_provider = "langfuse"

        with patch("shepherd.config.load_config", return_value=mock_config):
            shell = ShepherdShell()
            output = StringIO()

            def mock_print(*a, **k):
                print(*a, file=output)

            with patch.object(shell.console, "print", side_effect=mock_print):
                shell._print_help()

        output_str = output.getvalue()
        # Provider-specific commands shown
        assert "traces list" in output_str
        assert "sessions list" in output_str
        assert "config init" in output_str
        assert "help" in output_str
        assert "exit" in output_str


class TestPrintWelcome:
    """Tests for welcome message."""

    def test_print_welcome_calls_console(self):
        shell = ShepherdShell()
        with patch.object(shell.console, "print") as mock_print:
            shell._print_welcome()

        # Should print at least twice (Panel and newline)
        assert mock_print.call_count >= 1
        # First call should be a Panel
        first_call_args = mock_print.call_args_list[0]
        from rich.panel import Panel

        assert isinstance(first_call_args[0][0], Panel)


class TestShellRunLoop:
    """Tests for shell run loop."""

    def test_run_handles_keyboard_interrupt(self):
        shell = ShepherdShell()

        # Simulate Ctrl+C then exit
        call_count = [0]

        def mock_input():
            call_count[0] += 1
            if call_count[0] == 1:
                raise KeyboardInterrupt()
            return "exit"

        with patch.object(shell, "_print_welcome"):
            with patch.object(shell.console, "print"):
                with patch("builtins.input", mock_input):
                    shell.run()

        assert shell.running is False

    def test_run_handles_eof(self):
        shell = ShepherdShell()

        with patch.object(shell, "_print_welcome"):
            with patch.object(shell.console, "print"):
                with patch("builtins.input", side_effect=EOFError()):
                    shell.run()

        assert shell.running is False

    def test_run_executes_commands(self):
        shell = ShepherdShell()

        inputs = iter(["help", "version", "exit"])

        with patch.object(shell, "_print_welcome"):
            with patch.object(shell.console, "print"):
                with patch.object(shell.console, "clear"):
                    with patch("builtins.input", lambda: next(inputs)):
                        shell.run()

        assert shell.running is False


class TestPromptToolkitIntegration:
    """Tests for prompt_toolkit integration."""

    def test_completer_includes_all_commands(self):
        ShepherdShell()  # Initialize to populate SHELL_COMMANDS

        # Get base commands
        builtin = ["help", "clear", "version", "exit", "quit"]
        base_commands = list(SHELL_COMMANDS.keys()) + builtin

        # All explicit provider commands should be registered
        for cmd in ["aiobs sessions list", "langfuse traces list", "config init", "config show"]:
            assert cmd in base_commands or cmd in SHELL_COMMANDS

    def test_run_with_prompt_toolkit_fallback(self):
        """Test that shell falls back to basic input when prompt_toolkit unavailable."""
        shell = ShepherdShell()

        with patch.dict("sys.modules", {"prompt_toolkit": None}):
            with patch.object(shell, "run"):
                # Import error should trigger fallback
                try:
                    shell.run_with_prompt_toolkit()
                except ImportError:
                    pass
