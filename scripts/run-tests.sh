#!/bin/bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 ErgoLab Test Suite${NC}\n"

# Parse arguments
TEST_TYPE=${1:-all}

# Function to run backend tests
run_backend_tests() {
    echo -e "${YELLOW}Running Backend Tests...${NC}"
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit backend-tests
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backend tests passed${NC}\n"
    else
        echo -e "${RED}✗ Backend tests failed${NC}\n"
        exit 1
    fi
}

# Function to run frontend tests
run_frontend_tests() {
    echo -e "${YELLOW}Running Frontend Tests...${NC}"
    cd portal-web
    npm test -- --coverage --watchAll=false
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend tests passed${NC}\n"
        cd ..
    else
        echo -e "${RED}✗ Frontend tests failed${NC}\n"
        cd ..
        exit 1
    fi
}

# Function to run security tests
run_security_tests() {
    echo -e "${YELLOW}Running Security Scans...${NC}"
    docker-compose -f docker-compose.test.yml run --rm backend-tests bandit -r app/
    docker-compose -f docker-compose.test.yml run --rm backend-tests safety check
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Security scans passed${NC}\n"
    else
        echo -e "${YELLOW}⚠ Security issues found${NC}\n"
    fi
}

# Function to generate coverage report
generate_coverage() {
    echo -e "${YELLOW}Generating Coverage Report...${NC}"
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit backend-tests
    
    echo -e "${GREEN}Coverage report available at: backend/htmlcov/index.html${NC}\n"
}

# Main test execution
case $TEST_TYPE in
    backend)
        run_backend_tests
        ;;
    frontend)
        run_frontend_tests
        ;;
    security)
        run_security_tests
        ;;
    coverage)
        generate_coverage
        ;;
    all)
        run_backend_tests
        run_frontend_tests
        run_security_tests
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Usage: ./scripts/run-tests.sh [backend|frontend|security|coverage|all]"
        exit 1
        ;;
esac

# Cleanup
echo -e "${YELLOW}Cleaning up...${NC}"
docker-compose -f docker-compose.test.yml down

echo -e "${GREEN}✨ All tests completed successfully!${NC}"
