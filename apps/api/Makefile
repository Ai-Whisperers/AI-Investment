# Makefile for dependency management and common tasks

.PHONY: help install update-deps compile-deps test lint format clean

help:
	@echo "Available commands:"
	@echo "  make install        - Install all dependencies"
	@echo "  make update-deps    - Update and compile dependencies from .in files"
	@echo "  make compile-deps   - Compile requirements.txt from requirements.in"
	@echo "  make test          - Run test suite"
	@echo "  make lint          - Run linting checks"
	@echo "  make format        - Format code with black"
	@echo "  make clean         - Clean cache and temporary files"

# Install dependencies
install:
	pip install --upgrade pip
	pip install pip-tools
	pip install -r requirements.txt
	pip install -r requirements-test.txt

# Update and compile dependencies
update-deps:
	pip install --upgrade pip-tools
	pip-compile --upgrade --resolver=backtracking requirements.in -o requirements.txt
	@echo "Dependencies updated. Please review changes before committing."

# Compile dependencies without updating
compile-deps:
	pip-compile --resolver=backtracking requirements.in -o requirements.txt

# Run tests
test:
	python -m pytest tests/ -v

# Run linting
lint:
	ruff check .
	black --check .

# Format code
format:
	black .
	ruff check --fix .

# Clean cache and temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/