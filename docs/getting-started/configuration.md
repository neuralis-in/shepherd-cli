# Configuration

Shepherd stores configuration in `~/.shepherd/config.toml`.

## Interactive Setup

```bash
shepherd config init
```

This will prompt you for:

1. **API Key** - Your AIOBS API key
2. **Endpoint** - API endpoint (defaults to AIOBS cloud)

## Environment Variables

```bash
export AIOBS_API_KEY=aiobs_sk_xxxxxxxxxxxx
```

:::{tip}
Environment variables take precedence over the config file.
:::

## Manual Configuration

Create or edit `~/.shepherd/config.toml`:

```toml
[default]
provider = "aiobs"

[providers.aiobs]
api_key = "aiobs_sk_xxxxxxxxxxxx"
endpoint = "https://shepherd-api-48963996968.us-central1.run.app"

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
shepherd config set aiobs.api_key "aiobs_sk_newkey123"
shepherd config set cli.output_format json
```

### Get a value

```bash
shepherd config get aiobs.endpoint
```

## Available Keys

| Key | Description | Default |
|-----|-------------|---------|
| `aiobs.api_key` | Your AIOBS API key | (required) |
| `aiobs.endpoint` | AIOBS API endpoint | cloud URL |
| `cli.output_format` | `table` or `json` | `table` |
| `cli.color` | Enable colors | `true` |

