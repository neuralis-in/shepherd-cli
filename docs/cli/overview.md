# CLI Overview

## Command Structure

```
shepherd [OPTIONS] COMMAND [ARGS]
```

## Global Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--install-completion` | Install shell completion |
| `--show-completion` | Show completion script |

## Commands

| Command | Description |
|---------|-------------|
| `version` | Show version information |
| `shell` | Start interactive shell |
| `config` | Manage configuration |
| `sessions` | List and inspect sessions (routes to current provider) |
| `traces` | List and inspect traces (Langfuse only) |
| `langfuse` | Langfuse-specific commands |
| `aiobs` | AIOBS-specific commands |

## Provider-Aware Commands

Top-level `sessions` and `traces` commands route to your default provider:

```bash
# Set default provider
shepherd config set provider langfuse

# These now use Langfuse
shepherd sessions list
shepherd sessions search --user-id alice
shepherd traces list
shepherd traces search --tag production
```

## Explicit Provider Commands

Use provider-specific commands regardless of default:

```bash
# Always use Langfuse
shepherd langfuse traces list
shepherd langfuse sessions search --min-cost 0.01

# Always use AIOBS
shepherd aiobs sessions list
shepherd aiobs sessions search --has-errors
```

## Output Formats

```bash
# Table (default)
shepherd sessions list

# JSON
shepherd sessions list -o json

# IDs only (for scripting)
shepherd sessions list --ids
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AIOBS_API_KEY` | AIOBS API key (overrides config) |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key (overrides config) |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key (overrides config) |
| `NO_COLOR` | Disable colored output |

