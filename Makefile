# Makefile for Smart File Organizer Testing
# Provides convenient commands for testing and development

.PHONY: help test test-quick test-coverage test-unit test-integration install-deps clean lint format

# Default target
help:
	@echo "Smart File Organizer - Test Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install-deps    Install all testing dependencies"
	@echo "  install-dev     Install development dependencies"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test           Run full test suite with coverage"
	@echo "  test-quick     Run tests without coverage (faster)"
	@echo "  test-unit      Run only unit tests"
	@echo "  test-reanalysis Run re-analysis feature tests"
	@echo "  test-integration  Run only integration tests"
	@echo "  test-coverage  Generate detailed coverage report"
	@echo ""
	@echo "Quality Commands:"
	@echo "  lint           Run code linting (flake8)"
	@echo "  format         Format code with black"
	@echo "  type-check     Run type checking with mypy"
	@echo ""
	@echo "Cleanup Commands:"
	@echo "  clean          Remove test artifacts and cache"
	@echo "  clean-all      Remove all generated files"

# Installation targets
install-deps:
	@echo "📦 Installing test dependencies..."
	pip install -r requirements-test.txt

install-dev: install-deps
	@echo "🔧 Installing development dependencies..."
	pip install -e .

# Testing targets
test:
	@echo "🧪 Running full test suite with coverage..."
	python -m pytest test_file_organizer.py -v --cov=file_organizer --cov-report=html --cov-report=term

test-quick:
	@echo "⚡ Running quick tests..."
	python -m pytest test_file_organizer.py -v --tb=short -x

test-unit:
	@echo "🔬 Running unit tests..."
	python -m pytest test_file_organizer.py::TestSmartFileOrganizer -v

test-reanalysis:
	@echo "🔄 Testing re-analysis functionality..."
	python -m pytest test_file_organizer.py -k "reanalyz" -v

test-integration: test-unit test-reanalysis
	@echo "🔗 Running integration tests..."
	python -m pytest test_file_organizer.py::TestIntegration -v

test-coverage:
	@echo "📊 Generating detailed coverage report..."
	python -m pytest test_file_organizer.py --cov=file_organizer --cov-report=html --cov-report=term-missing
	@echo "Coverage report available at: htmlcov/index.html"

# Code quality targets
lint:
	@echo "🔍 Running code linting..."
	flake8 file_organizer.py test_file_organizer.py --max-line-length=100

format:
	@echo "✨ Formatting code..."
	black file_organizer.py test_file_organizer.py --line-length=100

type-check:
	@echo "🔎 Running type checking..."
	mypy file_organizer.py --ignore-missing-imports

# Cleanup targets
clean:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.pyc
	rm -rf __pycache__/
	rm -rf test_data/

clean-all: clean
	@echo "🧹 Cleaning all generated files..."
	rm -rf FileOrganizer_Logs/
	rm -rf Organized_*/

# Development workflow
dev-test: format lint test-quick
	@echo "✅ Development testing complete!"

ci-test: install-deps lint type-check test
	@echo "✅ CI testing complete!"

# File watching (requires entr: brew install entr)
watch-test:
	@echo "👀 Watching files for changes..."
	find . -name "*.py" | entr -c make test-quick% 
