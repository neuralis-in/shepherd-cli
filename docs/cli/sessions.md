# Sessions Commands

Sessions commands work with both AIOBS and Langfuse providers. The available options vary by provider.

## `shepherd sessions list`

List all sessions.

```bash
shepherd sessions list [OPTIONS]
```

**Options:**

| Option | Short | Description | AIOBS | Langfuse |
|--------|-------|-------------|-------|----------|
| `--output` | `-o` | Output format: `table` or `json` | ✅ | ✅ |
| `--limit` | `-n` | Max sessions to display | ✅ | ✅ |
| `--page` | `-p` | Page number | ❌ | ✅ |
| `--from` | | Filter after timestamp | ❌ | ✅ |
| `--to` | | Filter before timestamp | ❌ | ✅ |
| `--ids` | | Print only session IDs | ✅ | ✅ |

**Examples:**

```bash
shepherd sessions list
shepherd sessions list -n 10
shepherd sessions list -o json
shepherd sessions list --ids

# Langfuse pagination
shepherd sessions list --page 2 -n 20
shepherd sessions list --from 2025-12-01
```

## `shepherd sessions get`

Get session details.

```bash
shepherd sessions get <session-id> [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output format: `table` or `json` |

**Examples:**

```bash
shepherd sessions get be393d0d-7139-4241-a00d-e3c9ff4f9fcf
shepherd sessions get be393d0d-7139-4241-a00d-e3c9ff4f9fcf -o json
```

## `shepherd sessions search`

Search and filter sessions. Options vary by provider.

```bash
shepherd sessions search [QUERY] [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `QUERY` | Text search (matches session ID, name, labels, metadata, or user IDs) |

### AIOBS Options

| Option | Short | Description |
|--------|-------|-------------|
| `--label` | `-l` | Filter by label (`key=value`, can specify multiple) |
| `--provider` | `-p` | Filter by LLM provider (e.g., `openai`, `anthropic`) |
| `--model` | `-m` | Filter by model name (e.g., `gpt-4`, `claude-3`) |
| `--function` | `-f` | Filter by function name |
| `--after` | | Sessions started after date (`YYYY-MM-DD`) |
| `--before` | | Sessions started before date (`YYYY-MM-DD`) |
| `--has-errors` | | Only show sessions with errors |
| `--evals-failed` | | Only show sessions with failed evaluations |
| `--output` | `-o` | Output format: `table` or `json` |
| `--limit` | `-n` | Max sessions to display |
| `--ids` | | Print only session IDs |

### Langfuse Options

| Option | Short | Description |
|--------|-------|-------------|
| `--user-id` | `-u` | Filter by user ID |
| `--min-traces` | | Minimum number of traces |
| `--max-traces` | | Maximum number of traces |
| `--min-cost` | | Minimum total cost |
| `--max-cost` | | Maximum total cost |
| `--from` / `--after` | | Sessions after timestamp |
| `--to` / `--before` | | Sessions before timestamp |
| `--output` | `-o` | Output format: `table` or `json` |
| `--limit` | `-n` | Max sessions to display |
| `--page` | `-p` | Page number |
| `--ids` | | Print only session IDs |

### AIOBS Examples

```bash
# Text search
shepherd sessions search "my-agent"

# Filter by label
shepherd sessions search --label env=production
shepherd sessions search -l env=prod -l user=alice

# Filter by provider and model
shepherd sessions search --provider openai
shepherd sessions search -p anthropic -m claude-3

# Filter by function
shepherd sessions search --function process_data

# Date range
shepherd sessions search --after 2025-12-01
shepherd sessions search --after 2025-12-01 --before 2025-12-07

# Error and eval filters
shepherd sessions search --has-errors
shepherd sessions search --evals-failed

# Combined filters
shepherd sessions search "agent" --provider openai --model gpt-4 --has-errors
shepherd sessions search -p anthropic -l user=alice --after 2025-12-01 -n 10
```

### Langfuse Examples

```bash
# Text search (matches session ID, user IDs)
shepherd sessions search "user-123"

# Filter by user
shepherd sessions search --user-id alice
shepherd sessions search -u bob

# Filter by trace count
shepherd sessions search --min-traces 5
shepherd sessions search --max-traces 10

# Filter by cost
shepherd sessions search --min-cost 0.01
shepherd sessions search --min-cost 0.001 --max-cost 0.10

# Date range
shepherd sessions search --from 2025-12-01
shepherd sessions search --after 2025-12-01 --before 2025-12-07

# Combined filters
shepherd sessions search --user-id alice --min-cost 0.01
shepherd sessions search --min-traces 5 --from 2025-12-01 -n 20

# Output options
shepherd sessions search --min-cost 0.01 -o json
shepherd sessions search --user-id alice --ids
```

## `shepherd sessions diff` (AIOBS only)

Compare two sessions and show their differences. This command is only available for AIOBS provider.

```bash
shepherd sessions diff <session-id1> <session-id2> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `SESSION_ID1` | First session ID (baseline) |
| `SESSION_ID2` | Second session ID (comparison) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output format: `table` or `json` |

**What it compares:**

- **Metadata**: Duration, labels, meta fields
- **LLM Calls**: Total calls, tokens (input/output/total), latency, errors
- **Provider Distribution**: Calls per provider (OpenAI, Anthropic, etc.)
- **Model Distribution**: Calls per model (gpt-4, claude-3, etc.)
- **Function Events**: Total calls, unique functions, duration
- **Trace Structure**: Trace depth, root nodes
- **Evaluations**: Total, passed, failed, pass rate
- **System Prompts**: Compares system prompts used in each session
- **Request Parameters**: Temperature, max tokens, tools used, streaming
- **Responses**: Content length, tool calls, stop reasons

**Examples:**

```bash
# Basic comparison
shepherd sessions diff abc123 def456

# Output as JSON
shepherd sessions diff abc123 def456 -o json

# Compare baseline vs experiment
shepherd sessions diff baseline-session-id experiment-session-id

# Explicit AIOBS command
shepherd aiobs sessions diff abc123 def456
```

**Example Output:**

```
╭───────────────────── Session Diff ─────────────────────╮
│ Session 1: abc12345... (baseline-agent)                │
│ Session 2: def67890... (updated-agent)                 │
╰────────────────────────────────────────────────────────╯

┏━━━━━━━━━━━ LLM Calls Summary ━━━━━━━━━━━┓
│ Metric        │ S1    │ S2    │ Delta   │
├───────────────┼───────┼───────┼─────────┤
│ Total Calls   │ 5     │ 8     │ +3      │
│ Total Tokens  │ 1,200 │ 1,800 │ +600    │
│ Avg Latency   │ 2.0s  │ 1.5s  │ -500ms  │
└───────────────┴───────┴───────┴─────────┘

⚠ System prompts differ between sessions

Tools Used:
  + Added: run_security_scan
  - Removed: search_code
  Common: get_file_contents
```

## Explicit Provider Commands

Use provider-specific commands to bypass routing:

```bash
# AIOBS sessions
shepherd aiobs sessions list
shepherd aiobs sessions search --has-errors
shepherd aiobs sessions diff session1 session2

# Langfuse sessions
shepherd langfuse sessions list
shepherd langfuse sessions search --user-id alice
shepherd langfuse sessions get session-abc
```

## Scripting

### AIOBS Examples

```bash
# Process sessions in a loop
for sid in $(shepherd sessions list --ids -n 5); do
    shepherd sessions get "$sid" -o json > "session_${sid}.json"
done

# Pipe to jq
shepherd sessions list -o json | jq '.sessions[].name'

# Get latest session
LATEST=$(shepherd sessions list --ids -n 1)
shepherd sessions get "$LATEST"

# Find sessions with errors and export
for sid in $(shepherd sessions search --has-errors --ids); do
    shepherd sessions get "$sid" -o json > "error_session_${sid}.json"
done

# Search for production sessions with failed evals
shepherd sessions search -l env=production --evals-failed -o json | jq '.sessions'

# Compare latest two sessions
SESSIONS=($(shepherd sessions list --ids -n 2))
shepherd sessions diff "${SESSIONS[0]}" "${SESSIONS[1]}"

# Export diff to JSON for analysis
shepherd sessions diff session-v1 session-v2 -o json > diff_report.json
```

### Langfuse Examples

```bash
# Process sessions in a loop
for sid in $(shepherd langfuse sessions list --ids -n 5); do
    shepherd langfuse sessions get "$sid" -o json > "session_${sid}.json"
done

# Pipe to jq
shepherd langfuse sessions list -o json | jq '.sessions[].id'

# Find expensive sessions
shepherd langfuse sessions search --min-cost 0.05 -o json

# Export user sessions
shepherd langfuse sessions search --user-id alice -o json > alice_sessions.json

# Get sessions with many traces
for sid in $(shepherd langfuse sessions search --min-traces 10 --ids); do
    echo "Session $sid has 10+ traces"
done
```

