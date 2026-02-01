# ErgoLab Backend Tests

## Test Structure

```
tests/
├── conftest.py           # Test fixtures and configuration
├── test_auth.py          # Authentication tests
├── test_permissions.py   # Permission system tests
├── test_projects.py      # Project API tests
├── test_reports.py       # Reports API tests
├── test_database.py      # Database tests
├── test_email.py         # Email service tests
└── load/
    └── locustfile.py     # Load testing scenarios
```

## Running Tests

### With Docker (Recommended)

```bash
# Run all tests
make test-backend

# Run specific test types
make test-unit
make test-integration
make test-api

# Generate coverage report
make test-coverage

# Run load tests
make test-load

# Run security scans
make test-security
```

### Without Docker

```bash
cd backend

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Run specific markers
pytest -m unit
pytest -m api
pytest -m database
```

## Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.database` - Database tests
- `@pytest.mark.slow` - Slow running tests

## Coverage Requirements

- Minimum coverage: 80%
- Critical modules: 90%+

## Writing Tests

### Example Test

```python
import pytest
from fastapi import status

@pytest.mark.api
def test_create_project(client, manager_token):
    """Test creating a project"""
    response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "name": "Test Project",
            "code": "TEST001",
            "location": "Athens"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Test Project"
```

## Load Testing

Start Locust UI:
```bash
make test-load
# Open http://localhost:8089
```

Configure:
- Users: 100
- Spawn rate: 10/sec
- Host: http://localhost:8000
