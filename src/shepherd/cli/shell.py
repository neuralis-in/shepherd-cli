"""Interactive shell for Shepherd CLI."""

from __future__ import annotations

import shlex
from collections.abc import Callable

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from shepherd import __version__

app = typer.Typer(help="Interactive shell mode")
console = Console()

# Command registry for the shell
SHELL_COMMANDS: dict[str, tuple[Callable, str]] = {}


def register_command(name: str, description: str):
    """Decorator to register a command in the shell."""

    def decorator(func: Callable):
        SHELL_COMMANDS[name] = (func, description)
        return func

    return decorator


class ShepherdShell:
    """Interactive shell for Shepherd CLI."""

    def __init__(self):
        self.running = False
        self.console = Console()
        self._setup_commands()

    def _setup_commands(self):
        """Set up built-in shell commands."""
        # Import here to avoid circular imports
        from shepherd.cli.config import get_config, init_config, set_config, show_config
        from shepherd.cli.langfuse import (
            get_session as lf_get_session,
        )
        from shepherd.cli.langfuse import (
            get_trace,
            list_traces,
        )
        from shepherd.cli.langfuse import (
            list_sessions as lf_list_sessions,
        )
        from shepherd.cli.sessions import (
            diff_sessions,
            get_session,
            list_sessions,
            search_sessions,
        )

        # AIOBS Sessions commands - pass explicit defaults since typer.Option() returns objects
        def _aiobs_list_sessions(output=None, limit=None, ids_only=False):
            list_sessions(output=output, limit=limit, ids_only=ids_only)

        def _aiobs_get_session(session_id, output=None):
            get_session(session_id=session_id, output=output)

        def _aiobs_search_sessions(
            query=None,
            label=None,
            provider=None,
            model=None,
            function=None,
            after=None,
            before=None,
            has_errors=False,
            evals_failed=False,
            output=None,
            limit=None,
            ids_only=False,
        ):
            search_sessions(
                query=query,
                label=label,
                provider=provider,
                model=model,
                function=function,
                after=after,
                before=before,
                has_errors=has_errors,
                evals_failed=evals_failed,
                output=output,
                limit=limit,
                ids_only=ids_only,
            )

        def _aiobs_diff_sessions(session_id1, session_id2, output=None):
            diff_sessions(session_id1=session_id1, session_id2=session_id2, output=output)

        # Explicit AIOBS commands (always available)
        SHELL_COMMANDS["aiobs sessions list"] = (_aiobs_list_sessions, "List all sessions")
        SHELL_COMMANDS["aiobs sessions get"] = (_aiobs_get_session, "Get session details")
        SHELL_COMMANDS["aiobs sessions search"] = (_aiobs_search_sessions, "Search sessions")
        SHELL_COMMANDS["aiobs sessions diff"] = (_aiobs_diff_sessions, "Compare two sessions")

        # Langfuse Traces commands
        def _lf_list_traces(
            output=None,
            limit=50,
            page=1,
            name=None,
            user_id=None,
            session_id=None,
            tags=None,
            from_timestamp=None,
            to_timestamp=None,
            ids_only=False,
        ):
            list_traces(
                output=output,
                limit=limit,
                page=page,
                name=name,
                user_id=user_id,
                session_id=session_id,
                tags=tags,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
                ids_only=ids_only,
            )

        def _lf_get_trace(trace_id, output=None):
            get_trace(trace_id=trace_id, output=output)

        # Langfuse sessions commands
        def _lf_list_sessions(
            output=None,
            limit=50,
            page=1,
            from_timestamp=None,
            to_timestamp=None,
            ids_only=False,
        ):
            lf_list_sessions(
                output=output,
                limit=limit,
                page=page,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
                ids_only=ids_only,
            )

        def _lf_get_session(session_id, output=None):
            lf_get_session(session_id=session_id, output=output)

        # Explicit Langfuse commands (always available)
        SHELL_COMMANDS["langfuse sessions list"] = (_lf_list_sessions, "List sessions")
        SHELL_COMMANDS["langfuse sessions get"] = (_lf_get_session, "Get session details")
        SHELL_COMMANDS["langfuse traces list"] = (_lf_list_traces, "List traces")
        SHELL_COMMANDS["langfuse traces get"] = (_lf_get_trace, "Get trace details")

        # Store provider-specific command mappings for dynamic routing
        self._provider_commands = {
            "langfuse": {
                "traces list": (_lf_list_traces, "List traces"),
                "traces get": (_lf_get_trace, "Get trace details"),
                "sessions list": (_lf_list_sessions, "List sessions"),
                "sessions get": (_lf_get_session, "Get session details"),
            },
            "aiobs": {
                "sessions list": (_aiobs_list_sessions, "List all sessions"),
                "sessions get": (_aiobs_get_session, "Get session details"),
                "sessions search": (_aiobs_search_sessions, "Search sessions"),
                "sessions diff": (_aiobs_diff_sessions, "Compare two sessions"),
            },
        }

        # Config commands
        def _config_init(provider=None):
            init_config(provider=provider)

        def _config_show():
            show_config()

        def _config_set(key, value):
            set_config(key=key, value=value)

        def _config_get(key):
            get_config(key=key)

        SHELL_COMMANDS["config init"] = (_config_init, "Initialize configuration")
        SHELL_COMMANDS["config show"] = (_config_show, "Show current configuration")
        SHELL_COMMANDS["config set"] = (_config_set, "Set a configuration value")
        SHELL_COMMANDS["config get"] = (_config_get, "Get a configuration value")

    def _get_prompt(self) -> str:
        """Get the shell prompt with provider indicator."""
        from shepherd.config import load_config

        config = load_config()
        provider = config.default_provider
        provider_color = "magenta" if provider == "langfuse" else "yellow"
        return (
            f"[bold cyan]shepherd[/bold cyan] "
            f"[{provider_color}]({provider})[/{provider_color}] [dim]>[/dim] "
        )

    def _print_welcome(self):
        """Print welcome message."""
        from shepherd.config import load_config

        config = load_config()
        provider = config.default_provider
        provider_color = "magenta" if provider == "langfuse" else "yellow"

        welcome = Text()
        welcome.append("🐑 ", style="bold")
        welcome.append("Shepherd Shell", style="bold green")
        welcome.append(f" v{__version__}\n", style="dim")
        welcome.append("Debug your AI agents like you debug your code\n\n", style="italic")
        welcome.append("Provider: ", style="dim")
        welcome.append(provider, style=f"bold {provider_color}")
        welcome.append("  (change: ", style="dim")
        welcome.append("config set provider <name>", style="cyan")
        welcome.append(")\n\n", style="dim")
        welcome.append("Type ", style="dim")
        welcome.append("help", style="bold cyan")
        welcome.append(" for available commands, ", style="dim")
        welcome.append("exit", style="bold cyan")
        welcome.append(" to quit.", style="dim")

        self.console.print(Panel(welcome, border_style="cyan", padding=(1, 2)))
        self.console.print()

    def _print_help(self):
        """Print help message with available commands based on current provider."""
        from shepherd.config import load_config

        config = load_config()
        provider = config.default_provider
        provider_color = "magenta" if provider == "langfuse" else "yellow"

        self.console.print("\n[bold]Available Commands:[/bold]\n")

        # Show commands for current provider
        self.console.print(
            f"  [bold {provider_color}]{provider.upper()} (active provider)[/bold {provider_color}]"
        )
        if hasattr(self, "_provider_commands") and provider in self._provider_commands:
            for cmd, (_, desc) in self._provider_commands[provider].items():
                self.console.print(f"    [green]{cmd:<28}[/green] {desc}")
        self.console.print()

        # Show explicit provider commands for the OTHER provider
        other_provider = "aiobs" if provider == "langfuse" else "langfuse"
        other_color = "yellow" if provider == "langfuse" else "magenta"
        explicit_cmds = [
            cmd for cmd in SHELL_COMMANDS.keys() if cmd.startswith(f"{other_provider} ")
        ]
        if explicit_cmds:
            prefix_msg = f"{other_provider.upper()} (use explicit prefix)"
            self.console.print(f"  [bold {other_color}]{prefix_msg}[/bold {other_color}]")
            for cmd in sorted(explicit_cmds):
                _, desc = SHELL_COMMANDS[cmd]
                self.console.print(f"    [green]{cmd:<28}[/green] {desc}")
            self.console.print()

        # Config commands
        self.console.print("  [bold cyan]Config[/bold cyan]")
        for cmd in ["config init", "config show", "config set", "config get"]:
            if cmd in SHELL_COMMANDS:
                _, desc = SHELL_COMMANDS[cmd]
                self.console.print(f"    [green]{cmd:<28}[/green] {desc}")
        self.console.print()

        # Shell commands
        self.console.print("  [bold cyan]Shell[/bold cyan]")
        shell_cmds = [
            ("help", "Show this help message"),
            ("clear", "Clear the screen"),
            ("version", "Show version information"),
            ("exit", "Exit the shell"),
        ]
        for cmd, desc in shell_cmds:
            self.console.print(f"    [green]{cmd:<28}[/green] {desc}")
        self.console.print()

        self.console.print("[dim]Tip: Commands work the same as CLI commands.[/dim]")
        self.console.print(
            "[dim]Switch provider:[/dim] [cyan]config set provider <langfuse|aiobs>[/cyan]"
        )
        example_cmd = (
            "traces list --limit 5" if provider == "langfuse" else "sessions list --limit 5"
        )
        self.console.print(f"[dim]Example:[/dim] [cyan]{example_cmd}[/cyan]\n")

    def _parse_command(self, line: str) -> tuple[str, list[str]]:
        """Parse a command line into command and arguments."""
        # Strip leading slash if present (support /command syntax)
        if line.startswith("/"):
            line = line[1:]

        try:
            parts = shlex.split(line)
        except ValueError:
            parts = line.split()

        if not parts:
            return "", []

        # Get current provider for checking provider-specific commands
        from shepherd.config import load_config

        config = load_config()
        provider = config.default_provider
        provider_cmds = set()
        if hasattr(self, "_provider_commands") and provider in self._provider_commands:
            provider_cmds = set(self._provider_commands[provider].keys())

        # Check for three-word commands first (e.g., "langfuse traces list", "aiobs sessions get")
        if len(parts) >= 3:
            three_word = f"{parts[0]} {parts[1]} {parts[2]}"
            if three_word in SHELL_COMMANDS:
                return three_word, parts[3:]

        # Check for two-word commands (e.g., "sessions list", "traces get")
        if len(parts) >= 2:
            two_word = f"{parts[0]} {parts[1]}"
            # Check both global commands and provider-specific commands
            if two_word in SHELL_COMMANDS or two_word in provider_cmds:
                return two_word, parts[2:]

        return parts[0], parts[1:]

    def _execute_command(self, cmd: str, args: list[str]) -> bool:
        """Execute a command. Returns False if shell should exit."""
        if not cmd:
            return True

        # Built-in commands
        if cmd in ("exit", "quit"):
            self.console.print("[dim]Goodbye! 👋[/dim]\n")
            return False

        if cmd == "help":
            self._print_help()
            return True

        if cmd == "clear":
            self.console.clear()
            return True

        if cmd == "version":
            self.console.print(f"[bold green]shepherd[/bold green] v{__version__}")
            return True

        # Get current provider for dynamic command routing
        from shepherd.config import load_config

        config = load_config()
        provider = config.default_provider

        # Check if this is a provider-agnostic command (traces/sessions without prefix)
        # Route to current provider's implementation
        if hasattr(self, "_provider_commands") and provider in self._provider_commands:
            if cmd in self._provider_commands[provider]:
                func, _ = self._provider_commands[provider][cmd]
                try:
                    kwargs = self._parse_args(cmd, args)
                    func(**kwargs)
                except typer.Exit:
                    pass
                except SystemExit:
                    pass
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Command interrupted.[/yellow]")
                except Exception as e:
                    self.console.print(f"[red]Error:[/red] {e}")
                return True

        # Check explicit provider commands (e.g., "langfuse traces list", "aiobs sessions get")
        if cmd in SHELL_COMMANDS:
            func, _ = SHELL_COMMANDS[cmd]
            try:
                # Parse arguments for the command
                kwargs = self._parse_args(cmd, args)
                func(**kwargs)
            except typer.Exit:
                pass  # Normal exit, continue shell
            except SystemExit:
                pass  # Typer sometimes raises SystemExit
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Command interrupted.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error:[/red] {e}")
            return True

        # Unknown command
        self.console.print(f"[red]Unknown command:[/red] {cmd}")
        self.console.print("[dim]Type 'help' for available commands.[/dim]")
        return True

    def _parse_args(self, cmd: str, args: list[str]) -> dict:
        """Parse command arguments into kwargs."""
        kwargs: dict = {}
        positional: list[str] = []
        labels: list[str] = []  # Collect multiple --label flags
        tags: list[str] = []  # Collect multiple --tag flags
        i = 0

        while i < len(args):
            arg = args[i]
            if arg.startswith("--"):
                key = arg[2:].replace("-", "_")
                # Handle boolean flags (no value expected)
                bool_flags = {"ids", "has_errors", "errors", "evals_failed", "failed_evals"}
                if key in bool_flags:
                    kwargs[key] = True
                    i += 1
                elif i + 1 < len(args) and not args[i + 1].startswith("-"):
                    # Handle --label and --tag specially - can be specified multiple times
                    if key == "label":
                        labels.append(args[i + 1])
                    elif key == "tag":
                        tags.append(args[i + 1])
                    else:
                        kwargs[key] = args[i + 1]
                    i += 2
                else:
                    kwargs[key] = True
                    i += 1
            elif arg.startswith("-"):
                # Short flags
                key = arg[1:]
                # Map common short flags
                flag_map = {
                    "o": "output",
                    "n": "limit",
                    "l": "label",
                    "p": "page",
                    "m": "model",
                    "f": "function",
                    "u": "user_id",
                    "s": "session_id",
                    "t": "tag",
                }
                key = flag_map.get(key, key)
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    # Handle -l and -t specially - can be specified multiple times
                    if key == "label":
                        labels.append(args[i + 1])
                    elif key == "tag":
                        tags.append(args[i + 1])
                    else:
                        kwargs[key] = args[i + 1]
                    i += 2
                else:
                    kwargs[key] = True
                    i += 1
            else:
                positional.append(arg)
                i += 1

        # Add collected labels if any
        if labels:
            kwargs["label"] = labels

        # Add collected tags if any
        if tags:
            kwargs["tags"] = tags

        # Handle positional arguments based on command
        if cmd in ("sessions get", "aiobs sessions get", "langfuse sessions get") and positional:
            kwargs["session_id"] = positional[0]
        elif cmd in ("sessions search", "aiobs sessions search") and positional:
            kwargs["query"] = positional[0]
        elif cmd in ("sessions diff", "aiobs sessions diff") and len(positional) >= 2:
            kwargs["session_id1"] = positional[0]
            kwargs["session_id2"] = positional[1]
        elif cmd in ("traces get", "langfuse traces get") and positional:
            kwargs["trace_id"] = positional[0]
        elif cmd == "config set" and len(positional) >= 2:
            kwargs["key"] = positional[0]
            kwargs["value"] = positional[1]
        elif cmd == "config get" and positional:
            kwargs["key"] = positional[0]
        elif cmd == "config init" and positional:
            kwargs["provider"] = positional[0]

        # Convert numeric values to int if present and not a boolean flag
        for int_field in ("limit", "page"):
            if int_field in kwargs:
                if kwargs[int_field] is True:
                    # Flag was passed without a value, remove it
                    del kwargs[int_field]
                else:
                    try:
                        kwargs[int_field] = int(kwargs[int_field])
                    except (ValueError, TypeError):
                        del kwargs[int_field]

        # Handle timestamp aliases
        if "from" in kwargs:
            kwargs["from_timestamp"] = kwargs.pop("from")
        if "to" in kwargs:
            kwargs["to_timestamp"] = kwargs.pop("to")

        # Handle boolean flags
        if "ids" in kwargs:
            kwargs["ids_only"] = bool(kwargs.pop("ids"))
        if "errors" in kwargs:
            kwargs["has_errors"] = bool(kwargs.pop("errors"))
        if "failed_evals" in kwargs:
            kwargs["evals_failed"] = bool(kwargs.pop("failed_evals"))

        return kwargs

    def run(self):
        """Run the interactive shell."""
        self.running = True
        self._print_welcome()

        while self.running:
            try:
                # Use rich prompt
                self.console.print(self._get_prompt(), end="")
                line = input().strip()

                cmd, args = self._parse_command(line)
                if not self._execute_command(cmd, args):
                    self.running = False

            except KeyboardInterrupt:
                self.console.print("\n[dim]Press Ctrl+D or type 'exit' to quit.[/dim]")
            except EOFError:
                self.console.print("\n[dim]Goodbye! 👋[/dim]\n")
                self.running = False

    def run_with_prompt_toolkit(self):
        """Run the shell with prompt_toolkit for better UX (if available)."""
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
            from prompt_toolkit.completion import WordCompleter
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.styles import Style

            from shepherd.config import get_config_dir

            # Create history file
            history_file = get_config_dir() / ".shell_history"
            history = FileHistory(str(history_file))

            # Create completer with commands (both with and without / prefix)
            builtin = ["help", "clear", "version", "exit", "quit"]
            base_commands = list(SHELL_COMMANDS.keys()) + builtin
            commands = base_commands + [f"/{cmd}" for cmd in base_commands]
            completer = WordCompleter(commands, ignore_case=True)

            # Custom style
            style = Style.from_dict(
                {
                    "prompt": "ansicyan bold",
                    "prompt.symbol": "ansiwhite",
                }
            )

            session: PromptSession = PromptSession(
                history=history,
                auto_suggest=AutoSuggestFromHistory(),
                completer=completer,
                style=style,
            )

            self.running = True
            self._print_welcome()

            while self.running:
                try:
                    line = session.prompt("shepherd > ").strip()
                    cmd, args = self._parse_command(line)
                    if not self._execute_command(cmd, args):
                        self.running = False

                except KeyboardInterrupt:
                    self.console.print("[dim]Press Ctrl+D or type 'exit' to quit.[/dim]")
                except EOFError:
                    self.console.print("\n[dim]Goodbye! 👋[/dim]\n")
                    self.running = False

        except ImportError:
            # Fall back to basic input
            self.run()


def start_shell():
    """Start the interactive shell."""
    shell = ShepherdShell()

    # Try to use prompt_toolkit for better experience
    try:
        import prompt_toolkit  # noqa: F401

        shell.run_with_prompt_toolkit()
    except ImportError:
        shell.run()


@app.callback(invoke_without_command=True)
def shell_main(ctx: typer.Context):
    """Start an interactive Shepherd shell."""
    if ctx.invoked_subcommand is None:
        start_shell()
