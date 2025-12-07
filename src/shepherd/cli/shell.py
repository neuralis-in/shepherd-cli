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
        from shepherd.cli.sessions import get_session, list_sessions, search_sessions

        # Sessions commands - pass explicit defaults since typer.Option() returns objects
        def _list_sessions(output=None, limit=None, ids_only=False):
            list_sessions(output=output, limit=limit, ids_only=ids_only)

        def _get_session(session_id, output=None):
            get_session(session_id=session_id, output=output)

        def _search_sessions(
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

        SHELL_COMMANDS["sessions list"] = (_list_sessions, "List all sessions")
        SHELL_COMMANDS["sessions get"] = (_get_session, "Get details for a specific session")
        SHELL_COMMANDS["sessions search"] = (_search_sessions, "Search and filter sessions")

        # Config commands
        def _config_init():
            init_config()

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
        """Get the shell prompt."""
        return "[bold cyan]shepherd[/bold cyan] [dim]>[/dim] "

    def _print_welcome(self):
        """Print welcome message."""
        welcome = Text()
        welcome.append("🐑 ", style="bold")
        welcome.append("Shepherd Shell", style="bold green")
        welcome.append(f" v{__version__}\n", style="dim")
        welcome.append("Debug your AI agents like you debug your code\n\n", style="italic")
        welcome.append("Type ", style="dim")
        welcome.append("help", style="bold cyan")
        welcome.append(" for available commands, ", style="dim")
        welcome.append("exit", style="bold cyan")
        welcome.append(" to quit.", style="dim")

        self.console.print(Panel(welcome, border_style="cyan", padding=(1, 2)))
        self.console.print()

    def _print_help(self):
        """Print help message with available commands."""
        self.console.print("\n[bold]Available Commands:[/bold]\n")

        # Group commands
        groups = {
            "Sessions": ["sessions list", "sessions get", "sessions search"],
            "Config": ["config init", "config show", "config set", "config get"],
            "Shell": ["help", "clear", "version", "exit", "quit"],
        }

        for group_name, commands in groups.items():
            self.console.print(f"  [bold cyan]{group_name}[/bold cyan]")
            for cmd in commands:
                if cmd in SHELL_COMMANDS:
                    _, desc = SHELL_COMMANDS[cmd]
                    self.console.print(f"    [green]{cmd:<20}[/green] {desc}")
                elif cmd == "help":
                    self.console.print(f"    [green]{cmd:<20}[/green] Show this help message")
                elif cmd == "clear":
                    self.console.print(f"    [green]{cmd:<20}[/green] Clear the screen")
                elif cmd == "version":
                    self.console.print(f"    [green]{cmd:<20}[/green] Show version information")
                elif cmd in ("exit", "quit"):
                    self.console.print(f"    [green]{cmd:<20}[/green] Exit the shell")
            self.console.print()

        self.console.print("[dim]Tip: Commands work the same as CLI commands.[/dim]")
        self.console.print(
            "[dim]Syntax:[/dim] [cyan]/command[/cyan] [dim]or[/dim] [cyan]command[/cyan]"
        )
        self.console.print("[dim]Example:[/dim] [cyan]/sessions list --limit 5[/cyan]\n")

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

        # Check for two-word commands first (e.g., "sessions list")
        if len(parts) >= 2:
            two_word = f"{parts[0]} {parts[1]}"
            if two_word in SHELL_COMMANDS:
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

        # Check registered commands
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
                    # Handle --label specially - can be specified multiple times
                    if key == "label":
                        labels.append(args[i + 1])
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
                    "p": "provider",
                    "m": "model",
                    "f": "function",
                }
                key = flag_map.get(key, key)
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    # Handle -l specially - can be specified multiple times
                    if key == "label":
                        labels.append(args[i + 1])
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

        # Handle positional arguments based on command
        if cmd == "sessions get" and positional:
            kwargs["session_id"] = positional[0]
        elif cmd == "sessions search" and positional:
            kwargs["query"] = positional[0]
        elif cmd == "config set" and len(positional) >= 2:
            kwargs["key"] = positional[0]
            kwargs["value"] = positional[1]
        elif cmd == "config get" and positional:
            kwargs["key"] = positional[0]

        # Convert limit to int if present and not a boolean flag
        if "limit" in kwargs:
            if kwargs["limit"] is True:
                # --limit was passed without a value, remove it
                del kwargs["limit"]
            else:
                try:
                    kwargs["limit"] = int(kwargs["limit"])
                except (ValueError, TypeError):
                    del kwargs["limit"]

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
