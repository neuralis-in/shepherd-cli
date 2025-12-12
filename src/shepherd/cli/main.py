"""Main CLI entry point for Shepherd."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from shepherd import __version__
from shepherd.cli.config import app as config_app
from shepherd.cli.shell import start_shell
from shepherd.config import load_config

# Create main app
app = typer.Typer(
    name="shepherd",
    help="🐑 Debug your AI agents like you debug your code",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Add subcommands
app.add_typer(config_app, name="config", help="Manage configuration")

# Import provider-specific apps for explicit access
from shepherd.cli.sessions import app as aiobs_sessions_app
from shepherd.cli.langfuse import app as langfuse_app

# Explicit provider subcommands (always available)
app.add_typer(langfuse_app, name="langfuse", help="Langfuse provider commands (traces, sessions)")

aiobs_app = typer.Typer(help="AIOBS provider commands")
aiobs_app.add_typer(aiobs_sessions_app, name="sessions", help="List and inspect AIOBS sessions")
app.add_typer(aiobs_app, name="aiobs", help="AIOBS provider commands (sessions)")

# ============================================================================
# Provider-aware top-level commands
# These route to the appropriate provider based on config
# ============================================================================

# Top-level traces commands (route based on provider)
traces_app = typer.Typer(help="List and inspect traces (routes to current provider)")


def _get_provider() -> str:
    """Get the current default provider."""
    config = load_config()
    return config.default_provider


@traces_app.command("list")
def traces_list(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum number of traces"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    name: Optional[str] = typer.Option(None, "--name", help="Filter by trace name"),
    user_id: Optional[str] = typer.Option(None, "--user-id", "-u", help="Filter by user ID"),
    session_id: Optional[str] = typer.Option(
        None, "--session-id", "-s", help="Filter by session ID"
    ),
    tags: Optional[list[str]] = typer.Option(None, "--tag", "-t", help="Filter by tags"),
    from_timestamp: Optional[str] = typer.Option(None, "--from", help="Filter from timestamp"),
    to_timestamp: Optional[str] = typer.Option(None, "--to", help="Filter to timestamp"),
    ids_only: bool = typer.Option(False, "--ids", help="Only show trace IDs"),
):
    """List traces from the current provider."""
    provider = _get_provider()
    if provider == "langfuse":
        from shepherd.cli.langfuse import list_traces

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
    else:
        console = Console()
        console.print(f"[yellow]Provider '{provider}' does not support traces.[/yellow]")
        console.print("[dim]Switch to langfuse: shepherd config set provider langfuse[/dim]")
        raise typer.Exit(1)


@traces_app.command("get")
def traces_get(
    trace_id: str = typer.Argument(..., help="Trace ID to retrieve"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Get details for a specific trace."""
    provider = _get_provider()
    if provider == "langfuse":
        from shepherd.cli.langfuse import get_trace

        get_trace(trace_id=trace_id, output=output)
    else:
        console = Console()
        console.print(f"[yellow]Provider '{provider}' does not support traces.[/yellow]")
        console.print("[dim]Switch to langfuse: shepherd config set provider langfuse[/dim]")
        raise typer.Exit(1)


@traces_app.command("search")
def traces_search(
    query: Optional[str] = typer.Argument(None, help="Search query"),
    name: Optional[str] = typer.Option(None, "--name", help="Filter by trace name"),
    user_id: Optional[str] = typer.Option(None, "--user-id", "-u", help="Filter by user ID"),
    session_id: Optional[str] = typer.Option(
        None, "--session-id", "-s", help="Filter by session ID"
    ),
    tags: Optional[list[str]] = typer.Option(None, "--tag", "-t", help="Filter by tag(s)"),
    release: Optional[str] = typer.Option(None, "--release", "-r", help="Filter by release"),
    min_cost: Optional[float] = typer.Option(None, "--min-cost", help="Minimum cost"),
    max_cost: Optional[float] = typer.Option(None, "--max-cost", help="Maximum cost"),
    min_latency: Optional[float] = typer.Option(
        None, "--min-latency", help="Minimum latency (seconds)"
    ),
    max_latency: Optional[float] = typer.Option(
        None, "--max-latency", help="Maximum latency (seconds)"
    ),
    from_timestamp: Optional[str] = typer.Option(
        None, "--from", "--after", help="Filter from timestamp"
    ),
    to_timestamp: Optional[str] = typer.Option(
        None, "--to", "--before", help="Filter to timestamp"
    ),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum number of traces"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    ids_only: bool = typer.Option(False, "--ids", help="Only show trace IDs"),
):
    """Search and filter traces."""
    provider = _get_provider()
    if provider == "langfuse":
        from shepherd.cli.langfuse import search_traces

        search_traces(
            query=query,
            name=name,
            user_id=user_id,
            session_id=session_id,
            tags=tags,
            release=release,
            min_cost=min_cost,
            max_cost=max_cost,
            min_latency=min_latency,
            max_latency=max_latency,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            output=output,
            limit=limit,
            page=page,
            ids_only=ids_only,
        )
    else:
        console = Console()
        console.print(f"[yellow]Provider '{provider}' does not support trace search.[/yellow]")
        console.print("[dim]Switch to langfuse: shepherd config set provider langfuse[/dim]")
        console.print("[dim]Or use explicit: shepherd langfuse traces search[/dim]")
        raise typer.Exit(1)


