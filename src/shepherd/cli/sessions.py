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


class SessionDiff:
    """Represents the diff between two sessions."""

    def __init__(
        self,
        session1: SessionsResponse,
        session2: SessionsResponse,
    ):
        self.session1 = session1
        self.session2 = session2
        self.s1 = session1.sessions[0] if session1.sessions else None
        self.s2 = session2.sessions[0] if session2.sessions else None

    def _calc_total_tokens(self, events: list[Event]) -> dict[str, int]:
        """Calculate total tokens from events."""
        total = {"input": 0, "output": 0, "total": 0}
        for event in events:
            if event.response and "usage" in event.response:
                usage = event.response["usage"]
                total["input"] += usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
                total["output"] += usage.get("completion_tokens", 0) or usage.get(
                    "output_tokens", 0
                )
                total["total"] += usage.get("total_tokens", 0)
        return total

    def _calc_avg_latency(self, events: list[Event]) -> float:
        """Calculate average latency from events."""
        if not events:
            return 0.0
        return sum(e.duration_ms for e in events) / len(events)

    def _count_errors(self, events: list[Event], function_events: list[FunctionEvent]) -> int:
        """Count errors in events."""
        count = sum(1 for e in events if e.error)
        count += sum(1 for e in function_events if e.error)
        return count

    def _get_provider_distribution(self, events: list[Event]) -> dict[str, int]:
        """Get provider distribution from events."""
        dist: dict[str, int] = {}
        for event in events:
            dist[event.provider] = dist.get(event.provider, 0) + 1
        return dist

    def _get_model_distribution(self, events: list[Event]) -> dict[str, int]:
        """Get model distribution from events."""
        dist: dict[str, int] = {}
        for event in events:
            if event.request:
                model = event.request.get("model", "unknown")
                dist[model] = dist.get(model, 0) + 1
        return dist

    def _get_unique_functions(self, function_events: list[FunctionEvent]) -> set[str]:
        """Get unique function names."""
        return {e.name for e in function_events if e.name}

    def _get_function_counts(self, function_events: list[FunctionEvent]) -> dict[str, int]:
        """Get function call counts."""
        counts: dict[str, int] = {}
        for event in function_events:
            if event.name:
                counts[event.name] = counts.get(event.name, 0) + 1
        return counts

    def _count_evaluations(
        self, events: list[Event], function_events: list[FunctionEvent]
    ) -> dict[str, int]:
        """Count evaluation results."""
        result = {"total": 0, "passed": 0, "failed": 0}
        all_evals = []
        for event in events:
            all_evals.extend(event.evaluations)
        for event in function_events:
            all_evals.extend(event.evaluations)

        result["total"] = len(all_evals)
        for ev in all_evals:
            if _eval_is_failed(ev):
                result["failed"] += 1
            else:
                result["passed"] += 1
        return result

    def _get_trace_depth(self, nodes: list[TraceNode]) -> int:
        """Get maximum trace depth."""
        if not nodes:
            return 0

        def _depth(node: TraceNode) -> int:
            if not node.children:
                return 1
            return 1 + max(_depth(c) for c in node.children)

        return max(_depth(n) for n in nodes)

    def _get_errors_list(
        self, events: list[Event], function_events: list[FunctionEvent]
    ) -> list[str]:
        """Get list of error messages."""
        errors = []
        for event in events:
            if event.error:
                errors.append(f"[{event.provider}/{event.api}] {event.error}")
        for event in function_events:
            if event.error:
                errors.append(f"[fn:{event.name}] {event.error}")
        return errors

    def _extract_system_prompts(self, events: list[Event]) -> list[dict]:
        """Extract system prompts from events."""
        prompts = []
        for i, event in enumerate(events):
            if not event.request:
                continue
            messages = event.request.get("messages", [])
            system_content = None

            # Check for system message in messages array
            for msg in messages:
                if isinstance(msg, dict) and msg.get("role") == "system":
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        # Handle content blocks (e.g., Anthropic format)
                        content = " ".join(
                            block.get("text", "") for block in content if isinstance(block, dict)
                        )
                    system_content = content
                    break

            # Check for top-level system parameter (Anthropic style)
            if not system_content:
                system_content = event.request.get("system", "")

            if system_content:
                prompts.append(
                    {
                        "index": i,
                        "provider": event.provider,
                        "model": event.request.get("model", "unknown"),
                        "content": system_content[:500] + "..."
                        if len(system_content) > 500
                        else system_content,
                        "full_length": len(system_content),
                    }
                )
        return prompts

    def _extract_request_params(self, events: list[Event]) -> list[dict]:
        """Extract request parameters from events."""
        params_list = []
        for i, event in enumerate(events):
            if not event.request:
                continue

            params = {
                "index": i,
                "provider": event.provider,
                "api": event.api,
                "model": event.request.get("model", "unknown"),
            }

            # Common parameters across providers
            param_keys = [
                "temperature",
                "max_tokens",
                "top_p",
                "top_k",
                "frequency_penalty",
                "presence_penalty",
                "stop",
                "stream",
                "tools",
                "tool_choice",
                "response_format",
            ]

            for key in param_keys:
                if key in event.request:
                    value = event.request[key]
                    # Summarize tools if present
                    if key == "tools" and isinstance(value, list):
                        params[key] = [
                            t.get("function", {}).get("name", "unknown")
                            if isinstance(t, dict)
                            else str(t)
                            for t in value
                        ]
                    else:
                        params[key] = value

            # Extract user message preview
            messages = event.request.get("messages", [])
            user_msgs = [m for m in messages if isinstance(m, dict) and m.get("role") == "user"]
            if user_msgs:
                last_user = user_msgs[-1]
                content = last_user.get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        block.get("text", "")
                        for block in content
                        if isinstance(block, dict) and block.get("type") == "text"
                    )
                params["user_message_preview"] = (
                    content[:200] + "..." if len(str(content)) > 200 else content
                )

            params_list.append(params)
        return params_list

    def _extract_responses(self, events: list[Event]) -> list[dict]:
        """Extract response content from events."""
        responses = []
        for i, event in enumerate(events):
            if not event.response:
                continue

            model = event.response.get("model")
            if not model and event.request:
                model = event.request.get("model", "unknown")
            resp = {
                "index": i,
                "provider": event.provider,
                "model": model or "unknown",
                "duration_ms": event.duration_ms,
            }

            # Extract usage info
            usage = event.response.get("usage", {})
            if usage:
                resp["tokens"] = {
                    "input": usage.get("prompt_tokens") or usage.get("input_tokens", 0),
                    "output": usage.get("completion_tokens") or usage.get("output_tokens", 0),
                    "total": usage.get("total_tokens", 0),
                }

            # Extract response content - handle different formats
            content = None

            # OpenAI format
            choices = event.response.get("choices", [])
            if choices and isinstance(choices, list):
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    message = first_choice.get("message", {})
                    content = message.get("content", "")
                    # Check for tool calls
                    tool_calls = message.get("tool_calls", [])
                    if tool_calls:
                        resp["tool_calls"] = [
                            {
                                "name": tc.get("function", {}).get("name", "unknown"),
                                "arguments_preview": str(
                                    tc.get("function", {}).get("arguments", "")
                                )[:100],
                            }
                            for tc in tool_calls
                            if isinstance(tc, dict)
                        ]

            # Anthropic format
            if not content:
                content_blocks = event.response.get("content", [])
                if isinstance(content_blocks, list):
                    text_blocks = [
                        b.get("text", "")
                        for b in content_blocks
                        if isinstance(b, dict) and b.get("type") == "text"
                    ]
                    content = " ".join(text_blocks)
                    # Check for tool use
                    tool_uses = [
                        b
                        for b in content_blocks
                        if isinstance(b, dict) and b.get("type") == "tool_use"
                    ]
                    if tool_uses:
                        resp["tool_calls"] = [
                            {
                                "name": tu.get("name", "unknown"),
                                "arguments_preview": str(tu.get("input", ""))[:100],
                            }
                            for tu in tool_uses
                        ]
                elif isinstance(content_blocks, str):
                    content = content_blocks

            # Direct text field
            if not content:
                content = event.response.get("text", "")

            if content:
                resp["content_preview"] = (
                    content[:300] + "..." if len(str(content)) > 300 else content
                )
                resp["content_length"] = len(str(content))

            # Stop reason
            stop_reason = event.response.get("stop_reason") or (
                choices[0].get("finish_reason") if choices else None
            )
            if stop_reason:
                resp["stop_reason"] = stop_reason

            responses.append(resp)
        return responses

    def _compare_system_prompts(self, prompts1: list[dict], prompts2: list[dict]) -> dict:
        """Compare system prompts between sessions."""
        # Get unique prompts by content
        set1 = {p["content"] for p in prompts1}
        set2 = {p["content"] for p in prompts2}

        return {
            "session1": prompts1,
            "session2": prompts2,
            "unique_to_session1": list(set1 - set2),
            "unique_to_session2": list(set2 - set1),
            "common": list(set1 & set2),
            "changed": len(set1) != len(set2) or set1 != set2,
        }

    def _compare_request_params(self, params1: list[dict], params2: list[dict]) -> dict:
        """Compare request parameters between sessions."""

        # Aggregate parameters
        def aggregate_params(params_list: list[dict]) -> dict:
            agg: dict = {
                "temperatures": [],
                "max_tokens": [],
                "models": [],
                "tools_used": set(),
                "stream_count": 0,
            }
            for p in params_list:
                if "temperature" in p:
                    agg["temperatures"].append(p["temperature"])
                if "max_tokens" in p:
                    agg["max_tokens"].append(p["max_tokens"])
                agg["models"].append(p.get("model", "unknown"))
                if "tools" in p:
                    agg["tools_used"].update(p["tools"])
                if p.get("stream"):
                    agg["stream_count"] += 1
            agg["tools_used"] = list(agg["tools_used"])
            return agg

        agg1 = aggregate_params(params1)
        agg2 = aggregate_params(params2)

        return {
            "session1": {
                "requests": params1,
                "summary": {
                    "avg_temperature": sum(agg1["temperatures"]) / len(agg1["temperatures"])
                    if agg1["temperatures"]
                    else None,
                    "avg_max_tokens": sum(agg1["max_tokens"]) / len(agg1["max_tokens"])
                    if agg1["max_tokens"]
                    else None,
                    "tools_used": agg1["tools_used"],
                    "streaming_requests": agg1["stream_count"],
                },
            },
            "session2": {
                "requests": params2,
                "summary": {
                    "avg_temperature": sum(agg2["temperatures"]) / len(agg2["temperatures"])
                    if agg2["temperatures"]
                    else None,
                    "avg_max_tokens": sum(agg2["max_tokens"]) / len(agg2["max_tokens"])
                    if agg2["max_tokens"]
                    else None,
                    "tools_used": agg2["tools_used"],
                    "streaming_requests": agg2["stream_count"],
                },
            },
            "tools_added": list(set(agg2["tools_used"]) - set(agg1["tools_used"])),
            "tools_removed": list(set(agg1["tools_used"]) - set(agg2["tools_used"])),
        }

    def _compare_responses(self, responses1: list[dict], responses2: list[dict]) -> dict:
        """Compare responses between sessions."""

        def summarize_responses(resp_list: list[dict]) -> dict:
            total_content_len = 0
            tool_call_count = 0
            stop_reasons: dict[str, int] = {}

            for r in resp_list:
                total_content_len += r.get("content_length", 0)
                tool_call_count += len(r.get("tool_calls", []))
                reason = r.get("stop_reason", "unknown")
                stop_reasons[reason] = stop_reasons.get(reason, 0) + 1

            return {
                "total_content_length": total_content_len,
                "avg_content_length": total_content_len / len(resp_list) if resp_list else 0,
                "tool_call_count": tool_call_count,
                "stop_reasons": stop_reasons,
            }

        summary1 = summarize_responses(responses1)
        summary2 = summarize_responses(responses2)

        return {
            "session1": {
                "responses": responses1,
                "summary": summary1,
            },
            "session2": {
                "responses": responses2,
                "summary": summary2,
            },
            "delta": {
                "avg_content_length": (
                    summary2["avg_content_length"] - summary1["avg_content_length"]
                ),
                "tool_call_count": (summary2["tool_call_count"] - summary1["tool_call_count"]),
            },
        }

    def compute(self) -> dict:
        """Compute the diff between two sessions."""
        if not self.s1 or not self.s2:
            return {}

        # Session metadata
        s1_duration = (
            (self.s1.ended_at - self.s1.started_at) * 1000
            if self.s1.ended_at and self.s1.started_at
            else 0
        )
        s2_duration = (
            (self.s2.ended_at - self.s2.started_at) * 1000
            if self.s2.ended_at and self.s2.started_at
            else 0
        )

        # Labels diff
        s1_labels = set(self.s1.labels.items())
        s2_labels = set(self.s2.labels.items())
        labels_added = dict(s2_labels - s1_labels)
        labels_removed = dict(s1_labels - s2_labels)

        # Meta diff
        s1_meta = set(self.s1.meta.items())
        s2_meta = set(self.s2.meta.items())
        meta_added = dict(s2_meta - s1_meta)
        meta_removed = dict(s1_meta - s2_meta)

        # Token calculations
        tokens1 = self._calc_total_tokens(self.session1.events)
        tokens2 = self._calc_total_tokens(self.session2.events)

        # Latency
        avg_latency1 = self._calc_avg_latency(self.session1.events)
        avg_latency2 = self._calc_avg_latency(self.session2.events)

        # Errors
        errors1 = self._count_errors(self.session1.events, self.session1.function_events)
        errors2 = self._count_errors(self.session2.events, self.session2.function_events)

        # Provider distribution
        providers1 = self._get_provider_distribution(self.session1.events)
        providers2 = self._get_provider_distribution(self.session2.events)

        # Model distribution
        models1 = self._get_model_distribution(self.session1.events)
        models2 = self._get_model_distribution(self.session2.events)

        # Function events
        fn_counts1 = self._get_function_counts(self.session1.function_events)
        fn_counts2 = self._get_function_counts(self.session2.function_events)
        fns1 = set(fn_counts1.keys())
        fns2 = set(fn_counts2.keys())

        # Avg function duration
        fn_avg_duration1 = (
            sum(e.duration_ms for e in self.session1.function_events)
            / len(self.session1.function_events)
            if self.session1.function_events
            else 0
        )
        fn_avg_duration2 = (
            sum(e.duration_ms for e in self.session2.function_events)
            / len(self.session2.function_events)
            if self.session2.function_events
            else 0
        )

        # Evaluations
        evals1 = self._count_evaluations(self.session1.events, self.session1.function_events)
        evals2 = self._count_evaluations(self.session2.events, self.session2.function_events)

        # Trace depth
        trace_depth1 = self._get_trace_depth(self.session1.trace_tree)
        trace_depth2 = self._get_trace_depth(self.session2.trace_tree)

        # Errors list
        errors_list1 = self._get_errors_list(self.session1.events, self.session1.function_events)
        errors_list2 = self._get_errors_list(self.session2.events, self.session2.function_events)

        # System prompts
        system_prompts1 = self._extract_system_prompts(self.session1.events)
        system_prompts2 = self._extract_system_prompts(self.session2.events)
        system_prompts_comparison = self._compare_system_prompts(system_prompts1, system_prompts2)

        # Request parameters
        request_params1 = self._extract_request_params(self.session1.events)
        request_params2 = self._extract_request_params(self.session2.events)
        request_params_comparison = self._compare_request_params(request_params1, request_params2)

        # Responses
        responses1 = self._extract_responses(self.session1.events)
        responses2 = self._extract_responses(self.session2.events)
        responses_comparison = self._compare_responses(responses1, responses2)

        return {
            "metadata": {
                "session1": {
                    "id": self.s1.id,
                    "name": self.s1.name,
                    "started_at": self.s1.started_at,
                    "duration_ms": s1_duration,
                    "labels": dict(self.s1.labels),
                    "meta": dict(self.s1.meta),
                },
                "session2": {
                    "id": self.s2.id,
                    "name": self.s2.name,
                    "started_at": self.s2.started_at,
                    "duration_ms": s2_duration,
                    "labels": dict(self.s2.labels),
                    "meta": dict(self.s2.meta),
                },
                "duration_delta_ms": s2_duration - s1_duration,
                "labels_added": labels_added,
                "labels_removed": labels_removed,
                "meta_added": meta_added,
                "meta_removed": meta_removed,
            },
            "llm_calls": {
                "session1": {
                    "total": len(self.session1.events),
                    "tokens": tokens1,
                    "avg_latency_ms": avg_latency1,
                    "errors": errors1,
                },
                "session2": {
                    "total": len(self.session2.events),
                    "tokens": tokens2,
                    "avg_latency_ms": avg_latency2,
                    "errors": errors2,
                },
                "delta": {
                    "total": len(self.session2.events) - len(self.session1.events),
                    "tokens": {
                        "input": tokens2["input"] - tokens1["input"],
                        "output": tokens2["output"] - tokens1["output"],
                        "total": tokens2["total"] - tokens1["total"],
                    },
                    "avg_latency_ms": avg_latency2 - avg_latency1,
                    "errors": errors2 - errors1,
                },
            },
            "providers": {
                "session1": providers1,
                "session2": providers2,
            },
            "models": {
                "session1": models1,
                "session2": models2,
            },
            "functions": {
                "session1": {
                    "total": len(self.session1.function_events),
                    "unique": len(fns1),
                    "avg_duration_ms": fn_avg_duration1,
                    "counts": fn_counts1,
                },
                "session2": {
                    "total": len(self.session2.function_events),
                    "unique": len(fns2),
                    "avg_duration_ms": fn_avg_duration2,
                    "counts": fn_counts2,
                },
                "delta": {
                    "total": len(self.session2.function_events)
                    - len(self.session1.function_events),
                    "avg_duration_ms": fn_avg_duration2 - fn_avg_duration1,
                },
                "only_in_session1": list(fns1 - fns2),
                "only_in_session2": list(fns2 - fns1),
                "in_both": list(fns1 & fns2),
            },
            "trace": {
                "session1": {
                    "depth": trace_depth1,
                    "root_nodes": len(self.session1.trace_tree),
                },
                "session2": {
                    "depth": trace_depth2,
                    "root_nodes": len(self.session2.trace_tree),
                },
            },
            "evaluations": {
                "session1": evals1,
                "session2": evals2,
                "delta": {
                    "total": evals2["total"] - evals1["total"],
                    "passed": evals2["passed"] - evals1["passed"],
                    "failed": evals2["failed"] - evals1["failed"],
                },
                "pass_rate1": evals1["passed"] / evals1["total"] if evals1["total"] > 0 else 0,
                "pass_rate2": evals2["passed"] / evals2["total"] if evals2["total"] > 0 else 0,
            },
            "errors": {
                "session1": errors_list1,
                "session2": errors_list2,
            },
            "system_prompts": system_prompts_comparison,
            "request_params": request_params_comparison,
            "responses": responses_comparison,
        }


