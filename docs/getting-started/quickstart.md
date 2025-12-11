# Quick Start

Get debugging in under 5 minutes.

## Prerequisites

1. [Install Shepherd CLI](installation.md)
2. [Configure your API key](configuration.md)

## Choose Your Provider

Shepherd supports multiple observability providers:

```bash
# For AIOBS (default)
shepherd config set provider aiobs

# For Langfuse
shepherd config set provider langfuse
```

---

## AIOBS Quick Start

### List Sessions

```bash
shepherd sessions list
```

Output:

```
                              Sessions                              
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ ID          ┃ Name         ┃ Started      ┃ Duration ┃ Events ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ be393d0d... │ pipeline-ex… │ 2025-12-03   │     9.6s │      4 │
│ 6dfe36bb... │ pipeline-ex… │ 2025-12-03   │     9.8s │      4 │
└─────────────┴──────────────┴──────────────┴──────────┴────────┘
```

### Search and Filter

```bash
# Search by text
shepherd sessions search "my-agent"

# Filter by labels
shepherd sessions search --label env=production

# Find sessions with errors
shepherd sessions search --has-errors

# Compare two sessions
shepherd sessions diff session1 session2
```

---

## Langfuse Quick Start

### List Traces

```bash
shepherd traces list
```

Output:

```
                              Traces                               
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ ID          ┃ Name         ┃ Timestamp    ┃ Latency  ┃ Cost   ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ trace-001   │ pipeline     │ 2025-12-09   │     3.5s │ $0.001 │
│ trace-002   │ chat-agent   │ 2025-12-09   │     1.2s │ $0.000 │
└─────────────┴──────────────┴──────────────┴──────────┴────────┘
```

### Search and Filter

```bash
# Search traces by name/tags
shepherd traces search "my-agent"
shepherd traces search --tag production

# Filter by cost and latency
shepherd traces search --min-cost 0.01 --max-latency 5.0

# Search sessions
shepherd sessions search --user-id alice
shepherd sessions search --min-traces 5
```

---

## Common Commands

```bash
# Limit results
shepherd sessions list -n 5
shepherd traces list -n 10

# Get only IDs (for scripting)
shepherd sessions list --ids
shepherd traces list --ids

# Export as JSON
shepherd sessions list -o json > sessions.json
shepherd traces get <id> -o json > trace.json
```

## Typical Workflow

```bash
# 1. Find recent sessions/traces
shepherd sessions list -n 20
shepherd traces list -n 20

# 2. Get latest ID
ID=$(shepherd sessions list --ids -n 1)

# 3. Inspect it
shepherd sessions get $ID

# 4. Export for analysis
shepherd sessions get $ID -o json > debug.json
```

