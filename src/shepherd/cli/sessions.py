"""Sessions CLI commands."""

from __future__ import annotations

import json
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from shepherd.config import get_api_key, get_endpoint, load_config
from shepherd.models import SessionsResponse, TraceNode
from shepherd.providers.aiobs import (
    AIOBSClient,
    AIOBSError,
    AuthenticationError,
    SessionNotFoundError,
)

app = typer.Typer(help="List and inspect sessions")
console = Console()


def _format_timestamp(ts: float) -> str:
    """Format a Unix timestamp to human-readable string."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _format_duration(ms: float) -> str:
    """Format duration in milliseconds to human-readable string."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms / 1000:.1f}s"
    else:
        return f"{ms / 60000:.1f}m"


def _get_client() -> AIOBSClient:
    """Get an authenticated AIOBS client."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]No API key configured.[/red]")
        console.print("Run [bold]shepherd config init[/bold] to set up your API key.")
        console.print("Or set the [bold]AIOBS_API_KEY[/bold] environment variable.")
        raise typer.Exit(1)

    endpoint = get_endpoint()
    return AIOBSClient(api_key=api_key, endpoint=endpoint)


def _print_sessions_table(response: SessionsResponse) -> None:
    """Print sessions as a rich table."""
    if not response.sessions:
        console.print("[yellow]No sessions found.[/yellow]")
        return

    table = Table(title="Sessions", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Started", style="green")
    table.add_column("Duration", style="yellow", justify="right")
    table.add_column("Events", justify="right")
    table.add_column("Labels", style="dim")

    # Count events per session
    event_counts: dict[str, int] = {}
    for event in response.events:
        event_counts[event.session_id] = event_counts.get(event.session_id, 0) + 1
    for event in response.function_events:
        event_counts[event.session_id] = event_counts.get(event.session_id, 0) + 1

    for session in response.sessions:
        # Calculate duration
        duration = ""
        if session.ended_at and session.started_at:
            duration_ms = (session.ended_at - session.started_at) * 1000
            duration = _format_duration(duration_ms)

        # Format labels
        labels = ", ".join(f"{k}={v}" for k, v in session.labels.items()) if session.labels else ""

        table.add_row(
            session.id[:8] + "...",  # Truncate ID for display
            session.name,
            _format_timestamp(session.started_at),
            duration,
            str(event_counts.get(session.id, 0)),
            labels[:30] + "..." if len(labels) > 30 else labels,
        )

    console.print(table)


def _print_sessions_json(response: SessionsResponse) -> None:
    """Print sessions as JSON."""
    output = {
        "sessions": [s.model_dump() for s in response.sessions],
        "total_events": len(response.events),
        "total_function_events": len(response.function_events),
    }
    console.print_json(json.dumps(output, indent=2))


def _build_trace_tree(node: TraceNode, tree: Tree) -> None:
    """Recursively build a rich tree from a trace node."""
    # Determine the label
    if node.event_type == "function":
        label = f"[bold blue]fn[/bold blue] {node.name or node.api}"
    else:
        model = ""
        if node.request and "model" in node.request:
            model = f" ({node.request['model']})"
        label = f"[bold magenta]{node.provider}[/bold magenta] {node.api}{model}"

    # Add duration
    label += f" [dim]{_format_duration(node.duration_ms)}[/dim]"

    # Add to tree
    branch = tree.add(label)

    # Recurse for children
    for child in node.children:
        _build_trace_tree(child, branch)


def _print_session_detail(response: SessionsResponse) -> None:
    """Print detailed session information."""
    if not response.sessions:
        console.print("[yellow]No session data found.[/yellow]")
        return

    session = response.sessions[0]

    # Session header
    duration = ""
    if session.ended_at and session.started_at:
        duration_ms = (session.ended_at - session.started_at) * 1000
        duration = _format_duration(duration_ms)

    header = f"""[bold]Session:[/bold] {session.id}
[bold]Name:[/bold]    {session.name}
[bold]Started:[/bold] {_format_timestamp(session.started_at)}
[bold]Duration:[/bold] {duration}
[bold]Events:[/bold]  {len(response.events)} LLM calls, {len(response.function_events)} functions"""

    if session.labels:
        labels = ", ".join(f"{k}={v}" for k, v in session.labels.items())
        header += f"\n[bold]Labels:[/bold]  {labels}"

    if session.meta:
        meta = ", ".join(f"{k}={v}" for k, v in session.meta.items())
        header += f"\n[bold]Meta:[/bold]    {meta}"

    console.print(Panel(header, title="[bold]Session Info[/bold]", expand=False))

    # Trace tree
    if response.trace_tree:
        console.print("\n[bold]Trace Tree:[/bold]\n")
        tree = Tree(f"[bold]{session.name}[/bold]")
        for root_node in response.trace_tree:
            _build_trace_tree(root_node, tree)
        console.print(tree)

    # Events summary
    if response.events:
        console.print("\n[bold]LLM Calls:[/bold]\n")
        event_table = Table(show_header=True, header_style="bold")
        event_table.add_column("Provider", style="magenta")
        event_table.add_column("API")
        event_table.add_column("Model", style="cyan")
        event_table.add_column("Duration", justify="right")
        event_table.add_column("Tokens", justify="right")

        for event in response.events[:10]:  # Limit to 10
            model = event.request.get("model", "-") if event.request else "-"
            tokens = "-"
            if event.response and "usage" in event.response:
                usage = event.response["usage"]
                tokens = str(usage.get("total_tokens", "-"))

            event_table.add_row(
                event.provider,
                event.api,
                model,
                _format_duration(event.duration_ms),
                tokens,
            )

        console.print(event_table)

        if len(response.events) > 10:
            console.print(f"[dim]... and {len(response.events) - 10} more events[/dim]")


@app.command("list")
def list_sessions(
    output: str = typer.Option(
        None,
        "--output", "-o",
        help="Output format: table or json (overrides config)",
    ),
    limit: int = typer.Option(
        None,
        "--limit", "-n",
        help="Maximum number of sessions to display",
    ),
    ids_only: bool = typer.Option(
        False,
        "--ids",
        help="Only print session IDs (one per line)",
    ),
):
    """List all sessions."""
    config = load_config()
    output_format = output or config.cli.output_format

    try:
        with _get_client() as client:
            response = client.list_sessions()

            # Apply limit if specified
            if limit and response.sessions:
                response.sessions = response.sessions[:limit]

            # IDs only mode
            if ids_only:
                for session in response.sessions:
                    console.print(session.id)
            elif output_format == "json":
                _print_sessions_json(response)
            else:
                _print_sessions_table(response)

    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise typer.Exit(1)
    except AIOBSError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("get")
def get_session(
    session_id: str = typer.Argument(..., help="Session ID to fetch"),
    output: str = typer.Option(
        None,
        "--output", "-o",
        help="Output format: table or json (overrides config)",
    ),
):
    """Get details for a specific session."""
    config = load_config()
    output_format = output or config.cli.output_format

    try:
        with _get_client() as client:
            response = client.get_session(session_id)

            if output_format == "json":
                console.print_json(response.model_dump_json(indent=2))
            else:
                _print_session_detail(response)

    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise typer.Exit(1)
    except SessionNotFoundError as e:
        console.print(f"[red]Session not found:[/red] {e}")
        raise typer.Exit(1)
    except AIOBSError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

