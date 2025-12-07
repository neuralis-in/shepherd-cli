# Config Commands

## `shepherd config init`

Interactive configuration setup.

```bash
shepherd config init
```

## `shepherd config show`

Display current configuration.

```bash
shepherd config show
```

Output:

```
╭─────── Config (~/.shepherd/config.toml) ────────╮
│ Provider: aiobs                                 │
│                                                 │
│ AIOBS:                                          │
│   API Key:  aiobs_sk_x...xxxx                   │
│   Endpoint: https://shepherd-api-...            │
│                                                 │
│ CLI:                                            │
│   Output Format: table                          │
│   Color:         True                           │
╰─────────────────────────────────────────────────╯
```

## `shepherd config set`

Set a configuration value.

```bash
shepherd config set <key> <value>
```

**Examples:**

```bash
shepherd config set aiobs.api_key "aiobs_sk_xxx"
shepherd config set cli.output_format json
```

**Available Keys:**

| Key | Type | Description |
|-----|------|-------------|
| `aiobs.api_key` | string | AIOBS API key |
| `aiobs.endpoint` | string | API endpoint URL |
| `cli.output_format` | `table` \| `json` | Output format |
| `cli.color` | `true` \| `false` | Enable colors |

## `shepherd config get`

Get a configuration value.

```bash
shepherd config get <key>
```

