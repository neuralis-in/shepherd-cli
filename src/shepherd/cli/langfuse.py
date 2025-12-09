"""Langfuse CLI commands for traces and sessions."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from shepherd.config import (
    get_langfuse_host,
    get_langfuse_public_key,
    get_langfuse_secret_key,
    load_config,
)
from shepherd.models.langfuse import (
    LangfuseObservation,
    LangfuseSession,
    LangfuseSessionsResponse,
    LangfuseTrace,
    LangfuseTracesResponse,
)
from shepherd.providers.langfuse import (
    AuthenticationError,
    LangfuseClient,
    LangfuseError,
    NotFoundError,
)

# Create main langfuse app
app = typer.Typer(help="Langfuse traces and sessions")

# Subcommands
traces_app = typer.Typer(help="List and inspect Langfuse traces")
sessions_app = typer.Typer(help="List and inspect Langfuse sessions")

app.add_typer(traces_app, name="traces")
app.add_typer(sessions_app, name="sessions")

console = Console()


def _format_timestamp(ts: str) -> str:
    """Format an ISO timestamp to human-readable string."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return str(ts) if ts else "-"


def _format_duration(seconds: float | None) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds is None:
        return "-"
    ms = seconds * 1000
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms / 1000:.1f}s"
    else:
        return f"{ms / 60000:.1f}m"


def _format_duration_ms(ms: float | None) -> str:
    """Format duration in milliseconds to human-readable string."""
    if ms is None:
        return "-"
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms / 1000:.1f}s"
    else:
        return f"{ms / 60000:.1f}m"


def _format_cost(cost: float | None) -> str:
    """Format cost to human-readable string."""
    if cost is None or cost == 0:
        return "-"
    if cost < 0.01:
        return f"${cost:.4f}"
    return f"${cost:.2f}"


def _format_tokens(tokens: int | None) -> str:
    """Format token count."""
    if tokens is None or tokens == 0:
        return "-"
    if tokens >= 1000:
        return f"{tokens / 1000:.1f}k"
    return str(tokens)


def _print_llm_messages(messages: Any) -> None:
    """Print LLM input messages in a readable format."""
    if not messages:
        return
    
    # Handle list of messages (chat format)
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                
                # Color based on role
                role_color = {
                    "system": "cyan",
                    "user": "green",
                    "assistant": "yellow",
                    "function": "magenta",
                    "tool": "magenta",
                }.get(role, "white")
                
                # Truncate long content
                if isinstance(content, str):
                    display_content = content[:500] + "..." if len(content) > 500 else content
                elif isinstance(content, list):
                    # Handle content blocks (like images)
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                    display_content = " ".join(text_parts)
                    if len(display_content) > 500:
                        display_content = display_content[:500] + "..."
                else:
                    display_content = str(content)[:500]
                
                console.print(Panel(
                    display_content,
                    title=f"[bold {role_color}]{role}[/bold {role_color}]",
                    expand=False,
                    border_style="dim",
                ))
    elif isinstance(messages, dict):
        # Single message
        console.print(Panel(
            json.dumps(messages, indent=2, default=str)[:500],
            expand=False,
            border_style="dim",
        ))
    else:
        # String or other
        console.print(Panel(str(messages)[:500], expand=False, border_style="dim"))


def _print_llm_output(output: Any) -> None:
    """Print LLM output in a readable format."""
    if not output:
        return
    
    if isinstance(output, dict):
        # Check for assistant message format
        role = output.get("role", "")
        content = output.get("content", "")
        
        if role == "assistant" and content:
            display_content = content[:800] + "..." if len(content) > 800 else content
            console.print(Panel(
                display_content,
                title="[bold yellow]assistant[/bold yellow]",
                expand=False,
                border_style="dim",
            ))
            
            # Check for tool calls
            tool_calls = output.get("tool_calls", [])
            if tool_calls:
                console.print("[dim]Tool calls:[/dim]")
                for tc in tool_calls[:3]:
                    if isinstance(tc, dict):
                        func = tc.get("function", {})
                        console.print(f"  • {func.get('name', 'unknown')}")
        else:
            # Generic dict output
            output_str = json.dumps(output, indent=2, default=str)
            if len(output_str) > 800:
                output_str = output_str[:800] + "..."
            console.print(Panel(output_str, expand=False, border_style="dim"))
    elif isinstance(output, str):
        display_content = output[:800] + "..." if len(output) > 800 else output
        console.print(Panel(display_content, expand=False, border_style="dim"))
    else:
        console.print(Panel(str(output)[:800], expand=False, border_style="dim"))


