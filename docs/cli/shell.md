# Interactive Shell

## `shepherd shell`

Start an interactive shell for exploring sessions and managing configuration.

```bash
shepherd shell
```

The shell provides a REPL (Read-Eval-Print Loop) experience with command history, tab completion, and auto-suggestions.

## Features

| Feature | Description |
|---------|-------------|
| **Command History** | Persisted across sessions (`~/.shepherd/.shell_history`) |
| **Tab Completion** | Complete commands as you type |
| **Auto-suggestions** | Suggestions from command history |
| **Slash Syntax** | Use `/command` or `command` syntax |

## Welcome Screen

```
╭───────────────────────────────────────────────────────────────────╮
│                                                                   │
│   🐑 Shepherd Shell v0.1.0                                        │
│   Debug your AI agents like you debug your code                   │
│                                                                   │
│   Type help for available commands, exit to quit.                 │
│                                                                   │
╰───────────────────────────────────────────────────────────────────╯

shepherd > 
```

## Available Commands

### Sessions

| Command | Description |
|---------|-------------|
| `sessions list` | List all sessions |
| `sessions get <id>` | Get details for a specific session |
| `sessions search [query]` | Search and filter sessions |
| `sessions diff <id1> <id2>` | Compare two sessions |

### Config

| Command | Description |
|---------|-------------|
| `config init` | Initialize configuration interactively |
| `config show` | Show current configuration |
| `config set <key> <value>` | Set a configuration value |
| `config get <key>` | Get a configuration value |

### Shell

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `clear` | Clear the screen |
| `version` | Show version information |
| `exit` / `quit` | Exit the shell |

## Examples

### Basic Usage

```bash
# Start the shell
shepherd shell

# Inside the shell:
shepherd > sessions list
shepherd > sessions get abc123
shepherd > config show
shepherd > exit
```

### Using Options

```bash
shepherd > sessions list --limit 5
shepherd > sessions list -o json
shepherd > sessions list --ids
shepherd > sessions get abc123 -o json
```

### Searching Sessions

```bash
# Text search
shepherd > sessions search "my-agent"

# Filter by label
shepherd > sessions search --label env=production
shepherd > sessions search -l env=prod -l user=alice

# Filter by provider and model
shepherd > sessions search -p openai -m gpt-4

# Date and error filters
shepherd > sessions search --after 2025-12-01 --has-errors
shepherd > sessions search --evals-failed

# Combined filters
shepherd > sessions search -p anthropic -l user=alice --evals-failed -n 5
```

### Comparing Sessions

```bash
# Compare two sessions
shepherd > sessions diff abc123 def456

# Output diff as JSON
shepherd > sessions diff abc123 def456 -o json
```

The diff command shows:
- **Metadata**: Duration, labels changes
- **LLM Calls**: Token usage, latency, error comparison
- **System Prompts**: Differences in system prompts used
- **Request Parameters**: Temperature, max tokens, tools changes
- **Responses**: Content length, tool calls, stop reasons

### Slash Syntax

Both syntaxes work identically:

```bash
shepherd > sessions list
shepherd > /sessions list
```

### Tab Completion

```bash
shepherd > sess<TAB>
# Completes to: sessions

shepherd > sessions <TAB>
# Shows: list, get
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Tab` | Auto-complete command |
| `↑` / `↓` | Navigate command history |
| `Ctrl+C` | Cancel current input |
| `Ctrl+D` | Exit shell |

## Installation

The shell works out of the box. For enhanced features (tab completion, history), install the shell extras:

```bash
pip install shepherd-cli[shell]
```

This installs `prompt_toolkit` for a better interactive experience. Without it, the shell falls back to basic input.

## Tips

1. **Quick session inspection**: Use `sessions list --ids -n 1` to get the latest session ID, then `sessions get <id>` to inspect it.

2. **JSON for scripting**: While in the shell, use `-o json` for machine-readable output you can copy.

3. **Clear clutter**: Use `clear` to reset the screen between commands.

4. **Find problem sessions**: Use `sessions search --has-errors` or `sessions search --evals-failed` to quickly find sessions that need attention.

5. **Filter by environment**: Use labels to filter sessions by environment, e.g., `sessions search -l env=production`.

6. **Compare runs**: Use `sessions diff <baseline> <experiment>` to compare two sessions and see what changed in prompts, parameters, and responses.

