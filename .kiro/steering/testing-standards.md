# Testing Standards

## Preferred Libraries

| Purpose | Library |
|---|---|
| Test runner & assertions | `pytest` |
| Mocking | `unittest.mock` (stdlib) |
| HTTP mocking | `responses` or `httpretty` |
| Coverage | `pytest-cov` |
| Async tests | `pytest-asyncio` |

Install dev dependencies:
```
pytest pytest-cov pytest-asyncio responses
```

## File Organization

```
project/
├── src/
│   └── module/
│       └── service.py
└── tests/
    ├── conftest.py          # shared fixtures
    ├── unit/
    │   └── test_service.py
    └── integration/
        └── test_service_api.py
```

- Mirror `src/` structure under `tests/`
- Prefix all test files with `test_`
- Prefix all test functions with `test_`
- Put shared fixtures in `conftest.py`

## Unit Tests

Test a single function/class in isolation. Mock all external dependencies.

```python
# tests/unit/test_service.py
from unittest.mock import MagicMock, patch
from src.module.service import UserService

def test_get_user_returns_user_when_found():
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"id": "usr_1", "name": "Jane"}

    service = UserService(repo=mock_repo)
    result = service.get_user("usr_1")

    assert result["name"] == "Jane"
    mock_repo.find_by_id.assert_called_once_with("usr_1")

def test_get_user_raises_when_not_found():
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = None

    service = UserService(repo=mock_repo)

    with pytest.raises(NotFoundError):
        service.get_user("usr_999")
```

### Naming Convention

```
test_<unit>_<condition>_<expected_outcome>
```

Examples:
- `test_create_user_with_duplicate_email_raises_conflict`
- `test_parse_token_when_expired_returns_none`

## Integration Tests

Test multiple components together, including real I/O (DB, HTTP). Use fixtures to set up/tear down state.

```python
# tests/integration/test_service_api.py
import responses as rsps
import pytest

@pytest.fixture
def mock_external_api():
    with rsps.RequestsMock() as r:
        r.add(rsps.GET, "https://api.example.com/users/1",
              json={"id": "1", "name": "Jane"}, status=200)
        yield r

def test_fetch_user_from_external_api(mock_external_api):
    result = fetch_user("1")
    assert result["name"] == "Jane"
```

- Integration tests live under `tests/integration/`
- Never call real external services in CI — always mock at the network boundary
- Use `pytest` fixtures for DB setup/teardown, not manual setup in test body

## Mocking Approaches

| Scenario | Approach |
|---|---|
| Injected dependency | Pass `MagicMock()` directly |
| Module-level import | `@patch("module.path.ClassName")` |
| External HTTP | `responses` library |
| Env variables | `monkeypatch.setenv` (pytest built-in) |
| Time/datetime | `@patch("module.datetime")` or `freezegun` |

Prefer dependency injection over `@patch` where possible — it makes tests simpler and avoids patching path fragility.

## Assertion Style

Use plain `assert` with pytest (not `unittest` assert methods):

```python
# preferred
assert result == expected
assert result is None
assert "key" in response
assert len(items) == 3

# avoid
self.assertEqual(result, expected)
self.assertIsNone(result)
```

For exceptions:
```python
with pytest.raises(ValueError, match="invalid email"):
    validate_email("bad")
```

## Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from src.db import create_engine, Session

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session
        session.rollback()
```

- Use `scope="session"` for expensive setup (DB engine, HTTP client)
- Use default `scope="function"` for anything that mutates state

## Coverage Expectations

| Layer | Minimum Coverage |
|---|---|
| Business logic / services | 90% |
| Utilities / helpers | 85% |
| API handlers / routes | 80% |
| Overall project | 80% |

Run with coverage:
```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

Configure in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit = ["*/__init__.py"]
```

## General Rules

- Each test must be independent — no shared mutable state between tests
- One logical assertion per test (multiple `assert` lines are fine if testing one concept)
- Tests must not write to disk, network, or external services without explicit mocking
- Keep test setup minimal — if setup is complex, extract to a fixture
- Delete tests only when the feature they cover is removed