def _get_client() -> LangfuseClient:
    """Get an authenticated Langfuse client."""
    public_key = get_langfuse_public_key()
    secret_key = get_langfuse_secret_key()

    if not public_key or not secret_key:
        console.print("[red]Langfuse API keys not configured.[/red]")
        console.print("Run [bold]shepherd config init[/bold] to set up your keys.")
        console.print(
            "Or set [bold]LANGFUSE_PUBLIC_KEY[/bold] and [bold]LANGFUSE_SECRET_KEY[/bold] environment variables."
        )
        raise typer.Exit(1)

    host = get_langfuse_host()
    return LangfuseClient(public_key=public_key, secret_key=secret_key, host=host)


# ============================================================================
# Traces Commands
# ============================================================================


def _print_traces_table(response: LangfuseTracesResponse) -> None:
    """Print traces as a rich table."""
    if not response.data:
        console.print("[yellow]No traces found.[/yellow]")
        return

    table = Table(title="Traces", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Timestamp", style="green")
    table.add_column("Latency", style="yellow", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("User", style="dim")
    table.add_column("Tags", style="dim")

    for trace in response.data:
        tags = ", ".join(trace.tags[:3]) if trace.tags else ""
        if len(trace.tags) > 3:
            tags += "..."

        table.add_row(
            trace.id[:12] + "...",
            trace.name or "-",
            _format_timestamp(trace.timestamp),
            _format_duration(trace.latency),
            _format_cost(trace.total_cost),
            (trace.user_id[:12] + "...") if trace.user_id and len(trace.user_id) > 12 else trace.user_id or "-",
            tags,
        )

    console.print(table)

    # Show pagination info
    meta = response.meta
    if meta:
        total = meta.get("totalItems", len(response.data))
        page = meta.get("page", 1)
        total_pages = meta.get("totalPages", 1)
        console.print(f"\n[dim]Page {page}/{total_pages} ({total} total traces)[/dim]")


def _print_traces_json(response: LangfuseTracesResponse) -> None:
    """Print traces as JSON."""
    output = {
        "traces": [t.model_dump(by_alias=True) for t in response.data],
        "meta": response.meta,
    }
    console.print_json(json.dumps(output, indent=2, default=str))


def _build_observation_tree(observations: list[str | LangfuseObservation], tree: Tree) -> None:
    """Build a rich tree from observations.
    
    Observations can be either:
    - Full LangfuseObservation objects (from get_trace endpoint)
    - String IDs (from list_traces endpoint)
    """
    # Filter to only full observation objects (not string IDs)
    full_observations = [o for o in observations if isinstance(o, LangfuseObservation)]
    
    if not full_observations:
        # If we only have IDs, just show them as a list
        for obs in observations:
            if isinstance(obs, str):
                tree.add(f"[dim]{obs}[/dim]")
        return
    
    # Build parent-child relationships
    obs_by_id: dict[str, LangfuseObservation] = {o.id: o for o in full_observations}
    children: dict[str | None, list[LangfuseObservation]] = {None: []}

    for obs in full_observations:
        parent_id = obs.parent_observation_id
        if parent_id not in children:
            children[parent_id] = []
        children[parent_id].append(obs)

    def add_node(obs: LangfuseObservation, parent_tree: Tree) -> None:
        # Build label based on type
        type_color = {
            "GENERATION": "magenta",
            "SPAN": "blue",
            "EVENT": "green",
        }.get(obs.type, "white")

        if obs.type == "GENERATION":
            # For generations, show model prominently
            label = f"[bold {type_color}]{obs.model or 'LLM'}[/bold {type_color}]"
            if obs.name and obs.name != "OpenAI-generation":
                label += f" ({obs.name})"
        else:
            # For spans/events, show name
            label = f"[bold {type_color}]{obs.type.lower()}[/bold {type_color}]"
            if obs.name:
                label += f" {obs.name}"
        
        # Add latency (in milliseconds)
        if obs.latency:
            label += f" [dim]{_format_duration_ms(obs.latency)}[/dim]"
        
        # Add token info for generations
        if obs.type == "GENERATION" and obs.usage:
            total_tokens = obs.usage.get("total") or obs.usage.get("totalTokens", 0)
            if total_tokens:
                label += f" [yellow]{total_tokens} tok[/yellow]"

        branch = parent_tree.add(label)

        # Add children
        for child in children.get(obs.id, []):
            add_node(child, branch)

    # Add root observations (no parent)
    for obs in children.get(None, []):
        add_node(obs, tree)


def _print_trace_detail(trace: LangfuseTrace) -> None:
    """Print detailed trace information."""
    # Trace header
    header = f"""[bold]Trace:[/bold]   {trace.id}
[bold]Name:[/bold]    {trace.name or "-"}
[bold]Time:[/bold]    {_format_timestamp(trace.timestamp)}
[bold]Latency:[/bold] {_format_duration(trace.latency)}
[bold]Cost:[/bold]    {_format_cost(trace.total_cost)}"""

    if trace.user_id:
        header += f"\n[bold]User:[/bold]    {trace.user_id}"
    if trace.session_id:
        header += f"\n[bold]Session:[/bold] {trace.session_id}"
    if trace.tags:
        header += f"\n[bold]Tags:[/bold]    {', '.join(trace.tags)}"
    if trace.release:
        header += f"\n[bold]Release:[/bold] {trace.release}"
    if trace.version:
        header += f"\n[bold]Version:[/bold] {trace.version}"

    console.print(Panel(header, title="[bold]Trace Info[/bold]", expand=False))

    # Observations tree
    if trace.observations:
        # Filter to only full observation objects
        full_observations = [o for o in trace.observations if isinstance(o, LangfuseObservation)]
        
        console.print("\n[bold]Trace Tree:[/bold]\n")
        tree = Tree(f"[bold]{trace.name or trace.id}[/bold]")
        _build_observation_tree(trace.observations, tree)
        console.print(tree)

        # LLM Calls table (only GENERATION type)
        if full_observations:
            generations = [o for o in full_observations if o.type == "GENERATION"]
            
            if generations:
                console.print("\n[bold]LLM Calls:[/bold]\n")
                llm_table = Table(show_header=True, header_style="bold")
                llm_table.add_column("Model", style="cyan")
                llm_table.add_column("Duration", justify="right")
                llm_table.add_column("In", justify="right", style="green")
                llm_table.add_column("Out", justify="right", style="yellow")
                llm_table.add_column("Total", justify="right")
                llm_table.add_column("Cost", justify="right")

                for obs in generations[:10]:
                    in_tokens = "-"
                    out_tokens = "-"
                    total_tokens = "-"
                    if obs.usage:
                        in_tok = obs.usage.get("input") or obs.usage.get("inputTokens", 0)
                        out_tok = obs.usage.get("output") or obs.usage.get("outputTokens", 0)
                        total_tok = obs.usage.get("total") or obs.usage.get("totalTokens", 0)
                        if in_tok:
                            in_tokens = str(in_tok)
                        if out_tok:
                            out_tokens = str(out_tok)
                        if total_tok:
                            total_tokens = str(total_tok)

                    llm_table.add_row(
                        obs.model or "-",
                        _format_duration_ms(obs.latency),
                        in_tokens,
                        out_tokens,
                        total_tokens,
                        _format_cost(obs.calculated_total_cost),
                    )

                console.print(llm_table)

                if len(generations) > 10:
                    console.print(f"[dim]... and {len(generations) - 10} more LLM calls[/dim]")

                # Show input/output for first generation
                first_gen = generations[0]
                if first_gen.input:
                    console.print("\n[bold]First LLM Call - Input:[/bold]")
                    _print_llm_messages(first_gen.input)
                
                if first_gen.output:
                    console.print("\n[bold]First LLM Call - Output:[/bold]")
                    _print_llm_output(first_gen.output)
        else:
            # Just show count of observation IDs
            console.print(f"\n[dim]{len(trace.observations)} observation IDs (use 'traces get' for details)[/dim]")

    # Trace-level Input/Output preview (if different from LLM calls)
    if trace.input and not trace.observations:
        console.print("\n[bold]Input:[/bold]")
        input_str = json.dumps(trace.input, indent=2, default=str) if isinstance(trace.input, (dict, list)) else str(trace.input)
        if len(input_str) > 500:
            input_str = input_str[:500] + "..."
        console.print(Panel(input_str, expand=False, border_style="dim"))

    if trace.output:
        console.print("\n[bold]Output:[/bold]")
        output_str = json.dumps(trace.output, indent=2, default=str) if isinstance(trace.output, (dict, list)) else str(trace.output)
        if len(output_str) > 500:
            output_str = output_str[:500] + "..."
        console.print(Panel(output_str, expand=False, border_style="dim"))


@traces_app.command("list")
def list_traces(
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table or json (overrides config)",
    ),
    limit: int = typer.Option(
        50,
        "--limit",
        "-n",
        help="Maximum number of traces to display",
    ),
    page: int = typer.Option(
        1,
        "--page",
        "-p",
        help="Page number",
    ),
    name: str = typer.Option(
        None,
        "--name",
        help="Filter by trace name",
    ),
    user_id: str = typer.Option(
        None,
        "--user-id",
        "-u",
        help="Filter by user ID",
    ),
    session_id: str = typer.Option(
        None,
        "--session-id",
        "-s",
        help="Filter by session ID",
    ),
    tags: list[str] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Filter by tag (can specify multiple)",
    ),
    from_timestamp: str = typer.Option(
        None,
        "--from",
        help="Filter traces after this timestamp (ISO 8601 or YYYY-MM-DD)",
    ),
    to_timestamp: str = typer.Option(
        None,
        "--to",
        help="Filter traces before this timestamp (ISO 8601 or YYYY-MM-DD)",
    ),
    ids_only: bool = typer.Option(
        False,
        "--ids",
        help="Only print trace IDs (one per line)",
    ),
):
    """List Langfuse traces with optional filters."""
    config = load_config()
    output_format = output or config.cli.output_format

    try:
        with _get_client() as client:
            response = client.list_traces(
                limit=limit,
                page=page,
                name=name,
                user_id=user_id,
                session_id=session_id,
                tags=tags,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
            )

            if ids_only:
                for trace in response.data:
                    console.print(trace.id)
            elif output_format == "json":
                _print_traces_json(response)
            else:
                _print_traces_table(response)

    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise typer.Exit(1)
    except LangfuseError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@traces_app.command("get")
