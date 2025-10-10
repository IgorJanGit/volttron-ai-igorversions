#!/bin/bash
# VOLTTRON AI Chat Service Test Runner
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
VERBOSE=false
COVERAGE=false
HTML_REPORT=false
INSTALL_DEPS=false
TEST_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -h|--html)
            HTML_REPORT=true
            shift
            ;;
        -i|--install)
            INSTALL_DEPS=true
            shift
            ;;
        -f|--file)
            TEST_FILE="$2"
            shift 2
            ;;
        --help)
            echo "VOLTTRON AI Chat Service Test Runner"
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose     Run tests with verbose output"
            echo "  -c, --coverage    Generate coverage report"
            echo "  -h, --html        Generate HTML coverage report"
            echo "  -i, --install     Install test dependencies first"
            echo "  -f, --file FILE   Run specific test file"
            echo "  --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Run all tests"
            echo "  $0 -v -c                    # Verbose with coverage"
            echo "  $0 -i -c -h                 # Install deps, coverage with HTML"
            echo "  $0 -f test_ai_service.py    # Run specific test file"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🧪 VOLTTRON AI Chat Service Test Runner${NC}"
echo "=" * 50

# Install dependencies if requested
if [[ "$INSTALL_DEPS" == true ]]; then
    echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
    pip install -r test_requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
    echo ""
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing test dependencies...${NC}"
    pip install -r test_requirements.txt
fi

# Build pytest command
PYTEST_CMD="pytest"

if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=chat_app --cov-report=term"
    
    if [[ "$HTML_REPORT" == true ]]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html:htmlcov"
    fi
fi

if [[ -n "$TEST_FILE" ]]; then
    # Since we're in the tests directory, use filename directly
    PYTEST_CMD="$PYTEST_CMD $TEST_FILE"
else
    PYTEST_CMD="$PYTEST_CMD ."  # Current directory (tests/)
fi

# Add additional pytest options
PYTEST_CMD="$PYTEST_CMD --tb=short --strict-markers"

echo -e "${BLUE}🔍 Running tests...${NC}"
echo "Command: $PYTEST_CMD"
echo ""

# Set environment variable for testing
export TESTING=true
export OPENAI_API_KEY=${OPENAI_API_KEY:-"test-key-for-testing"}

# Run the tests
if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    
    if [[ "$HTML_REPORT" == true ]]; then
        echo -e "${BLUE}📊 HTML coverage report generated: htmlcov/index.html${NC}"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi