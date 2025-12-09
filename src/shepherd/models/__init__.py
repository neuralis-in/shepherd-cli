"""Pydantic models for Shepherd CLI."""

from shepherd.models.session import (
    Callsite,
    Event,
    FunctionEvent,
    Session,
    SessionsResponse,
    TraceNode,
)
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
