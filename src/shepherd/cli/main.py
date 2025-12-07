"""Main CLI entry point for Shepherd."""

from __future__ import annotations

import typer
from rich.console import Console

from shepherd import __version__
from shepherd.cli.config import app as config_app
from shepherd.cli.sessions import app as sessions_app

# Create main app
app = typer.Typer(
    name="shepherd",
    help="🐑 Debug your AI agents like you debug your code",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Add subcommands
app.add_typer(config_app, name="config", help="Manage configuration")
app.add_typer(sessions_app, name="sessions", help="List and inspect sessions")

console = Console()


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold green]shepherd[/bold green] v{__version__}")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """🐑 Shepherd CLI - Debug your AI agents like you debug your code."""
    # This will be expanded later for shell mode
    pass


if __name__ == "__main__":
    app()
