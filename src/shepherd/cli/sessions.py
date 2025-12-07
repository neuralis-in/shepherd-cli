"""Sessions CLI commands."""

from __future__ import annotations

import json
import re
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from shepherd.config import get_api_key, get_endpoint, load_config
from shepherd.models import Event, FunctionEvent, Session, SessionsResponse, TraceNode
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
        "--output",
        "-o",
        help="Output format: table or json (overrides config)",
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-n",
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
        "--output",
        "-o",
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


def _parse_date(date_str: str) -> float:
    """Parse a date string to Unix timestamp."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).timestamp()
        except ValueError:
            continue
    raise typer.BadParameter(
        f"Invalid date format: {date_str}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
    )


def _parse_label(label_str: str) -> tuple[str, str]:
    """Parse a label string in key=value format."""
    if "=" not in label_str:
        raise typer.BadParameter(f"Invalid label format: {label_str}. Use key=value")
    key, value = label_str.split("=", 1)
    return key.strip(), value.strip()


def _session_matches_query(session: Session, query: str) -> bool:
    """Check if a session matches the text query."""
    query_lower = query.lower()
    # Match against ID or name
    if query_lower in session.id.lower():
        return True
    if query_lower in session.name.lower():
        return True
    # Match against label values
    for value in session.labels.values():
        if query_lower in str(value).lower():
            return True
    # Match against meta values
    for value in session.meta.values():
        if query_lower in str(value).lower():
            return True
    return False


def _session_matches_labels(session: Session, labels: list[tuple[str, str]]) -> bool:
    """Check if a session has all the specified labels."""
    for key, value in labels:
        if key not in session.labels:
            return False
        if session.labels[key] != value:
            return False
    return True


def _session_has_provider(
    session: Session,
    events: list[Event],
    function_events: list[FunctionEvent],
    provider: str,
) -> bool:
    """Check if a session has events from the specified provider."""
    provider_lower = provider.lower()
    for event in events:
        if event.session_id == session.id and event.provider.lower() == provider_lower:
            return True
    for event in function_events:
        if event.session_id == session.id and event.provider.lower() == provider_lower:
            return True
    return False


def _session_has_model(
    session: Session,
    events: list[Event],
    model: str,
) -> bool:
    """Check if a session has events using the specified model."""
    model_lower = model.lower()
    for event in events:
        if event.session_id != session.id:
            continue
        if event.request:
            event_model = event.request.get("model", "")
            if model_lower in str(event_model).lower():
                return True
    return False


def _session_has_errors(
    session: Session,
    events: list[Event],
    function_events: list[FunctionEvent],
) -> bool:
    """Check if a session has any errors."""
    for event in events:
        if event.session_id == session.id and event.error:
            return True
    for event in function_events:
        if event.session_id == session.id and event.error:
            return True
    return False


def _session_has_function(
    session: Session,
    function_events: list[FunctionEvent],
    function_name: str,
) -> bool:
    """Check if a session has calls to the specified function."""
    name_lower = function_name.lower()
    for event in function_events:
        if event.session_id != session.id:
            continue
        if event.name and name_lower in event.name.lower():
            return True
        if event.module and name_lower in event.module.lower():
            return True
    return False


def _eval_is_failed(evaluation: dict) -> bool:
    """Check if an evaluation result indicates failure."""
    if not isinstance(evaluation, dict):
        return False
    # Check common patterns for failed evaluations
    if evaluation.get("passed") is False:
        return True
    if evaluation.get("result") is False:
        return True
    if str(evaluation.get("status", "")).lower() in ("failed", "fail", "error"):
        return True
    if evaluation.get("success") is False:
        return True
    return False


def _session_has_failed_evals(
    session: Session,
    events: list[Event],
    function_events: list[FunctionEvent],
) -> bool:
    """Check if a session has any failed evaluations."""
    for event in events:
        if event.session_id != session.id:
            continue
        for evaluation in event.evaluations:
            if _eval_is_failed(evaluation):
                return True
    for event in function_events:
        if event.session_id != session.id:
            continue
        for evaluation in event.evaluations:
            if _eval_is_failed(evaluation):
                return True
    return False


def _filter_sessions(
    response: SessionsResponse,
    query: str | None = None,
    labels: list[tuple[str, str]] | None = None,
    provider: str | None = None,
    model: str | None = None,
    function: str | None = None,
    after: float | None = None,
    before: float | None = None,
    has_errors: bool = False,
    evals_failed: bool = False,
) -> SessionsResponse:
    """Filter sessions based on criteria."""
    filtered_sessions = []

    for session in response.sessions:
        # Text query filter
        if query and not _session_matches_query(session, query):
            continue

        # Labels filter
        if labels and not _session_matches_labels(session, labels):
            continue

        # Provider filter
        if provider and not _session_has_provider(
            session, response.events, response.function_events, provider
        ):
            continue

        # Model filter
        if model and not _session_has_model(session, response.events, model):
            continue

        # Function filter
        if function and not _session_has_function(session, response.function_events, function):
            continue

        # Date range filters
        if after and session.started_at < after:
            continue
        if before and session.started_at > before:
            continue

        # Errors filter
        if has_errors and not _session_has_errors(
            session, response.events, response.function_events
        ):
            continue

        # Failed evaluations filter
        if evals_failed and not _session_has_failed_evals(
            session, response.events, response.function_events
        ):
            continue

        filtered_sessions.append(session)

    # Filter events to only include those from matching sessions
    session_ids = {s.id for s in filtered_sessions}
    filtered_events = [e for e in response.events if e.session_id in session_ids]
    filtered_function_events = [e for e in response.function_events if e.session_id in session_ids]

    return SessionsResponse(
        sessions=filtered_sessions,
        events=filtered_events,
        function_events=filtered_function_events,
        trace_tree=response.trace_tree,
        enh_prompt_traces=response.enh_prompt_traces,
        generated_at=response.generated_at,
        version=response.version,
    )


def _print_search_results(
    response: SessionsResponse,
    query: str | None = None,
) -> None:
    """Print search results with highlighting."""
    if not response.sessions:
        console.print("[yellow]No sessions match your search criteria.[/yellow]")
        return

    table = Table(
        title=f"Search Results ({len(response.sessions)} sessions)",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Started", style="green")
    table.add_column("Duration", style="yellow", justify="right")
    table.add_column("Events", justify="right")
    table.add_column("Errors", justify="right")
    table.add_column("Labels", style="dim")

    # Count events and errors per session
    event_counts: dict[str, int] = {}
    error_counts: dict[str, int] = {}
    for event in response.events:
        event_counts[event.session_id] = event_counts.get(event.session_id, 0) + 1
        if event.error:
            error_counts[event.session_id] = error_counts.get(event.session_id, 0) + 1
    for event in response.function_events:
        event_counts[event.session_id] = event_counts.get(event.session_id, 0) + 1
        if event.error:
            error_counts[event.session_id] = error_counts.get(event.session_id, 0) + 1

    for session in response.sessions:
        # Calculate duration
        duration = ""
        if session.ended_at and session.started_at:
            duration_ms = (session.ended_at - session.started_at) * 1000
            duration = _format_duration(duration_ms)

        # Format labels
        labels = ", ".join(f"{k}={v}" for k, v in session.labels.items()) if session.labels else ""

        # Format name with highlighting if query matches
        name = session.name
        if query and query.lower() in name.lower():
            # Highlight matching portion
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            name = pattern.sub(f"[bold yellow]{query}[/bold yellow]", name)

        # Format errors column
        errors = error_counts.get(session.id, 0)
        errors_str = str(errors) if errors == 0 else f"[red]{errors}[/red]"

        table.add_row(
            session.id[:8] + "...",
            name,
            _format_timestamp(session.started_at),
            duration,
            str(event_counts.get(session.id, 0)),
            errors_str,
            labels[:30] + "..." if len(labels) > 30 else labels,
        )

    console.print(table)


@app.command("search")
def search_sessions(
    query: str | None = typer.Argument(
        None,
        help="Search query (matches session name, ID, labels, or metadata)",
    ),
    label: list[str] | None = typer.Option(
        None,
        "--label",
        "-l",
        help="Filter by label (format: key=value, can specify multiple)",
    ),
    provider: str | None = typer.Option(
        None,
        "--provider",
        "-p",
        help="Filter by provider (e.g., openai, anthropic)",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Filter by model name (e.g., gpt-4, claude-3)",
    ),
    function: str | None = typer.Option(
        None,
        "--function",
        "-f",
        help="Filter by function name",
    ),
    after: str | None = typer.Option(
        None,
        "--after",
        help="Filter sessions started after date (YYYY-MM-DD)",
    ),
    before: str | None = typer.Option(
        None,
        "--before",
        help="Filter sessions started before date (YYYY-MM-DD)",
    ),
    has_errors: bool = typer.Option(
        False,
        "--has-errors",
        "--errors",
        help="Only show sessions with errors",
    ),
    evals_failed: bool = typer.Option(
        False,
        "--evals-failed",
        "--failed-evals",
        help="Only show sessions with failed evaluations",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table or json",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        "-n",
        help="Maximum number of sessions to display",
    ),
    ids_only: bool = typer.Option(
        False,
        "--ids",
        help="Only print session IDs (one per line)",
    ),
):
    """Search and filter sessions.

    Examples:

        shepherd sessions search "my-agent"

        shepherd sessions search --label env=production

        shepherd sessions search --provider openai --model gpt-4

        shepherd sessions search --after 2025-12-01 --has-errors

        shepherd sessions search --evals-failed

        shepherd sessions search --function process_data -l user=alice
    """
    config = load_config()
    output_format = output or config.cli.output_format

    # Parse labels
    parsed_labels: list[tuple[str, str]] = []
    if label:
        for lbl in label:
            parsed_labels.append(_parse_label(lbl))

    # Parse dates
    after_ts = _parse_date(after) if after else None
    before_ts = _parse_date(before) if before else None

    try:
        with _get_client() as client:
            response = client.list_sessions()

            # Apply filters
            filtered = _filter_sessions(
                response,
                query=query,
                labels=parsed_labels if parsed_labels else None,
                provider=provider,
                model=model,
                function=function,
                after=after_ts,
                before=before_ts,
                has_errors=has_errors,
                evals_failed=evals_failed,
            )

            # Apply limit
            if limit and filtered.sessions:
                filtered.sessions = filtered.sessions[:limit]

            # Output
            if ids_only:
                for session in filtered.sessions:
                    console.print(session.id)
            elif output_format == "json":
                _print_sessions_json(filtered)
            else:
                _print_search_results(filtered, query)

    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise typer.Exit(1)
    except AIOBSError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