def get_trace(
    trace_id: str = typer.Argument(..., help="Trace ID to fetch"),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table or json (overrides config)",
    ),
):
    """Get details for a specific Langfuse trace."""
    config = load_config()
    output_format = output or config.cli.output_format

    try:
        with _get_client() as client:
            trace = client.get_trace(trace_id)

            if output_format == "json":
                console.print_json(trace.model_dump_json(indent=2, by_alias=True))
            else:
                _print_trace_detail(trace)

    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise typer.Exit(1)
    except NotFoundError as e:
        console.print(f"[red]Trace not found:[/red] {e}")
        raise typer.Exit(1)
    except LangfuseError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# Sessions Commands
# ============================================================================


def _print_sessions_table(response: LangfuseSessionsResponse) -> None:
    """Print sessions as a rich table."""
    if not response.data:
        console.print("[yellow]No sessions found.[/yellow]")
        return

    table = Table(title="Sessions", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Created", style="green")
    table.add_column("Traces", justify="right")
    table.add_column("Duration", style="yellow", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Users", style="dim")

    for session in response.data:
        users = ", ".join(session.user_ids[:2]) if session.user_ids else "-"
        if len(session.user_ids) > 2:
            users += "..."

        table.add_row(
            session.id[:20] + "..." if len(session.id) > 20 else session.id,
            _format_timestamp(session.created_at),
            str(session.count_traces),
            _format_duration(session.session_duration / 1000 if session.session_duration else None),
            _format_tokens(session.total_tokens),
            _format_cost(session.total_cost),
            users,
        )

    console.print(table)

    # Show pagination info
    meta = response.meta
    if meta:
        total = meta.get("totalItems", len(response.data))
        page = meta.get("page", 1)
        total_pages = meta.get("totalPages", 1)
        console.print(f"\n[dim]Page {page}/{total_pages} ({total} total sessions)[/dim]")


def _print_sessions_json(response: LangfuseSessionsResponse) -> None:
    """Print sessions as JSON."""
    output = {
        "sessions": [s.model_dump(by_alias=True) for s in response.data],
        "meta": response.meta,
    }
    console.print_json(json.dumps(output, indent=2, default=str))


def _print_session_detail(session: LangfuseSession) -> None:
    """Print detailed session information."""
    # Session header
    header = f"""[bold]Session:[/bold]  {session.id}
[bold]Created:[/bold]  {_format_timestamp(session.created_at)}
[bold]Traces:[/bold]   {session.count_traces}
[bold]Duration:[/bold] {_format_duration(session.session_duration / 1000 if session.session_duration else None)}"""

    if session.user_ids:
        header += f"\n[bold]Users:[/bold]    {', '.join(session.user_ids)}"

    # Token and cost breakdown
    header += f"""

[bold]Token Usage:[/bold]
  Input:  {_format_tokens(session.input_tokens)}
  Output: {_format_tokens(session.output_tokens)}
  Total:  {_format_tokens(session.total_tokens)}

[bold]Cost:[/bold]
  Input:  {_format_cost(session.input_cost)}
  Output: {_format_cost(session.output_cost)}
  Total:  {_format_cost(session.total_cost)}"""

    console.print(Panel(header, title="[bold]Session Info[/bold]", expand=False))

    # Show traces if available
    if session.traces:
        console.print("\n[bold]Traces:[/bold]\n")
        trace_table = Table(show_header=True, header_style="bold")
        trace_table.add_column("ID", style="dim")
        trace_table.add_column("Name")
        trace_table.add_column("Timestamp", style="green")
        trace_table.add_column("Latency", justify="right")
        trace_table.add_column("Cost", justify="right")

        for trace in session.traces[:10]:
            trace_table.add_row(
                trace.id[:12] + "...",
                trace.name or "-",
                _format_timestamp(trace.timestamp),
                _format_duration(trace.latency),
                _format_cost(trace.total_cost),
            )

        console.print(trace_table)

        if len(session.traces) > 10:
            console.print(f"[dim]... and {len(session.traces) - 10} more traces[/dim]")


@sessions_app.command("list")
def list_sessions(
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table or json (overrides config)",
    ),
    limit: int = typer.Option(
        50,
        "--limit",
        "-n",
        help="Maximum number of sessions to display",
    ),
    page: int = typer.Option(
        1,
        "--page",
        "-p",
        help="Page number",
    ),
    from_timestamp: str = typer.Option(
        None,
        "--from",
        help="Filter sessions after this timestamp (ISO 8601 or YYYY-MM-DD)",
    ),
    to_timestamp: str = typer.Option(
        None,
        "--to",
        help="Filter sessions before this timestamp (ISO 8601 or YYYY-MM-DD)",
    ),
    ids_only: bool = typer.Option(
        False,
        "--ids",
        help="Only print session IDs (one per line)",
    ),
):
    """List Langfuse sessions."""
    config = load_config()
    output_format = output or config.cli.output_format

    try:
        with _get_client() as client:
            response = client.list_sessions(
                limit=limit,
                page=page,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
            )

            if ids_only:
                for session in response.data:
                    console.print(session.id)
            elif output_format == "json":
                _print_sessions_json(response)
            else:
                _print_sessions_table(response)

    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise typer.Exit(1)
    except LangfuseError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@sessions_app.command("get")
def get_session(
    session_id: str = typer.Argument(..., help="Session ID to fetch"),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table or json (overrides config)",
    ),
):
    """Get details for a specific Langfuse session."""
    config = load_config()
    output_format = output or config.cli.output_format

    try:
        with _get_client() as client:
            session = client.get_session(session_id)

            if output_format == "json":
                console.print_json(session.model_dump_json(indent=2, by_alias=True))
            else:
                _print_session_detail(session)

    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise typer.Exit(1)
    except NotFoundError as e:
        console.print(f"[red]Session not found:[/red] {e}")
        raise typer.Exit(1)
    except LangfuseError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

