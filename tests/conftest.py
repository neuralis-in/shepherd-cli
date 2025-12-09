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


# Fixtures for diff testing

DIFF_SESSION_1 = {
    "id": "session-diff-001",
    "name": "baseline-agent",
    "started_at": 1733580000.0,
    "ended_at": 1733580120.0,
    "meta": {"pid": 12345},
    "labels": {"env": "production", "version": "1.0.0"},
}

DIFF_SESSION_2 = {
    "id": "session-diff-002",
    "name": "updated-agent",
    "started_at": 1733590000.0,
    "ended_at": 1733590180.0,  # Longer duration
    "meta": {"pid": 12346},
    "labels": {"env": "production", "version": "2.0.0"},  # Different version
}

DIFF_EVENT_1 = {
    "provider": "openai",
    "api": "chat.completions.create",
    "request": {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for code review."},
            {"role": "user", "content": "Please review this Python function for bugs."},
        ],
        "tools": [
            {
                "type": "function",
                "function": {"name": "get_file_contents", "description": "Read a file"},
            },
            {
                "type": "function",
                "function": {"name": "search_code", "description": "Search codebase"},
            },
        ],
    },
    "response": {
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        "choices": [
            {
                "message": {
                    "content": (
                        "I've reviewed the function. Here are my findings:\n\n"
                        "1. Missing error handling\n2. Potential null reference"
                    ),
                    "role": "assistant",
                },
                "finish_reason": "stop",
            }
        ],
    },
    "error": None,
    "started_at": 1733580010.0,
    "ended_at": 1733580012.0,
    "duration_ms": 2000.0,
    "callsite": None,
    "span_id": "span-diff-001",
    "parent_span_id": None,
    "session_id": "session-diff-001",
    "evaluations": [{"name": "relevance", "passed": True, "score": 0.9}],
}

