# Configuration

Shepherd stores configuration in `~/.shepherd/config.toml`.

## Interactive Setup

```bash
shepherd config init
```

This will prompt you for your provider credentials.

## Environment Variables

```bash
# AIOBS
export AIOBS_API_KEY=aiobs_sk_xxxxxxxxxxxx

# Langfuse
export LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxxxx
export LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxxxxx
```

:::{tip}
Environment variables take precedence over the config file.
:::

## Manual Configuration

Create or edit `~/.shepherd/config.toml`:

```toml
[default]
provider = "langfuse"  # or "aiobs"

[providers.aiobs]
api_key = "aiobs_sk_xxxxxxxxxxxx"
endpoint = "https://shepherd-api-48963996968.us-central1.run.app"

[providers.langfuse]
public_key = "pk-lf-xxxxxxxxxxxx"
secret_key = "sk-lf-xxxxxxxxxxxx"
host = "https://cloud.langfuse.com"  # Optional, defaults to cloud

[cli]
output_format = "table"  # or "json"
color = true
```

## Config Commands

### Show current config

```bash
shepherd config show
```

### Set a value

```bash
# Set default provider
shepherd config set provider langfuse
shepherd config set provider aiobs

# AIOBS settings
shepherd config set aiobs.api_key "aiobs_sk_newkey123"

# Langfuse settings
shepherd config set langfuse.public_key "pk-lf-xxxxx"
shepherd config set langfuse.secret_key "sk-lf-xxxxx"
shepherd config set langfuse.host "https://your-langfuse.com"

# CLI settings
shepherd config set cli.output_format json
```

### Get a value

```bash
shepherd config get provider
shepherd config get aiobs.endpoint
shepherd config get langfuse.host
```

## Available Keys

### General

| Key | Description | Default |
|-----|-------------|---------|
| `provider` | Default provider (`aiobs` or `langfuse`) | `aiobs` |

### AIOBS Provider

| Key | Description | Default |
|-----|-------------|---------|
| `aiobs.api_key` | Your AIOBS API key | (required) |
| `aiobs.endpoint` | AIOBS API endpoint | cloud URL |

### Langfuse Provider

| Key | Description | Default |
|-----|-------------|---------|
| `langfuse.public_key` | Langfuse public API key | (required) |
| `langfuse.secret_key` | Langfuse secret API key | (required) |
| `langfuse.host` | Langfuse host URL | `https://cloud.langfuse.com` |

### CLI Settings

| Key | Description | Default |
|-----|-------------|---------|
| `cli.output_format` | `table` or `json` | `table` |
| `cli.color` | Enable colors | `true` |

