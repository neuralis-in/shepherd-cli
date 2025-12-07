# Providers

Shepherd is provider-agnostic. Currently supports AIOBS.

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

4. View traces:

```bash
shepherd sessions list
```

## Future Providers

Planned support for:

- **LangSmith**
- **Langfuse**
- **OpenTelemetry**

## Configuration

```toml
[providers.aiobs]
api_key = "aiobs_sk_xxxx"
endpoint = "https://shepherd-api-48963996968.us-central1.run.app"
```

For self-hosted:

```toml
[providers.aiobs]
endpoint = "https://your-server.com"
```

