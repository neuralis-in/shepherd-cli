# Testing

## Running Tests

```bash
source venv/bin/activate
pytest
pytest -v
pytest tests/test_client.py
```

## Test Structure

```
tests/
├── conftest.py      # Fixtures
├── test_cli.py      # CLI tests
├── test_client.py   # Client tests
├── test_config.py   # Config tests
└── test_models.py   # Model tests
```

## Writing Tests

### Fixtures

```python
def test_sessions(sample_sessions_response):
    response = SessionsResponse(**sample_sessions_response)
    assert len(response.sessions) == 1
```

### Mocking HTTP

```python
def test_list_sessions(httpx_mock, sample_sessions_response):
    httpx_mock.add_response(
        method="POST",
        url="https://api.example.com/v1/sessions",
        json=sample_sessions_response,
    )
    
    with AIOBSClient(api_key="test", endpoint="https://api.example.com") as client:
        response = client.list_sessions()
    
    assert len(response.sessions) == 1
```

### CLI Tests

```python
from typer.testing import CliRunner
from shepherd.cli.main import app

runner = CliRunner()

def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
```

