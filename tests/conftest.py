"""Shared test fixtures."""

import pytest

# Sample API responses for testing
SAMPLE_SESSION = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "test-session",
    "started_at": 1733580000.123,
    "ended_at": 1733580120.456,
    "meta": {"pid": 12345, "cwd": "/home/user/project"},
    "labels": {"environment": "test", "version": "1.0.0"},
}

SAMPLE_EVENT = {
    "provider": "openai",
    "api": "chat.completions.create",
    "request": {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
    },
    "response": {
        "id": "chatcmpl-abc123",
        "model": "gpt-4",
        "usage": {"prompt_tokens": 12, "completion_tokens": 20, "total_tokens": 32},
        "text": "Hello! How can I help you?",
    },
    "error": None,
    "started_at": 1733580010.100,
    "ended_at": 1733580011.500,
    "duration_ms": 1400.0,
    "callsite": None,
    "span_id": "span-001",
    "parent_span_id": None,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "evaluations": [],
}

SAMPLE_FUNCTION_EVENT = {
    "provider": "function",
    "api": "app.utils.process",
    "name": "process",
    "module": "app.utils",
    "args": ["hello"],
    "kwargs": {"verbose": True},
    "result": "processed: hello",
    "error": None,
    "started_at": 1733580009.000,
    "ended_at": 1733580012.000,
    "duration_ms": 3000.0,
    "callsite": None,
    "span_id": "span-000",
    "parent_span_id": None,
    "enh_prompt": False,
    "enh_prompt_id": None,
    "auto_enhance_after": None,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "evaluations": [],
}

SAMPLE_TRACE_NODE = {
    "provider": "openai",
    "api": "chat.completions.create",
    "request": {"model": "gpt-4"},
    "response": {"text": "Hello!"},
    "name": None,
    "module": None,
    "args": None,
    "kwargs": None,
    "result": None,
    "error": None,
    "started_at": 1733580010.100,
    "ended_at": 1733580011.500,
    "duration_ms": 1400.0,
    "span_id": "span-001",
    "parent_span_id": None,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "provider",
    "children": [],
    "evaluations": [],
}


@pytest.fixture
def sample_sessions_response():
    """Return a sample sessions API response."""
    return {
        "sessions": [SAMPLE_SESSION],
        "events": [SAMPLE_EVENT],
        "function_events": [SAMPLE_FUNCTION_EVENT],
        "trace_tree": [SAMPLE_TRACE_NODE],
        "enh_prompt_traces": [],
        "generated_at": 1733580500.789,
        "version": 1,
    }


@pytest.fixture
def empty_sessions_response():
    """Return an empty sessions API response."""
    return {
        "sessions": [],
        "events": [],
        "function_events": [],
        "trace_tree": [],
        "enh_prompt_traces": [],
        "generated_at": 1733580500.789,
        "version": 1,
    }


# Additional fixtures for search testing

SAMPLE_SESSION_PROD = {
    "id": "prod-session-001",
    "name": "production-agent",
    "started_at": 1733580000.0,
    "ended_at": 1733580120.0,
    "meta": {"pid": 12345},
    "labels": {"env": "production", "user": "alice"},
}

SAMPLE_SESSION_DEV = {
    "id": "dev-session-002",
    "name": "dev-agent",
    "started_at": 1733490000.0,  # Earlier date
    "ended_at": 1733490120.0,
    "meta": {"pid": 12346},
    "labels": {"env": "development", "user": "bob"},
}

SAMPLE_EVENT_ANTHROPIC = {
    "provider": "anthropic",
    "api": "messages.create",
    "request": {"model": "claude-3-opus"},
    "response": {"usage": {"input_tokens": 10, "output_tokens": 20}},
    "error": None,
    "started_at": 1733580010.0,
    "ended_at": 1733580011.0,
    "duration_ms": 1000.0,
    "callsite": None,
    "span_id": "span-anthropic-001",
    "parent_span_id": None,
    "session_id": "prod-session-001",
    "evaluations": [],
}

SAMPLE_EVENT_WITH_ERROR = {
    "provider": "openai",
    "api": "chat.completions.create",
    "request": {"model": "gpt-4"},
    "response": None,
    "error": "Rate limit exceeded",
    "started_at": 1733490010.0,
    "ended_at": 1733490011.0,
    "duration_ms": 1000.0,
    "callsite": None,
    "span_id": "span-error-001",
    "parent_span_id": None,
    "session_id": "dev-session-002",
    "evaluations": [],
}

SAMPLE_EVENT_WITH_FAILED_EVAL = {
    "provider": "openai",
    "api": "chat.completions.create",
    "request": {"model": "gpt-4"},
    "response": {"text": "response"},
    "error": None,
    "started_at": 1733580010.0,
    "ended_at": 1733580011.0,
    "duration_ms": 1000.0,
    "callsite": None,
    "span_id": "span-eval-001",
    "parent_span_id": None,
    "session_id": "prod-session-001",
    "evaluations": [{"name": "relevance", "passed": False, "score": 0.2}],
}

SAMPLE_FUNCTION_EVENT_PROCESS = {
    "provider": "function",
    "api": "mymodule.process_data",
    "name": "process_data",
    "module": "mymodule",
    "args": ["input"],
    "kwargs": {},
    "result": "output",
    "error": None,
    "started_at": 1733580009.0,
    "ended_at": 1733580012.0,
    "duration_ms": 3000.0,
    "callsite": None,
    "span_id": "span-fn-001",
    "parent_span_id": None,
    "enh_prompt": False,
    "enh_prompt_id": None,
    "auto_enhance_after": None,
    "session_id": "prod-session-001",
    "evaluations": [],
}


@pytest.fixture
def search_sessions_response():
    """Return a response with multiple sessions for search testing."""
    return {
        "sessions": [SAMPLE_SESSION_PROD, SAMPLE_SESSION_DEV],
        "events": [SAMPLE_EVENT_ANTHROPIC, SAMPLE_EVENT_WITH_ERROR],
        "function_events": [SAMPLE_FUNCTION_EVENT_PROCESS],
        "trace_tree": [],
        "enh_prompt_traces": [],
        "generated_at": 1733580500.789,
        "version": 1,
    }


@pytest.fixture
def search_sessions_with_failed_evals():
    """Return a response with sessions that have failed evaluations."""
    return {
        "sessions": [SAMPLE_SESSION_PROD, SAMPLE_SESSION_DEV],
        "events": [SAMPLE_EVENT_WITH_FAILED_EVAL, SAMPLE_EVENT_WITH_ERROR],
        "function_events": [],
        "trace_tree": [],
        "enh_prompt_traces": [],
        "generated_at": 1733580500.789,
        "version": 1,
    }
