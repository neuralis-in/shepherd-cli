# 🐑 Shepherd CLI

Debug your AI agents like you debug your code.

## Installation

```bash
pip install shepherd-cli
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
```

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
