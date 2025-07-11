#!/bin/bash
# test_runner.sh
# Convenient test runner for Enviro+ Data Logger

set -e  # Exit on any error

echo "🧪 Enviro+ Data Logger Test Suite"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Not in a virtual environment. Recommend using: source ~/pyenv/bin/activate"
fi

# Check if test dependencies are installed
if ! python -c "import pytest" 2>/dev/null; then
    print_warning "pytest not found. Installing test dependencies..."
    pip install -r requirements-test.txt
fi

# Parse command line arguments
case ${1:-all} in
    "unit")
        print_status "Running unit tests only..."
        pytest -v -m "unit" tests/test_enviro_logger.py
        ;;
    "integration")
        print_status "Running integration tests only..."
        pytest -v -m "integration" tests/test_enviro_logger.py
        ;;
    "coverage")
        print_status "Running all tests with coverage report..."
        pytest --cov=enhanced_enviro_logger --cov-report=html --cov-report=term tests/test_enviro_logger.py
        print_success "Coverage report generated in htmlcov/index.html"
        ;;
    "quick")
        print_status "Running quick tests (no hardware, no slow tests)..."
        pytest -v -m "not hardware and not slow" tests/test_enviro_logger.py
        ;;
    "hardware")
        print_status "Running hardware-dependent tests..."
        print_warning "Make sure hardware is connected and working!"
        pytest -v -m "hardware" tests/test_enviro_logger.py
        ;;
    "watch")
        print_status "Running tests in watch mode (re-run on file changes)..."
        if command -v pytest-watch &> /dev/null; then
            pytest-watch -- tests/test_enviro_logger.py
        else
            print_error "pytest-watch not installed. Install with: pip install pytest-watch"
            exit 1
        fi
        ;;
    "clean")
        print_status "Cleaning test artifacts..."
        rm -rf htmlcov/
        rm -rf .pytest_cache/
        rm -rf __pycache__/
        find . -name "*.pyc" -delete
        find . -name ".coverage" -delete
        print_success "Cleaned test artifacts"
        ;;
    "all")
        print_status "Running complete test suite..."
        pytest -v tests/test_enviro_logger.py
        ;;
    "help"|"-h"|"--help")
        echo ""
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Test types:"
        echo "  all         - Run all tests (default)"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests only"
        echo "  coverage    - Run tests with coverage report"
        echo "  quick       - Run fast tests only (no hardware)"
        echo "  hardware    - Run hardware-dependent tests"
        echo "  watch       - Run tests in watch mode"
        echo "  clean       - Clean test artifacts"
        echo "  help        - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 quick      # Fast tests for development"
        echo "  $0 coverage   # Full coverage analysis"
        echo "  $0 unit       # Just unit tests"
        echo ""
        exit 0
        ;;
    *)
        print_error "Unknown test type: $1"
        print_status "Use '$0 help' for available options"
        exit 1
        ;;
esac

echo ""
if [ $? -eq 0 ]; then
    print_success "Tests completed successfully! ✅"
else
    print_error "Some tests failed! ❌"
    exit 1
fi
