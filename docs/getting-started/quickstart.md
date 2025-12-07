# Quick Start

Get debugging in under 5 minutes.

## Prerequisites

1. [Install Shepherd CLI](installation.md)
2. [Configure your API key](configuration.md)

## List Sessions

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

## Filter and Limit

```bash
# Limit to 5 sessions
shepherd sessions list -n 5

# Get only IDs (for scripting)
shepherd sessions list --ids
```

## Get Session Details

```bash
shepherd sessions get be393d0d-7139-4241-a00d-e3c9ff4f9fcf
```

## Export as JSON

```bash
shepherd sessions list -o json > sessions.json
shepherd sessions get <id> -o json > trace.json
```

## Typical Workflow

```bash
# 1. Find recent sessions
shepherd sessions list -n 20

# 2. Get latest session ID
SESSION_ID=$(shepherd sessions list --ids -n 1)

# 3. Inspect it
shepherd sessions get $SESSION_ID

# 4. Export for analysis
shepherd sessions get $SESSION_ID -o json > debug.json
```