def _format_delta(value: float, unit: str = "", precision: int = 0) -> str:
    """Format a delta value with +/- sign and color."""
    if value == 0:
        return f"[dim]0{unit}[/dim]"
    sign = "+" if value > 0 else ""
    color = "red" if value > 0 else "green"
    if precision == 0:
        return f"[{color}]{sign}{int(value)}{unit}[/{color}]"
    return f"[{color}]{sign}{value:.{precision}f}{unit}[/{color}]"


def _format_delta_inverse(value: float, unit: str = "", precision: int = 0) -> str:
    """Format delta where lower is better (latency, errors)."""
    if value == 0:
        return f"[dim]0{unit}[/dim]"
    sign = "+" if value > 0 else ""
    color = "green" if value < 0 else "red"
    if precision == 0:
        return f"[{color}]{sign}{int(value)}{unit}[/{color}]"
    return f"[{color}]{sign}{value:.{precision}f}{unit}[/{color}]"


def _print_session_diff(diff: dict) -> None:
    """Print session diff as rich tables."""
    meta = diff["metadata"]
    s1_meta = meta["session1"]
    s2_meta = meta["session2"]

    # Header panel
    s1_started = _format_timestamp(s1_meta["started_at"])
    s2_started = _format_timestamp(s2_meta["started_at"])
    header = f"""[bold]Session 1:[/bold] {s1_meta["id"][:12]}... ({s1_meta["name"]})
[bold]Session 2:[/bold] {s2_meta["id"][:12]}... ({s2_meta["name"]})
[bold]Started:[/bold]   {s1_started} → {s2_started}"""

    console.print(Panel(header, title="[bold]Session Diff[/bold]", expand=False))
    console.print()

    # Metadata comparison
    meta_table = Table(title="Metadata Comparison", show_header=True, header_style="bold cyan")
    meta_table.add_column("Field", style="bold")
    meta_table.add_column("Session 1", style="dim")
    meta_table.add_column("Session 2", style="dim")
    meta_table.add_column("Delta", justify="right")

    meta_table.add_row(
        "Duration",
        _format_duration(s1_meta["duration_ms"]),
        _format_duration(s2_meta["duration_ms"]),
        _format_delta_inverse(meta["duration_delta_ms"], "ms"),
    )

    # Labels diff
    if meta["labels_added"] or meta["labels_removed"]:
        labels_diff = []
        for k, v in meta["labels_added"].items():
            labels_diff.append(f"[green]+{k}={v}[/green]")
        for k, v in meta["labels_removed"].items():
            labels_diff.append(f"[red]-{k}={v}[/red]")
        meta_table.add_row(
            "Labels",
            ", ".join(f"{k}={v}" for k, v in s1_meta["labels"].items()) or "-",
            ", ".join(f"{k}={v}" for k, v in s2_meta["labels"].items()) or "-",
            ", ".join(labels_diff),
        )

    console.print(meta_table)
    console.print()

    # LLM Calls comparison
    llm = diff["llm_calls"]
    llm_table = Table(title="LLM Calls Summary", show_header=True, header_style="bold cyan")
    llm_table.add_column("Metric", style="bold")
    llm_table.add_column("Session 1", justify="right")
    llm_table.add_column("Session 2", justify="right")
    llm_table.add_column("Delta", justify="right")

    llm_table.add_row(
        "Total Calls",
        str(llm["session1"]["total"]),
        str(llm["session2"]["total"]),
        _format_delta(llm["delta"]["total"]),
    )
    llm_table.add_row(
        "Input Tokens",
        f"{llm['session1']['tokens']['input']:,}",
        f"{llm['session2']['tokens']['input']:,}",
        _format_delta(llm["delta"]["tokens"]["input"]),
    )
    llm_table.add_row(
        "Output Tokens",
        f"{llm['session1']['tokens']['output']:,}",
        f"{llm['session2']['tokens']['output']:,}",
        _format_delta(llm["delta"]["tokens"]["output"]),
    )
    llm_table.add_row(
        "Total Tokens",
        f"{llm['session1']['tokens']['total']:,}",
        f"{llm['session2']['tokens']['total']:,}",
        _format_delta(llm["delta"]["tokens"]["total"]),
    )
    llm_table.add_row(
        "Avg Latency",
        _format_duration(llm["session1"]["avg_latency_ms"]),
        _format_duration(llm["session2"]["avg_latency_ms"]),
        _format_delta_inverse(llm["delta"]["avg_latency_ms"], "ms", 1),
    )
    llm_table.add_row(
        "Errors",
        str(llm["session1"]["errors"]),
        str(llm["session2"]["errors"]),
        _format_delta_inverse(llm["delta"]["errors"]),
    )

    console.print(llm_table)
    console.print()

    # Provider/Model distribution
    providers = diff["providers"]
    models = diff["models"]

    if providers["session1"] or providers["session2"]:
        prov_table = Table(
            title="Provider Distribution", show_header=True, header_style="bold cyan"
        )
        prov_table.add_column("Provider", style="bold")
        prov_table.add_column("Session 1", justify="right")
        prov_table.add_column("Session 2", justify="right")
        prov_table.add_column("Delta", justify="right")

        all_providers = set(providers["session1"].keys()) | set(providers["session2"].keys())
        for prov in sorted(all_providers):
            v1 = providers["session1"].get(prov, 0)
            v2 = providers["session2"].get(prov, 0)
            prov_table.add_row(prov, str(v1), str(v2), _format_delta(v2 - v1))

        console.print(prov_table)
        console.print()

    if models["session1"] or models["session2"]:
        model_table = Table(title="Model Distribution", show_header=True, header_style="bold cyan")
        model_table.add_column("Model", style="bold")
        model_table.add_column("Session 1", justify="right")
        model_table.add_column("Session 2", justify="right")
        model_table.add_column("Delta", justify="right")

        all_models = set(models["session1"].keys()) | set(models["session2"].keys())
        for mdl in sorted(all_models):
            v1 = models["session1"].get(mdl, 0)
            v2 = models["session2"].get(mdl, 0)
            model_table.add_row(mdl, str(v1), str(v2), _format_delta(v2 - v1))

        console.print(model_table)
        console.print()

    # Functions comparison
    fns = diff["functions"]
    if fns["session1"]["total"] > 0 or fns["session2"]["total"] > 0:
        fn_table = Table(
            title="Function Events Summary", show_header=True, header_style="bold cyan"
        )
        fn_table.add_column("Metric", style="bold")
        fn_table.add_column("Session 1", justify="right")
        fn_table.add_column("Session 2", justify="right")
        fn_table.add_column("Delta", justify="right")

        fn_table.add_row(
            "Total Calls",
            str(fns["session1"]["total"]),
            str(fns["session2"]["total"]),
            _format_delta(fns["delta"]["total"]),
        )
        fn_table.add_row(
            "Unique Functions",
            str(fns["session1"]["unique"]),
            str(fns["session2"]["unique"]),
            _format_delta(fns["session2"]["unique"] - fns["session1"]["unique"]),
        )
        fn_table.add_row(
            "Avg Duration",
            _format_duration(fns["session1"]["avg_duration_ms"]),
            _format_duration(fns["session2"]["avg_duration_ms"]),
            _format_delta_inverse(fns["delta"]["avg_duration_ms"], "ms", 1),
        )

        console.print(fn_table)
        console.print()

        # Functions only in one session
        if fns["only_in_session1"]:
            fns_s1 = ", ".join(fns["only_in_session1"])
            console.print(f"[bold]Functions only in Session 1:[/bold] [red]{fns_s1}[/red]")
        if fns["only_in_session2"]:
            fns_s2 = ", ".join(fns["only_in_session2"])
            console.print(f"[bold]Functions only in Session 2:[/bold] [green]{fns_s2}[/green]")
        if fns["only_in_session1"] or fns["only_in_session2"]:
            console.print()

    # Trace comparison
    trace = diff["trace"]
    if trace["session1"]["root_nodes"] > 0 or trace["session2"]["root_nodes"] > 0:
        trace_table = Table(title="Trace Structure", show_header=True, header_style="bold cyan")
        trace_table.add_column("Metric", style="bold")
        trace_table.add_column("Session 1", justify="right")
        trace_table.add_column("Session 2", justify="right")
        trace_table.add_column("Delta", justify="right")

        trace_table.add_row(
            "Trace Depth",
            str(trace["session1"]["depth"]),
            str(trace["session2"]["depth"]),
            _format_delta(trace["session2"]["depth"] - trace["session1"]["depth"]),
        )
        trace_table.add_row(
            "Root Nodes",
            str(trace["session1"]["root_nodes"]),
            str(trace["session2"]["root_nodes"]),
            _format_delta(trace["session2"]["root_nodes"] - trace["session1"]["root_nodes"]),
        )

        console.print(trace_table)
        console.print()

    # Evaluations comparison
    evals = diff["evaluations"]
    if evals["session1"]["total"] > 0 or evals["session2"]["total"] > 0:
        eval_table = Table(title="Evaluation Results", show_header=True, header_style="bold cyan")
        eval_table.add_column("Metric", style="bold")
        eval_table.add_column("Session 1", justify="right")
        eval_table.add_column("Session 2", justify="right")
        eval_table.add_column("Delta", justify="right")

        eval_table.add_row(
            "Total Evals",
            str(evals["session1"]["total"]),
            str(evals["session2"]["total"]),
            _format_delta(evals["delta"]["total"]),
        )
        eval_table.add_row(
            "Passed",
            str(evals["session1"]["passed"]),
            str(evals["session2"]["passed"]),
            _format_delta(evals["delta"]["passed"]),
        )
        eval_table.add_row(
            "Failed",
            str(evals["session1"]["failed"]),
            str(evals["session2"]["failed"]),
            _format_delta_inverse(evals["delta"]["failed"]),
        )
        eval_table.add_row(
            "Pass Rate",
            f"{evals['pass_rate1'] * 100:.1f}%",
            f"{evals['pass_rate2'] * 100:.1f}%",
            _format_delta((evals["pass_rate2"] - evals["pass_rate1"]) * 100, "%", 1),
        )

        console.print(eval_table)
        console.print()

    # Errors summary
    errors = diff["errors"]
    if errors["session1"] or errors["session2"]:
        console.print("[bold]Errors Summary:[/bold]")
        if errors["session1"]:
            console.print("\n[bold red]Session 1 Errors:[/bold red]")
            for err in errors["session1"][:5]:
                console.print(f"  • {err}")
            if len(errors["session1"]) > 5:
                console.print(f"  [dim]... and {len(errors['session1']) - 5} more[/dim]")

        if errors["session2"]:
            console.print("\n[bold red]Session 2 Errors:[/bold red]")
            for err in errors["session2"][:5]:
                console.print(f"  • {err}")
            if len(errors["session2"]) > 5:
                console.print(f"  [dim]... and {len(errors['session2']) - 5} more[/dim]")
        console.print()

    # System Prompts comparison
    sys_prompts = diff.get("system_prompts", {})
    if sys_prompts.get("session1") or sys_prompts.get("session2"):
        console.print(
            Panel("[bold]System Prompts Comparison[/bold]", border_style="cyan", expand=False)
        )

        if sys_prompts.get("changed"):
            console.print("[yellow]⚠ System prompts differ between sessions[/yellow]\n")

        # Show unique prompts
        if sys_prompts.get("unique_to_session1"):
            console.print("[bold red]Only in Session 1:[/bold red]")
            for prompt in sys_prompts["unique_to_session1"][:2]:
                console.print(
                    Panel(
                        prompt[:500] + "..." if len(prompt) > 500 else prompt,
                        style="red",
                        expand=False,
                    )
                )
            if len(sys_prompts["unique_to_session1"]) > 2:
                console.print(
                    f"  [dim]... and {len(sys_prompts['unique_to_session1']) - 2} more[/dim]"
                )

        if sys_prompts.get("unique_to_session2"):
            console.print("\n[bold green]Only in Session 2:[/bold green]")
            for prompt in sys_prompts["unique_to_session2"][:2]:
                console.print(
                    Panel(
                        prompt[:500] + "..." if len(prompt) > 500 else prompt,
                        style="green",
                        expand=False,
                    )
                )
            if len(sys_prompts["unique_to_session2"]) > 2:
                console.print(
                    f"  [dim]... and {len(sys_prompts['unique_to_session2']) - 2} more[/dim]"
                )

        # Show prompt details
        prompts1 = sys_prompts.get("session1", [])
        prompts2 = sys_prompts.get("session2", [])

        if prompts1 or prompts2:
            prompt_table = Table(
                title="System Prompt Details", show_header=True, header_style="bold cyan"
            )
            prompt_table.add_column("Session", style="bold")
            prompt_table.add_column("Model")
            prompt_table.add_column("Length", justify="right")
            prompt_table.add_column("Preview", max_width=60)

            for p in prompts1[:3]:
                prompt_table.add_row(
                    "1",
                    p.get("model", "unknown"),
                    str(p.get("full_length", 0)),
                    p.get("content", "")[:100] + "..."
                    if len(p.get("content", "")) > 100
                    else p.get("content", ""),
                )
            for p in prompts2[:3]:
                prompt_table.add_row(
                    "2",
                    p.get("model", "unknown"),
                    str(p.get("full_length", 0)),
                    p.get("content", "")[:100] + "..."
                    if len(p.get("content", "")) > 100
                    else p.get("content", ""),
                )

            console.print(prompt_table)
        console.print()

    # Request Parameters comparison
    req_params = diff.get("request_params", {})
    s1_summary = req_params.get("session1", {}).get("summary", {})
    s2_summary = req_params.get("session2", {}).get("summary", {})

    if s1_summary or s2_summary:
        params_table = Table(
            title="Request Parameters Summary", show_header=True, header_style="bold cyan"
        )
        params_table.add_column("Parameter", style="bold")
        params_table.add_column("Session 1", justify="right")
        params_table.add_column("Session 2", justify="right")
        params_table.add_column("Delta", justify="right")

        # Average temperature
        temp1 = s1_summary.get("avg_temperature")
        temp2 = s2_summary.get("avg_temperature")
        if temp1 is not None or temp2 is not None:
            params_table.add_row(
                "Avg Temperature",
                f"{temp1:.2f}" if temp1 is not None else "-",
                f"{temp2:.2f}" if temp2 is not None else "-",
                _format_delta((temp2 or 0) - (temp1 or 0), "", 2)
                if temp1 is not None and temp2 is not None
                else "-",
            )

        # Average max tokens
        max_tok1 = s1_summary.get("avg_max_tokens")
        max_tok2 = s2_summary.get("avg_max_tokens")
        if max_tok1 is not None or max_tok2 is not None:
            params_table.add_row(
                "Avg Max Tokens",
                f"{int(max_tok1):,}" if max_tok1 is not None else "-",
                f"{int(max_tok2):,}" if max_tok2 is not None else "-",
                _format_delta((max_tok2 or 0) - (max_tok1 or 0))
                if max_tok1 is not None and max_tok2 is not None
                else "-",
            )

        # Streaming requests
        stream1 = s1_summary.get("streaming_requests", 0)
        stream2 = s2_summary.get("streaming_requests", 0)
        params_table.add_row(
            "Streaming Requests",
            str(stream1),
            str(stream2),
            _format_delta(stream2 - stream1),
        )

        console.print(params_table)
        console.print()

        # Tools comparison
        tools1 = set(s1_summary.get("tools_used", []))
        tools2 = set(s2_summary.get("tools_used", []))
        tools_added = req_params.get("tools_added", [])
        tools_removed = req_params.get("tools_removed", [])

        if tools1 or tools2:
            console.print("[bold]Tools Used:[/bold]")
            if tools_added:
                console.print(f"  [green]+ Added:[/green] {', '.join(tools_added)}")
            if tools_removed:
                console.print(f"  [red]- Removed:[/red] {', '.join(tools_removed)}")
            common_tools = tools1 & tools2
            if common_tools:
                console.print(f"  [dim]Common:[/dim] {', '.join(common_tools)}")
            console.print()

    # Responses comparison
    resp_data = diff.get("responses", {})
    s1_resp_summary = resp_data.get("session1", {}).get("summary", {})
    s2_resp_summary = resp_data.get("session2", {}).get("summary", {})
    resp_delta = resp_data.get("delta", {})

    if s1_resp_summary or s2_resp_summary:
        resp_table = Table(title="Response Summary", show_header=True, header_style="bold cyan")
        resp_table.add_column("Metric", style="bold")
        resp_table.add_column("Session 1", justify="right")
        resp_table.add_column("Session 2", justify="right")
        resp_table.add_column("Delta", justify="right")

        # Average content length
        resp_table.add_row(
            "Avg Response Length",
            f"{int(s1_resp_summary.get('avg_content_length', 0)):,}",
            f"{int(s2_resp_summary.get('avg_content_length', 0)):,}",
            _format_delta(resp_delta.get("avg_content_length", 0), "", 0),
        )

        # Total content length
        resp_table.add_row(
            "Total Response Length",
            f"{s1_resp_summary.get('total_content_length', 0):,}",
            f"{s2_resp_summary.get('total_content_length', 0):,}",
            _format_delta(
                s2_resp_summary.get("total_content_length", 0)
                - s1_resp_summary.get("total_content_length", 0)
            ),
        )

        # Tool calls
        resp_table.add_row(
            "Tool Calls",
            str(s1_resp_summary.get("tool_call_count", 0)),
            str(s2_resp_summary.get("tool_call_count", 0)),
            _format_delta(resp_delta.get("tool_call_count", 0)),
        )

        console.print(resp_table)
        console.print()

        # Stop reasons
        stop1 = s1_resp_summary.get("stop_reasons", {})
        stop2 = s2_resp_summary.get("stop_reasons", {})
        if stop1 or stop2:
            stop_table = Table(title="Stop Reasons", show_header=True, header_style="bold cyan")
            stop_table.add_column("Reason", style="bold")
            stop_table.add_column("Session 1", justify="right")
            stop_table.add_column("Session 2", justify="right")

            all_reasons = set(stop1.keys()) | set(stop2.keys())
            for reason in sorted(all_reasons):
                stop_table.add_row(
                    reason,
                    str(stop1.get(reason, 0)),
                    str(stop2.get(reason, 0)),
                )

            console.print(stop_table)
            console.print()

    # Response previews (show first response from each session)
    s1_responses = resp_data.get("session1", {}).get("responses", [])
    s2_responses = resp_data.get("session2", {}).get("responses", [])

    if s1_responses or s2_responses:
        console.print("[bold]Response Previews:[/bold]\n")

        if s1_responses:
            first_resp = s1_responses[0]
            preview = first_resp.get("content_preview", "No content")
            console.print("[bold cyan]Session 1 (first response):[/bold cyan]")
            console.print(
                Panel(
                    preview,
                    title=f"{first_resp.get('provider', '')} / {first_resp.get('model', '')}",
                    subtitle=f"Duration: {_format_duration(first_resp.get('duration_ms', 0))}",
                    expand=False,
                    border_style="dim",
                )
            )
            if first_resp.get("tool_calls"):
                tool_names = ", ".join(tc["name"] for tc in first_resp["tool_calls"])
                console.print(f"  [dim]Tool calls: {tool_names}[/dim]")

        if s2_responses:
            first_resp = s2_responses[0]
            preview = first_resp.get("content_preview", "No content")
            console.print("\n[bold cyan]Session 2 (first response):[/bold cyan]")
            console.print(
                Panel(
                    preview,
                    title=f"{first_resp.get('provider', '')} / {first_resp.get('model', '')}",
                    subtitle=f"Duration: {_format_duration(first_resp.get('duration_ms', 0))}",
                    expand=False,
                    border_style="dim",
                )
            )
            if first_resp.get("tool_calls"):
                tool_names = ", ".join(tc["name"] for tc in first_resp["tool_calls"])
                console.print(f"  [dim]Tool calls: {tool_names}[/dim]")


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