app.add_typer(traces_app, name="traces", help="List and inspect traces (current provider)")


# Top-level sessions commands (route based on provider)
sessions_app = typer.Typer(help="List and inspect sessions (routes to current provider)")


@sessions_app.command("list")
def sessions_list(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n", help="Maximum number of sessions"),
    page: int = typer.Option(1, "--page", "-p", help="Page number (Langfuse only)"),
    from_timestamp: Optional[str] = typer.Option(
        None, "--from", help="Filter from timestamp (Langfuse only)"
    ),
    to_timestamp: Optional[str] = typer.Option(
        None, "--to", help="Filter to timestamp (Langfuse only)"
    ),
    ids_only: bool = typer.Option(False, "--ids", help="Only show session IDs"),
):
    """List sessions from the current provider."""
    provider = _get_provider()
    if provider == "langfuse":
        from shepherd.cli.langfuse import list_sessions

        list_sessions(
            output=output,
            limit=limit or 50,
            page=page,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            ids_only=ids_only,
        )
    else:
        from shepherd.cli.sessions import list_sessions

        list_sessions(output=output, limit=limit, ids_only=ids_only)


@sessions_app.command("get")
def sessions_get(
    session_id: str = typer.Argument(..., help="Session ID to retrieve"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Get details for a specific session."""
    provider = _get_provider()
    if provider == "langfuse":
        from shepherd.cli.langfuse import get_session

        get_session(session_id=session_id, output=output)
    else:
        from shepherd.cli.sessions import get_session

        get_session(session_id=session_id, output=output)


@sessions_app.command("search")
def sessions_search(
    query: Optional[str] = typer.Argument(None, help="Search query"),
    label: Optional[list[str]] = typer.Option(
        None, "--label", "-l", help="Filter by label(s) (AIOBS)"
    ),
    provider_filter: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Filter by provider (AIOBS)"
    ),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Filter by model (AIOBS)"),
    function: Optional[str] = typer.Option(
        None, "--function", "-f", help="Filter by function name (AIOBS)"
    ),
    user_id: Optional[str] = typer.Option(
        None, "--user-id", "-u", help="Filter by user ID (Langfuse)"
    ),
    after: Optional[str] = typer.Option(
        None, "--after", "--from", help="Filter sessions after date"
    ),
    before: Optional[str] = typer.Option(
        None, "--before", "--to", help="Filter sessions before date"
    ),
    has_errors: bool = typer.Option(
        False, "--errors", help="Only show sessions with errors (AIOBS)"
    ),
    evals_failed: bool = typer.Option(
        False, "--failed-evals", help="Only show sessions with failed evals (AIOBS)"
    ),
    min_traces: Optional[int] = typer.Option(None, "--min-traces", help="Min traces (Langfuse)"),
    max_traces: Optional[int] = typer.Option(None, "--max-traces", help="Max traces (Langfuse)"),
    min_cost: Optional[float] = typer.Option(None, "--min-cost", help="Minimum cost (Langfuse)"),
    max_cost: Optional[float] = typer.Option(None, "--max-cost", help="Maximum cost (Langfuse)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n", help="Maximum number of sessions"),
    page: int = typer.Option(1, "--page", help="Page number (Langfuse)"),
    ids_only: bool = typer.Option(False, "--ids", help="Only show session IDs"),
):
    """Search and filter sessions."""
    provider = _get_provider()
    if provider == "langfuse":
        from shepherd.cli.langfuse import search_sessions

        search_sessions(
            query=query,
            user_id=user_id,
            min_traces=min_traces,
            max_traces=max_traces,
            min_cost=min_cost,
            max_cost=max_cost,
            from_timestamp=after,
            to_timestamp=before,
            output=output,
            limit=limit or 50,
            page=page,
            ids_only=ids_only,
        )
    elif provider == "aiobs":
        from shepherd.cli.sessions import search_sessions

        search_sessions(
            query=query,
            label=label,
            provider=provider_filter,
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
    else:
        console = Console()
        console.print(f"[yellow]Provider '{provider}' does not support session search.[/yellow]")
        raise typer.Exit(1)


@sessions_app.command("diff")
def sessions_diff(
    session_id1: str = typer.Argument(..., help="First session ID"),
    session_id2: str = typer.Argument(..., help="Second session ID"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Compare two sessions (AIOBS only)."""
    provider = _get_provider()
    if provider == "aiobs":
        from shepherd.cli.sessions import diff_sessions

        diff_sessions(session_id1=session_id1, session_id2=session_id2, output=output)
    else:
        console = Console()
        console.print(f"[yellow]Provider '{provider}' does not support session diff.[/yellow]")
        console.print("[dim]Switch to aiobs: shepherd config set provider aiobs[/dim]")
        console.print("[dim]Or use explicit: shepherd aiobs sessions diff[/dim]")
        raise typer.Exit(1)


app.add_typer(sessions_app, name="sessions", help="List and inspect sessions (current provider)")

console = Console()


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold green]shepherd[/bold green] v{__version__}")


@app.command()
def shell():
    """Start an interactive Shepherd shell."""
    start_shell()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """🐑 Shepherd CLI - Debug your AI agents like you debug your code."""
    # This will be expanded later for shell mode
    pass


if __name__ == "__main__":
    app()
