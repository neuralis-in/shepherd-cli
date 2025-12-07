# 🐑 Shepherd CLI

Debug your AI agents like you debug your code.

## Installation

```bash
pip install shepherd-cli
```

For enhanced shell experience (tab completion, history):

```bash
pip install shepherd-cli[shell]
```

## Quick Start

### 1. Configure your API key

```bash
shepherd config init
```

Or set the environment variable:

```bash
export AIOBS_API_KEY=aiobs_sk_xxxx
```

### 2. List sessions

```bash
shepherd sessions list
```

### 3. Get session details

```bash
shepherd sessions get <session-id>
```

### 4. Interactive shell

```bash
shepherd shell
```

## Commands

### Config

```bash
shepherd config init          # Interactive setup
shepherd config show          # Show current config
shepherd config set <key> <value>
shepherd config get <key>
```

### Sessions

```bash
shepherd sessions list          # List all sessions
shepherd sessions list -n 10    # Limit to 10 sessions
shepherd sessions list -o json  # Output as JSON
shepherd sessions list --ids    # List only session IDs (for scripting)

shepherd sessions get <id>      # Get session details with trace tree
shepherd sessions get <id> -o json  # Output as JSON

# Search and filter sessions
shepherd sessions search "query"              # Search by name, ID, labels, or metadata
shepherd sessions search --label env=prod     # Filter by label
shepherd sessions search --provider openai    # Filter by provider
shepherd sessions search --model gpt-4        # Filter by model
shepherd sessions search --function my_func   # Filter by function name
shepherd sessions search --after 2025-12-01   # Sessions after date
shepherd sessions search --before 2025-12-07  # Sessions before date
shepherd sessions search --has-errors         # Only sessions with errors
shepherd sessions search --evals-failed       # Only sessions with failed evaluations

# Combine filters
shepherd sessions search --provider anthropic --label user=alice --after 2025-12-01
shepherd sessions search "agent" --model claude-3 --evals-failed -n 5
```

### Shell

```bash
shepherd shell                  # Start interactive shell
```

Inside the shell:
```
shepherd > sessions list
shepherd > sessions get <id>
shepherd > config show
shepherd > help
shepherd > exit
```

Features:
- Tab completion
- Command history (persisted)
- Auto-suggestions
- `/command` or `command` syntax

## Configuration

Config file location: `~/.shepherd/config.toml`

```toml
[default]
provider = "aiobs"

[providers.aiobs]
api_key = "aiobs_sk_xxxx"
endpoint = "https://shepherd-api-48963996968.us-central1.run.app"

[cli]
output_format = "table"
color = true
```

## Development

### Setup

```bash
git clone https://github.com/neuralis/shepherd-cli
cd shepherd-cli
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Project Structure

```
shepherd-cli/
├── src/shepherd/
│   ├── cli/           # CLI commands (typer)
│   ├── models/        # Pydantic models
│   ├── providers/     # API clients
│   └── config.py      # Configuration management
├── tests/             # Test suite
└── pyproject.toml
```

## License

MIT