@app.command("diff")
def diff_sessions(
    session_id1: str = typer.Argument(..., help="First session ID"),
    session_id2: str = typer.Argument(..., help="Second session ID"),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table or json",
    ),
):
    """Compare two sessions and show their differences.

    Shows a detailed comparison including:
    - Metadata (duration, labels, meta)
    - LLM calls (count, tokens, latency, errors)
    - Provider/model distribution
    - Function events
    - Trace structure
    - Evaluation results

    Examples:

        shepherd sessions diff abc123 def456

        shepherd sessions diff abc123 def456 --output json
    """
    config = load_config()
    output_format = output or config.cli.output_format

    try:
        with _get_client() as client:
            # Fetch both sessions
            session1 = client.get_session(session_id1)
            session2 = client.get_session(session_id2)

            if not session1.sessions:
                console.print(f"[red]Session not found:[/red] {session_id1}")
                raise typer.Exit(1)
            if not session2.sessions:
                console.print(f"[red]Session not found:[/red] {session_id2}")
                raise typer.Exit(1)

            # Compute diff
            diff_calc = SessionDiff(session1, session2)
            diff_result = diff_calc.compute()

            if output_format == "json":
                console.print_json(json.dumps(diff_result, indent=2))
            else:
                _print_session_diff(diff_result)

    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise typer.Exit(1)
    except SessionNotFoundError as e:
        console.print(f"[red]Session not found:[/red] {e}")
        raise typer.Exit(1)
    except AIOBSError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
