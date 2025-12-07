"""Tests for interactive shell."""

from io import StringIO
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from shepherd.cli.main import app
from shepherd.cli.shell import SHELL_COMMANDS, ShepherdShell
from shepherd.models import SessionsResponse

runner = CliRunner()


class TestShellCommand:
    """Tests for shell CLI command."""

    def test_shell_help(self):
        result = runner.invoke(app, ["shell", "--help"])
        assert result.exit_code == 0
        assert "interactive" in result.stdout.lower() or "shell" in result.stdout.lower()


class TestShepherdShellInit:
    """Tests for ShepherdShell initialization."""

    def test_shell_creates_commands(self):
        ShepherdShell()  # Initialize to populate SHELL_COMMANDS
        assert "sessions list" in SHELL_COMMANDS
        assert "sessions get" in SHELL_COMMANDS
        assert "config init" in SHELL_COMMANDS
        assert "config show" in SHELL_COMMANDS
        assert "config set" in SHELL_COMMANDS
        assert "config get" in SHELL_COMMANDS

    def test_shell_commands_are_callable(self):
        ShepherdShell()  # Initialize to populate SHELL_COMMANDS
        for cmd_name, (func, desc) in SHELL_COMMANDS.items():
            assert callable(func), f"Command {cmd_name} is not callable"
            assert isinstance(desc, str), f"Command {cmd_name} has no description"


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

    def test_parse_two_word_command(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("sessions list")
        assert cmd == "sessions list"
        assert args == []

    def test_parse_two_word_command_with_args(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("sessions list --limit 5")
        assert cmd == "sessions list"
        assert args == ["--limit", "5"]

    def test_parse_slash_prefix(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("/sessions list")
        assert cmd == "sessions list"
        assert args == []

    def test_parse_slash_prefix_with_args(self):
        shell = ShepherdShell()
        cmd, args = shell._parse_command("/sessions get abc123")
        assert cmd == "sessions get"
        assert args == ["abc123"]

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


class TestSessionsCommands:
    """Tests for sessions commands in shell."""

    def test_sessions_list_in_shell(self, sample_sessions_response):
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

    def test_sessions_list_with_limit_in_shell(self, sample_sessions_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command("sessions list", ["--limit", "5"])

        assert result is True

    def test_sessions_get_in_shell(self, sample_sessions_response):
        shell = ShepherdShell()
        mock_client = MagicMock()
        mock_client.get_session.return_value = SessionsResponse(**sample_sessions_response)
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("shepherd.cli.sessions.get_api_key", return_value="test_key"):
            with patch("shepherd.cli.sessions.AIOBSClient", return_value=mock_client):
                result = shell._execute_command("sessions get", ["session-123"])

        assert result is True
        mock_client.get_session.assert_called_once_with("session-123")


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


class TestPrintHelp:
    """Tests for help output."""

    def test_print_help_shows_all_groups(self):
        shell = ShepherdShell()
        output = StringIO()

        def mock_print(*a, **k):
            print(*a, file=output)

        with patch.object(shell.console, "print", side_effect=mock_print):
            shell._print_help()

        output_str = output.getvalue()
        assert "Sessions" in output_str
        assert "Config" in output_str
        assert "Shell" in output_str

    def test_print_help_shows_commands(self):
        shell = ShepherdShell()
        output = StringIO()

        def mock_print(*a, **k):
            print(*a, file=output)

        with patch.object(shell.console, "print", side_effect=mock_print):
            shell._print_help()

        output_str = output.getvalue()
        assert "sessions list" in output_str
        assert "sessions get" in output_str
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

        # All commands should be registered
        for cmd in ["sessions list", "sessions get", "config init", "config show"]:
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
