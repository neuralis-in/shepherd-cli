"""Tests for pydantic models."""

import pytest

from shepherd.models import (
    Callsite,
    Event,
    FunctionEvent,
    Session,
    SessionsResponse,
    TraceNode,
)


class TestCallsite:
    """Tests for Callsite model."""

    def test_valid_callsite(self):
        callsite = Callsite(file="main.py", line=42, function="run")
        assert callsite.file == "main.py"
        assert callsite.line == 42
        assert callsite.function == "run"


class TestSession:
    """Tests for Session model."""

    def test_valid_session(self):
        session = Session(
            id="test-id",
            name="test-session",
            started_at=1733580000.0,
            ended_at=1733580100.0,
            meta={"pid": 123},
            labels={"env": "test"},
        )
        assert session.id == "test-id"
        assert session.name == "test-session"
        assert session.meta == {"pid": 123}
        assert session.labels == {"env": "test"}

    def test_session_without_optional_fields(self):
        session = Session(
            id="test-id",
            name="test-session",
            started_at=1733580000.0,
        )
        assert session.ended_at is None
        assert session.meta == {}
        assert session.labels == {}


class TestEvent:
    """Tests for Event model."""

    def test_valid_event(self):
        event = Event(
            provider="openai",
            api="chat.completions.create",
            request={"model": "gpt-4"},
            response={"text": "Hello"},
            started_at=1733580000.0,
            ended_at=1733580001.0,
            duration_ms=1000.0,
            span_id="span-001",
            session_id="session-001",
        )
        assert event.provider == "openai"
        assert event.api == "chat.completions.create"
        assert event.duration_ms == 1000.0

    def test_event_with_null_response(self):
        event = Event(
            provider="openai",
            api="chat.completions.create",
            request={"model": "gpt-4"},
            response=None,
            error="API Error",
            started_at=1733580000.0,
            ended_at=1733580001.0,
            duration_ms=1000.0,
            span_id="span-001",
            session_id="session-001",
        )
        assert event.response is None
        assert event.error == "API Error"


class TestFunctionEvent:
    """Tests for FunctionEvent model."""

    def test_valid_function_event(self):
        event = FunctionEvent(
            provider="function",
            api="app.utils.process",
            name="process",
            module="app.utils",
            args=["hello"],
            kwargs={"verbose": True},
            result="done",
            started_at=1733580000.0,
            ended_at=1733580001.0,
            duration_ms=1000.0,
            span_id="span-001",
            session_id="session-001",
        )
        assert event.name == "process"
        assert event.args == ["hello"]
        assert event.kwargs == {"verbose": True}

    def test_function_event_with_null_args_kwargs(self):
        """Test that null args/kwargs are accepted (as returned by API)."""
        event = FunctionEvent(
            provider="function",
            api="app.utils.process",
            name="process",
            args=None,
            kwargs=None,
            started_at=1733580000.0,
            ended_at=1733580001.0,
            duration_ms=1000.0,
            span_id="span-001",
            session_id="session-001",
        )
        assert event.args is None
        assert event.kwargs is None


class TestTraceNode:
    """Tests for TraceNode model."""

    def test_provider_trace_node(self):
        node = TraceNode(
            provider="openai",
            api="chat.completions.create",
            request={"model": "gpt-4"},
            response={"text": "Hello"},
            started_at=1733580000.0,
            ended_at=1733580001.0,
            duration_ms=1000.0,
            span_id="span-001",
            session_id="session-001",
            event_type="provider",
        )
        assert node.provider == "openai"
        assert node.event_type == "provider"
        assert node.children == []

    def test_function_trace_node(self):
        node = TraceNode(
            provider="function",
            api="app.utils.process",
            name="process",
            module="app.utils",
            args=["hello"],
            kwargs={"verbose": True},
            result="done",
            started_at=1733580000.0,
            ended_at=1733580001.0,
            duration_ms=1000.0,
            span_id="span-001",
            session_id="session-001",
            event_type="function",
        )
        assert node.name == "process"
        assert node.event_type == "function"

    def test_trace_node_with_children(self):
        child = TraceNode(
            provider="openai",
            api="chat.completions.create",
            started_at=1733580000.0,
            ended_at=1733580001.0,
            duration_ms=1000.0,
            span_id="span-002",
            parent_span_id="span-001",
            session_id="session-001",
        )
        parent = TraceNode(
            provider="function",
            api="app.run",
            started_at=1733580000.0,
            ended_at=1733580002.0,
            duration_ms=2000.0,
            span_id="span-001",
            session_id="session-001",
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].parent_span_id == "span-001"


class TestSessionsResponse:
    """Tests for SessionsResponse model."""

    def test_valid_response(self, sample_sessions_response):
        response = SessionsResponse(**sample_sessions_response)
        assert len(response.sessions) == 1
        assert len(response.events) == 1
        assert len(response.function_events) == 1
        assert response.version == 1

    def test_empty_response(self, empty_sessions_response):
        response = SessionsResponse(**empty_sessions_response)
        assert len(response.sessions) == 0
        assert len(response.events) == 0

