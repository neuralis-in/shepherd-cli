# Contributing

## Setup

```bash
git clone https://github.com/neuralis/shepherd-cli
cd shepherd-cli
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Project Structure

```
shepherd-cli/
├── src/shepherd/
│   ├── cli/           # CLI commands
│   ├── models/        # Pydantic models
│   ├── providers/     # API clients
│   └── config.py      # Configuration
├── tests/             # Test suite
└── docs/              # Documentation
```

## Making Changes

1. Create a branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make changes with type hints and docstrings

3. Add tests:
   ```bash
   pytest
   ```

4. Format code:
   ```bash
   ruff check --fix .
   ruff format .
   ```

5. Submit a PR

## Adding a Provider

1. Create `src/shepherd/providers/newprovider.py`
2. Implement `list_sessions()` and `get_session()`
3. Add config support
4. Add tests
5. Update docs

