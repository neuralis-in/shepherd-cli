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
| `config` | Manage configuration |
| `sessions` | List and inspect sessions |

## Output Formats

```bash
# Table (default)
shepherd sessions list

# JSON
shepherd sessions list -o json
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AIOBS_API_KEY` | API key (overrides config) |
| `NO_COLOR` | Disable colored output |

