# Sessions Commands

## `shepherd sessions list`

List all sessions.

```bash
shepherd sessions list [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output format: `table` or `json` |
| `--limit` | `-n` | Max sessions to display |
| `--ids` | | Print only session IDs |

**Examples:**

```bash
shepherd sessions list
shepherd sessions list -n 10
shepherd sessions list -o json
shepherd sessions list --ids
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

Search and filter sessions.

```bash
shepherd sessions search [QUERY] [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `QUERY` | Text search (matches session name, ID, labels, or metadata) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--label` | `-l` | Filter by label (`key=value`, can specify multiple) |
| `--provider` | `-p` | Filter by provider (e.g., `openai`, `anthropic`) |
| `--model` | `-m` | Filter by model name (e.g., `gpt-4`, `claude-3`) |
| `--function` | `-f` | Filter by function name |
| `--after` | | Sessions started after date (`YYYY-MM-DD`) |
| `--before` | | Sessions started before date (`YYYY-MM-DD`) |
| `--has-errors` | | Only show sessions with errors |
| `--evals-failed` | | Only show sessions with failed evaluations |
| `--output` | `-o` | Output format: `table` or `json` |
| `--limit` | `-n` | Max sessions to display |
| `--ids` | | Print only session IDs |

**Examples:**

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

## Scripting

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
```

