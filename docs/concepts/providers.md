# Providers

Shepherd supports multiple observability providers. Switch between them or use provider-specific commands.

## Supported Providers

| Provider | Sessions | Traces | Search | Diff |
|----------|----------|--------|--------|------|
| AIOBS | ✅ | ❌ | ✅ | ✅ |
| Langfuse | ✅ | ✅ | ✅ | ❌ |

## Switching Providers

```bash
# Set default provider
shepherd config set provider langfuse
shepherd config set provider aiobs

# Check current provider
shepherd config get provider
```

## AIOBS

[AIOBS](https://github.com/neuralis/aiobs) is an open-source observability SDK.

### Setup

1. Install AIOBS:

```bash
pip install aiobs
```

2. Instrument your code:

```python
import aiobs

aiobs.init(api_key="aiobs_sk_xxx")
# LLM calls are now traced automatically
```

3. Configure Shepherd:

```bash
shepherd config init
```

4. View sessions:

```bash
shepherd sessions list
```

### Configuration

```toml
[default]
provider = "aiobs"

[providers.aiobs]
api_key = "aiobs_sk_xxxx"
endpoint = "https://shepherd-api-48963996968.us-central1.run.app"
```

For self-hosted:

```toml
[providers.aiobs]
endpoint = "https://your-server.com"
```

### Explicit Commands

Always use AIOBS regardless of default provider:

```bash
shepherd aiobs sessions list
shepherd aiobs sessions search --has-errors
shepherd aiobs sessions diff session1 session2
```

## Langfuse

[Langfuse](https://langfuse.com) is an open-source LLM observability platform.

### Setup

1. Get your API keys from [Langfuse Cloud](https://cloud.langfuse.com) or your self-hosted instance.

2. Configure Shepherd:

```bash
shepherd config set langfuse.public_key pk-lf-xxxxx
shepherd config set langfuse.secret_key sk-lf-xxxxx
shepherd config set provider langfuse
```

Or set environment variables:

```bash
export LANGFUSE_PUBLIC_KEY=pk-lf-xxxxx
export LANGFUSE_SECRET_KEY=sk-lf-xxxxx
```

3. View traces:

```bash
shepherd traces list
shepherd sessions list
```

### Configuration

```toml
[default]
provider = "langfuse"

[providers.langfuse]
public_key = "pk-lf-xxxxx"
secret_key = "sk-lf-xxxxx"
host = "https://cloud.langfuse.com"  # Optional, defaults to cloud
```

For self-hosted Langfuse:

```toml
[providers.langfuse]
host = "https://your-langfuse.com"
```

### Explicit Commands

Always use Langfuse regardless of default provider:

```bash
shepherd langfuse traces list
shepherd langfuse traces search --tag production
shepherd langfuse sessions list
shepherd langfuse sessions search --user-id alice
```

## Future Providers

Planned support for:

- **LangSmith**
- **OpenTelemetry**

