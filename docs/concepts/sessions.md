# Sessions & Traces

## Sessions

A **session** represents a single execution of your AI agent.

```json
{
  "id": "be393d0d-7139-4241-a00d-e3c9ff4f9fcf",
  "name": "code-review-agent",
  "started_at": 1733580000.123,
  "ended_at": 1733580120.456,
  "meta": { "pid": 12345 },
  "labels": { "environment": "production" }
}
```

| Property | Description |
|----------|-------------|
| `id` | Unique identifier (UUID) |
| `name` | Human-readable name |
| `started_at` | Unix timestamp |
| `ended_at` | Unix timestamp |
| `meta` | System metadata |
| `labels` | Custom labels |

## Events

### LLM Events

```json
{
  "provider": "openai",
  "api": "chat.completions.create",
  "request": { "model": "gpt-4" },
  "response": { "text": "Hello!" },
  "duration_ms": 1400.0
}
```

### Function Events

```json
{
  "provider": "function",
  "name": "process",
  "args": ["input"],
  "result": "output",
  "duration_ms": 500.0
}
```

## Trace Tree

Events form a hierarchical trace tree:

```
pipeline-example
├── fn research (3.5s)
│   └── openai chat.completions.create (3.0s)
├── fn summarize (2.5s)
│   └── openai chat.completions.create (2.4s)
└── fn critique (4.5s)
    └── openai chat.completions.create (4.1s)
```

