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
```

