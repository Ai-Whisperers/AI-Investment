#!/bin/bash

# Comprehensive test runner script for local development

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 Waardhaven AutoIndex - Comprehensive Test Suite"
echo "=================================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
fi

# Install test dependencies if needed
echo -e "\n📦 Installing test dependencies..."
pip install -q -r requirements-test.txt

# Run different test categories
run_test_category() {
    local category=$1
    local markers=$2
    local coverage_threshold=$3
    
    echo -e "\n🔬 Running $category tests..."
    
    if pytest tests/ -m "$markers" -v --tb=short --cov=app --cov-report=term-missing --cov-fail-under=$coverage_threshold; then
        echo -e "${GREEN}✅ $category tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ $category tests failed!${NC}"
        return 1
    fi
}

# Track overall success
ALL_PASSED=true

# 1. Fast unit tests
if ! run_test_category "Fast Unit" "fast and unit and not slow" 95; then
    ALL_PASSED=false
fi

# 2. Financial calculations (100% coverage required)
echo -e "\n💰 Running financial calculation tests (100% coverage required)..."
if pytest tests/unit/services -m "financial" -v \
    --cov=app.services.strategy_modules \
    --cov=app.services.performance_modules \
    --cov-report=term-missing \
    --cov-fail-under=100; then
    echo -e "${GREEN}✅ Financial tests passed with 100% coverage!${NC}"
else
    echo -e "${RED}❌ Financial tests failed - THIS IS CRITICAL!${NC}"
    ALL_PASSED=false
fi

# 3. Contract tests
if ! run_test_category "API Contract" "contract" 95; then
    ALL_PASSED=false
fi

# 4. Integration tests (if database is available)
if [[ -n "$DATABASE_URL" ]]; then
    if ! run_test_category "Integration" "integration" 90; then
        ALL_PASSED=false
    fi
else
    echo -e "${YELLOW}⚠️  Skipping integration tests (DATABASE_URL not set)${NC}"
fi

# 5. Performance benchmarks (optional)
if [[ "$1" == "--with-benchmarks" ]]; then
    echo -e "\n⚡ Running performance benchmarks..."
    pytest tests/performance -m "benchmark" --benchmark-only --benchmark-autosave
fi

# Generate coverage report
echo -e "\n📊 Generating coverage report..."
pytest tests/ --cov=app --cov-report=html --cov-report=term
echo -e "Coverage report generated at: htmlcov/index.html"

# Summary
echo -e "\n=================================================="
if $ALL_PASSED; then
    echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
    
    # Show coverage summary
    coverage report | tail -5
    
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please fix before committing.${NC}"
    exit 1
fi