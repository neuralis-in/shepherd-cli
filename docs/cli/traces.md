# Traces Commands

Traces commands are available for Langfuse provider. They allow you to list, inspect, and search through your LLM traces.

## `shepherd traces list`

List traces from Langfuse.

```bash
shepherd traces list [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output format: `table` or `json` |
| `--limit` | `-n` | Max traces to display (default: 50) |
| `--page` | `-p` | Page number |
| `--name` | | Filter by trace name |
| `--user-id` | `-u` | Filter by user ID |
| `--session-id` | `-s` | Filter by session ID |
| `--tag` | `-t` | Filter by tag (can specify multiple) |
| `--from` | | Filter traces after timestamp |
| `--to` | | Filter traces before timestamp |
| `--ids` | | Print only trace IDs |

**Examples:**

```bash
shepherd traces list
shepherd traces list -n 20
shepherd traces list --name "chat-completion"
shepherd traces list --user-id alice --tag production
shepherd traces list -o json
shepherd traces list --ids
```

## `shepherd traces get`

Get details for a specific trace.

```bash
shepherd traces get <trace-id> [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output format: `table` or `json` |

**Examples:**

```bash
shepherd traces get abc123
shepherd traces get abc123 -o json
```

## `shepherd traces search`

Search and filter traces with advanced criteria.

```bash
shepherd traces search [QUERY] [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `QUERY` | Text search (matches trace name, ID, user ID, session ID, tags, release) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | | Filter by trace name |
| `--user-id` | `-u` | Filter by user ID |
| `--session-id` | `-s` | Filter by session ID |
| `--tag` | `-t` | Filter by tag (can specify multiple) |
| `--release` | `-r` | Filter by release version |
| `--min-cost` | | Minimum total cost |
| `--max-cost` | | Maximum total cost |
| `--min-latency` | | Minimum latency in seconds |
| `--max-latency` | | Maximum latency in seconds |
| `--from` / `--after` | | Filter traces after timestamp |
| `--to` / `--before` | | Filter traces before timestamp |
| `--output` | `-o` | Output format: `table` or `json` |
| `--limit` | `-n` | Max traces to display (default: 50) |
| `--page` | `-p` | Page number |
| `--ids` | | Print only trace IDs |

**Examples:**

```bash
# Text search
shepherd traces search "my-agent"
shepherd traces search "production"

# Filter by user and tags
shepherd traces search --user-id alice
shepherd traces search --tag production --tag critical
shepherd traces search -u bob -t development

# Filter by cost and latency
shepherd traces search --min-cost 0.01
shepherd traces search --max-latency 5.0
shepherd traces search --min-cost 0.001 --max-cost 0.10

# Filter by release
shepherd traces search --release v2.1.0
shepherd traces search -r v2.0.0-beta

# Date range
shepherd traces search --from 2025-12-01
shepherd traces search --after 2025-12-01 --before 2025-12-07

# Combined filters
shepherd traces search --tag production --min-cost 0.01 --max-latency 10.0
shepherd traces search "agent" --user-id alice --release v2.1.0

# Output options
shepherd traces search --tag production -o json
shepherd traces search --min-cost 0.05 --ids
```

## Explicit Langfuse Commands

Use these to bypass provider routing:

```bash
shepherd langfuse traces list
shepherd langfuse traces get abc123
shepherd langfuse traces search --tag production
```

## Scripting

```bash
# Process traces in a loop
for tid in $(shepherd traces list --ids -n 10); do
    shepherd traces get "$tid" -o json > "trace_${tid}.json"
done

# Pipe to jq
shepherd traces list -o json | jq '.traces[].name'

# Get latest trace
LATEST=$(shepherd traces list --ids -n 1)
shepherd traces get "$LATEST"

# Find expensive traces
shepherd traces search --min-cost 0.10 --ids

# Export production traces
shepherd traces search --tag production -o json > production_traces.json

# Analyze slow traces
for tid in $(shepherd traces search --min-latency 10.0 --ids); do
    echo "Analyzing trace: $tid"
    shepherd traces get "$tid" -o json | jq '.latency, .totalCost'
done
```
