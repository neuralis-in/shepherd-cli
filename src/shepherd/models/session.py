"""Session and trace models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Callsite(BaseModel):
    """Code location where a call was made."""

    file: str
    line: int
    function: str


class Evaluation(BaseModel):
    """Evaluation result."""

    # Flexible structure for evaluations
    pass


class Event(BaseModel):
    """LLM provider event (e.g., OpenAI, Anthropic calls)."""

    provider: str
    api: str
    request: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] | None = None
    error: str | None = None
    started_at: float
    ended_at: float
    duration_ms: float
    callsite: Callsite | None = None
    span_id: str
    parent_span_id: str | None = None
    session_id: str
    evaluations: list[Any] = Field(default_factory=list)


class FunctionEvent(BaseModel):
    """Observed function event."""

    provider: str
    api: str
    name: str
    module: str | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None
    result: Any = None
    error: str | None = None
    started_at: float
    ended_at: float
    duration_ms: float
    callsite: Callsite | None = None
    span_id: str
    parent_span_id: str | None = None
    enh_prompt: bool = False
    enh_prompt_id: str | None = None
    auto_enhance_after: int | None = None
    session_id: str
    evaluations: list[Any] = Field(default_factory=list)


class TraceNode(BaseModel):
    """Node in the trace tree (can be either provider or function event)."""

    provider: str
    api: str
    # Provider event fields
    request: dict[str, Any] | None = None
    response: dict[str, Any] | None = None
    # Function event fields
    name: str | None = None
    module: str | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None
    result: Any = None
    error: str | None = None
    # Common fields
    started_at: float
    ended_at: float
    duration_ms: float
    span_id: str
    parent_span_id: str | None = None
    session_id: str
    event_type: str | None = None  # "function" or "provider"
    children: list[TraceNode] = Field(default_factory=list)
    evaluations: list[Any] = Field(default_factory=list)


class Session(BaseModel):
    """Session metadata."""

    id: str
    name: str
    started_at: float
    ended_at: float | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    labels: dict[str, str] = Field(default_factory=dict)


class SessionsResponse(BaseModel):
    """Response from /v1/sessions or /v1/sessions/{id}/tree."""

    sessions: list[Session] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    function_events: list[FunctionEvent] = Field(default_factory=list)
    trace_tree: list[TraceNode] = Field(default_factory=list)
    enh_prompt_traces: list[Any] = Field(default_factory=list)
    generated_at: float
    version: int = 1

