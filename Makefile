.PHONY: test test-backend test-frontend test-all test-coverage test-load clean-test

# Backend Tests
test-backend:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit backend-tests

test-backend-watch:
	docker-compose -f docker-compose.test.yml run --rm backend-tests pytest -v --cov=app -f

test-unit:
	docker-compose -f docker-compose.test.yml run --rm backend-tests pytest -v -m unit

test-integration:
	docker-compose -f docker-compose.test.yml run --rm backend-tests pytest -v -m integration

test-api:
	docker-compose -f docker-compose.test.yml run --rm backend-tests pytest -v -m api

# Coverage Report
test-coverage:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit backend-tests
	@echo "Coverage report generated in backend/htmlcov/index.html"
	@echo "Open with: open backend/htmlcov/index.html (macOS) or xdg-open backend/htmlcov/index.html (Linux)"

# Load Testing
test-load:
	docker-compose -f docker-compose.test.yml up locust-master locust-worker
	@echo "Locust UI available at http://localhost:8089"

# Clean test artifacts
clean-test:
	docker-compose -f docker-compose.test.yml down -v
	rm -rf backend/htmlcov backend/.coverage backend/coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

# Run all tests
test-all: test-backend
	@echo "All tests completed!"

# Security Tests
test-security:
	docker-compose -f docker-compose.test.yml run --rm backend-tests bandit -r app/
	docker-compose -f docker-compose.test.yml run --rm backend-tests safety check

# Code Quality
test-lint:
	docker-compose -f docker-compose.test.yml run --rm backend-tests flake8 app/
	docker-compose -f docker-compose.test.yml run --rm backend-tests black --check app/
	docker-compose -f docker-compose.test.yml run --rm backend-tests mypy app/
