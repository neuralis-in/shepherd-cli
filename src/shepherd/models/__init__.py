"""Pydantic models for Shepherd CLI."""

from shepherd.models.langfuse import (
    LangfuseObservation,
    LangfuseObservationsResponse,
    LangfuseScore,
    LangfuseScoresResponse,
    LangfuseSession,
    LangfuseSessionsResponse,
    LangfuseTrace,
    LangfuseTracesResponse,
)
from shepherd.models.session import (
    Callsite,
    Event,
    FunctionEvent,
    Session,
    SessionsResponse,
    TraceNode,
)

__all__ = [
    # AIOBS models
    "Callsite",
    "Event",
    "FunctionEvent",
    "Session",
    "SessionsResponse",
    "TraceNode",
    # Langfuse models
    "LangfuseObservation",
    "LangfuseObservationsResponse",
    "LangfuseScore",
    "LangfuseScoresResponse",
    "LangfuseSession",
    "LangfuseSessionsResponse",
    "LangfuseTrace",
    "LangfuseTracesResponse",
]
