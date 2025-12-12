"""Langfuse-specific models.

These models represent Langfuse's data structures for traces, observations,
sessions, and scores. They are separate from aiobs models.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LangfuseObservation(BaseModel):
    """Observation (generation, span, or event) in Langfuse."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    trace_id: str = Field(alias="traceId")
    type: str  # "GENERATION", "SPAN", "EVENT"
    name: str | None = None
    start_time: str = Field(alias="startTime")
    end_time: str | None = Field(default=None, alias="endTime")
    completion_start_time: str | None = Field(default=None, alias="completionStartTime")
    model: str | None = None
    model_parameters: dict[str, Any] | None = Field(default=None, alias="modelParameters")
    input: Any | None = None
    output: Any | None = None
    usage: dict[str, Any] | None = None
    level: str | None = None  # "DEBUG", "DEFAULT", "WARNING", "ERROR"
    status_message: str | None = Field(default=None, alias="statusMessage")
    parent_observation_id: str | None = Field(default=None, alias="parentObservationId")
    version: str | None = None
    metadata: dict[str, Any] | None = None
    # Computed fields from API
    latency: float | None = None  # in seconds
    time_to_first_token: float | None = Field(default=None, alias="timeToFirstToken")
    prompt_id: str | None = Field(default=None, alias="promptId")
    prompt_name: str | None = Field(default=None, alias="promptName")
    prompt_version: int | None = Field(default=None, alias="promptVersion")
    # Cost fields
    calculated_input_cost: float | None = Field(default=None, alias="calculatedInputCost")
    calculated_output_cost: float | None = Field(default=None, alias="calculatedOutputCost")
    calculated_total_cost: float | None = Field(default=None, alias="calculatedTotalCost")


class LangfuseTrace(BaseModel):
    """Trace in Langfuse representing a complete workflow or conversation."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    timestamp: str
    name: str | None = None
    user_id: str | None = Field(default=None, alias="userId")
    session_id: str | None = Field(default=None, alias="sessionId")
    release: str | None = None
    version: str | None = None
    metadata: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)
    public: bool = False
    # Computed/aggregated fields
    input: Any | None = None
    output: Any | None = None
    latency: float | None = None  # in seconds
    total_cost: float | None = Field(default=None, alias="totalCost")
    # Observations: list of IDs (from list endpoint) or full objects (from get endpoint)
    # When listing traces, API returns observation IDs as strings
    # When getting a single trace, API returns full observation objects
    observations: list[str | LangfuseObservation] = Field(default_factory=list)


class LangfuseSession(BaseModel):
    """Session in Langfuse grouping related traces."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    created_at: str = Field(alias="createdAt")
    project_id: str = Field(alias="projectId")
    # Optional fields from session details
    user_ids: list[str] = Field(default_factory=list, alias="userIds")
    count_traces: int = Field(default=0, alias="countTraces")
    # Aggregated metrics
    session_duration: float | None = Field(default=None, alias="sessionDuration")
    input_cost: float = Field(default=0, alias="inputCost")
    output_cost: float = Field(default=0, alias="outputCost")
    total_cost: float = Field(default=0, alias="totalCost")
    input_tokens: int = Field(default=0, alias="inputTokens")
    output_tokens: int = Field(default=0, alias="outputTokens")
    total_tokens: int = Field(default=0, alias="totalTokens")
    total_count: int = Field(default=0, alias="totalCount")
    # Nested traces (when fetching session with traces)
    traces: list[LangfuseTrace] = Field(default_factory=list)


class LangfuseScore(BaseModel):
    """Score/evaluation in Langfuse."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    trace_id: str = Field(alias="traceId")
    observation_id: str | None = Field(default=None, alias="observationId")
    name: str
    value: float | str | None = None
    string_value: str | None = Field(default=None, alias="stringValue")
    timestamp: str
    source: str  # "API", "ANNOTATION", "EVAL"
    data_type: str = Field(alias="dataType")  # "NUMERIC", "CATEGORICAL", "BOOLEAN"
    comment: str | None = None
    config_id: str | None = Field(default=None, alias="configId")


class LangfuseTracesResponse(BaseModel):
    """Response from /api/public/traces."""

    data: list[LangfuseTrace] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class LangfuseSessionsResponse(BaseModel):
    """Response from /api/public/sessions."""

    data: list[LangfuseSession] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class LangfuseObservationsResponse(BaseModel):
    """Response from /api/public/observations."""

    data: list[LangfuseObservation] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class LangfuseScoresResponse(BaseModel):
    """Response from /api/public/scores."""

    data: list[LangfuseScore] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
