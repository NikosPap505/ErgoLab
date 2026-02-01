#!/bin/bash

set -e

echo "📊 Generating Test Coverage Report..."

# Run tests with coverage
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit backend-tests

# Check if coverage meets threshold
COVERAGE=$(docker-compose -f docker-compose.test.yml run --rm backend-tests \
    coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')

THRESHOLD=80

echo ""
echo "Current Coverage: ${COVERAGE}%"
echo "Required Threshold: ${THRESHOLD}%"

if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
    echo "❌ Coverage is below threshold!"
    exit 1
else
    echo "✅ Coverage meets threshold!"
fi

# Open coverage report
if [[ "$OSTYPE" == "darwin"* ]]; then
    open backend/htmlcov/index.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open backend/htmlcov/index.html
fi

docker-compose -f docker-compose.test.yml down
