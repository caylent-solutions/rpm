SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

.PHONY: help install install-dev lint lint-check format format-check test test-unit test-functional test-cov clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies (editable + ruff + pytest)
	pip install -r requirements-dev.txt

lint: lint-check format-check ## Run all lint checks (ruff check + ruff format --check)

lint-check: ## Lint Python files (ruff check)
	ruff check .

format: ## Auto-format Python files (ruff format)
	ruff format .

format-check: ## Verify formatting without modifying files (ruff format --check)
	ruff format --check .

test: ## Run full test suite
	python -m pytest

test-unit: ## Run unit tests only
	python -m pytest -m unit

test-functional: ## Run functional tests only
	python -m pytest -m functional

test-cov: ## Run tests with coverage report
	python -m pytest --cov=rpm_cli --cov-report=term-missing

clean: ## Remove build artifacts and caches
	find . -depth -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache htmlcov dist build *.egg-info src/*.egg-info
	rm -f .coverage
	find . -depth -type f -name '*.pyc' -delete
