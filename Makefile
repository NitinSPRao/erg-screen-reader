.PHONY: help install dev web clean test lint format check

help: ## Show this help message
	@echo "🚣 Erg Screen Reader - Available Commands"
	@echo "========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with uv
	uv pip install -e .

dev: ## Install development dependencies
	uv pip install -e '.[dev]'

web: ## Start the web server
	uv run erg-web

cli: ## Show CLI help
	uv run erg-reader --help

clean: ## Clean up generated files
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

test: ## Run tests
	uv run pytest

lint: ## Run linting
	uv run ruff check .

format: ## Format code
	uv run black .
	uv run ruff check --fix .

check: ## Run all checks (lint + format + test)
	make lint
	make format
	make test

setup: ## Set up development environment
	python scripts/setup.py