DIFF_EVENT_2A = {
    "provider": "openai",
    "api": "chat.completions.create",
    "request": {
        "model": "gpt-4",
        "temperature": 0.5,  # Lower temperature
        "max_tokens": 2000,  # More tokens
        "messages": [
            {
                "role": "system",
                "content": "You are an expert code reviewer with focus on security.",
            },
            {"role": "user", "content": "Analyze this code for security vulnerabilities."},
        ],
        "tools": [
            {
                "type": "function",
                "function": {"name": "get_file_contents", "description": "Read a file"},
            },
            {
                "type": "function",
                "function": {"name": "run_security_scan", "description": "Run scan"},
            },
        ],
    },
    "response": {
        "usage": {"prompt_tokens": 80, "completion_tokens": 40, "total_tokens": 120},
        "choices": [
            {
                "message": {
                    "content": (
                        "Security analysis complete. Found 2 potential issues:\n\n"
                        "1. SQL injection risk\n2. Unvalidated input"
                    ),
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "run_security_scan",
                                "arguments": '{"path": "src/"}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
    },
    "error": None,
    "started_at": 1733590010.0,
    "ended_at": 1733590011.5,
    "duration_ms": 1500.0,  # Faster
    "callsite": None,
    "span_id": "span-diff-002a",
    "parent_span_id": None,
    "session_id": "session-diff-002",
    "evaluations": [{"name": "relevance", "passed": True, "score": 0.95}],
}

DIFF_EVENT_2B = {
    "provider": "anthropic",
    "api": "messages.create",
    "request": {
        "model": "claude-3-opus",
        "system": "You are a security expert.",  # Anthropic-style system prompt
        "max_tokens": 1500,
        "messages": [
            {"role": "user", "content": "Explain the security findings in detail."},
        ],
    },
    "response": {
        "usage": {"input_tokens": 60, "output_tokens": 30, "total_tokens": 90},
        "content": [
            {
                "type": "text",
                "text": (
                    "Based on the scan results, here's a detailed breakdown "
                    "of the security issues found..."
                ),
            },
        ],
        "stop_reason": "end_turn",
    },
    "error": None,
    "started_at": 1733590012.0,
    "ended_at": 1733590013.0,
    "duration_ms": 1000.0,
    "callsite": None,
    "span_id": "span-diff-002b",
    "parent_span_id": None,
    "session_id": "session-diff-002",
    "evaluations": [],
}

DIFF_FUNCTION_1 = {
    "provider": "function",
    "api": "mymodule.process",
    "name": "process",
    "module": "mymodule",
    "args": ["input"],
    "kwargs": {},
    "result": "output",
    "error": None,
    "started_at": 1733580009.0,
    "ended_at": 1733580010.0,
    "duration_ms": 1000.0,
    "callsite": None,
    "span_id": "span-fn-diff-001",
    "parent_span_id": None,
    "enh_prompt": False,
    "enh_prompt_id": None,
    "auto_enhance_after": None,
    "session_id": "session-diff-001",
    "evaluations": [],
}

DIFF_FUNCTION_2 = {
    "provider": "function",
    "api": "mymodule.new_process",
    "name": "new_process",  # Different function
    "module": "mymodule",
    "args": ["input"],
    "kwargs": {},
    "result": "output",
    "error": None,
    "started_at": 1733590009.0,
    "ended_at": 1733590009.5,
    "duration_ms": 500.0,  # Faster
    "callsite": None,
    "span_id": "span-fn-diff-002",
    "parent_span_id": None,
    "enh_prompt": False,
    "enh_prompt_id": None,
    "auto_enhance_after": None,
    "session_id": "session-diff-002",
    "evaluations": [],
}


@pytest.fixture
def diff_session_response_1():
    """Return the first session response for diff testing."""
    return {
        "sessions": [DIFF_SESSION_1],
        "events": [DIFF_EVENT_1],
        "function_events": [DIFF_FUNCTION_1],
        "trace_tree": [],
        "enh_prompt_traces": [],
        "generated_at": 1733580500.789,
        "version": 1,
    }


@pytest.fixture
def diff_session_response_2():
    """Return the second session response for diff testing."""
    return {
        "sessions": [DIFF_SESSION_2],
        "events": [DIFF_EVENT_2A, DIFF_EVENT_2B],
        "function_events": [DIFF_FUNCTION_2],
        "trace_tree": [],
        "enh_prompt_traces": [],
        "generated_at": 1733590500.789,
        "version": 1,
    }


# ============================================================================
# Langfuse Fixtures
# ============================================================================

SAMPLE_LANGFUSE_OBSERVATION = {
    "id": "obs-001",
    "traceId": "trace-001",
    "type": "GENERATION",
    "name": "chat-completion",
    "startTime": "2025-12-09T14:00:00.000Z",
    "endTime": "2025-12-09T14:00:02.500Z",
    "model": "gpt-4o-mini",
    "modelParameters": {"temperature": 0.7, "max_tokens": 1000},
    "input": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
    "output": {"role": "assistant", "content": "Hello! How can I help you today?"},
    "usage": {"input": 50, "output": 20, "total": 70},
    "level": "DEFAULT",
    "latency": 2.5,
    "calculatedInputCost": 0.00005,
    "calculatedOutputCost": 0.00002,
    "calculatedTotalCost": 0.00007,
}

SAMPLE_LANGFUSE_SPAN = {
    "id": "obs-002",
    "traceId": "trace-001",
    "type": "SPAN",
    "name": "process-request",
    "startTime": "2025-12-09T13:59:59.000Z",
    "endTime": "2025-12-09T14:00:03.000Z",
    "latency": 4.0,
}

SAMPLE_LANGFUSE_TRACE = {
    "id": "trace-001",
    "timestamp": "2025-12-09T13:59:59.000Z",
    "name": "pipeline",
    "userId": "user-123",
    "sessionId": "session-abc",
    "tags": ["production", "v2"],
    "latency": 4.0,
    "totalCost": 0.00007,
    "observations": ["obs-001", "obs-002"],  # IDs when listing
}

SAMPLE_LANGFUSE_TRACE_DETAIL = {
    "id": "trace-001",
    "timestamp": "2025-12-09T13:59:59.000Z",
    "name": "pipeline",
    "userId": "user-123",
    "sessionId": "session-abc",
    "tags": ["production", "v2"],
    "latency": 4.0,
    "totalCost": 0.00007,
    "observations": [SAMPLE_LANGFUSE_OBSERVATION, SAMPLE_LANGFUSE_SPAN],  # Full objects when getting
}

SAMPLE_LANGFUSE_SESSION = {
    "id": "session-abc",
    "createdAt": "2025-12-09T10:00:00.000Z",
    "projectId": "project-xyz",
    "userIds": ["user-123"],
    "countTraces": 5,
    "sessionDuration": 300.0,
    "inputCost": 0.001,
    "outputCost": 0.0005,
    "totalCost": 0.0015,
    "inputTokens": 500,
    "outputTokens": 200,
    "totalTokens": 700,
}


@pytest.fixture
def sample_langfuse_traces_response():
    """Return a sample Langfuse traces API response."""
    return {
        "data": [SAMPLE_LANGFUSE_TRACE],
        "meta": {"page": 1, "limit": 50, "totalItems": 1, "totalPages": 1},
    }


@pytest.fixture
def sample_langfuse_trace_detail():
    """Return a sample Langfuse trace detail with full observations."""
    return SAMPLE_LANGFUSE_TRACE_DETAIL


@pytest.fixture
def sample_langfuse_sessions_response():
    """Return a sample Langfuse sessions API response."""
    return {
        "data": [SAMPLE_LANGFUSE_SESSION],
        "meta": {"page": 1, "limit": 50, "totalItems": 1, "totalPages": 1},
    }


@pytest.fixture
def empty_langfuse_traces_response():
    """Return an empty Langfuse traces response."""
    return {
        "data": [],
        "meta": {"page": 1, "limit": 50, "totalItems": 0, "totalPages": 0},
    }


@pytest.fixture
def empty_langfuse_sessions_response():
    """Return an empty Langfuse sessions response."""
    return {
        "data": [],
        "meta": {"page": 1, "limit": 50, "totalItems": 0, "totalPages": 0},
    }
