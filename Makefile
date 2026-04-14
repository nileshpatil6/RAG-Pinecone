.PHONY: help install dev test lint format run docker-build docker-run docker-down docker-logs db-init check setup clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup        - Full first-time setup (venv + install + .env)"
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Run development server with auto-reload"
	@echo "  make test         - Run tests with coverage"
	@echo "  make lint         - Run ruff lint + mypy"
	@echo "  make format       - Auto-format with ruff"
	@echo "  make check        - lint + test (CI equivalent)"
	@echo "  make run          - Run production server"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Start services via docker-compose"
	@echo "  make docker-down  - Stop docker-compose services"
	@echo "  make docker-logs  - Tail app container logs"
	@echo "  make db-init      - Initialize the database"
	@echo "  make clean        - Remove build artifacts and caches"

# First-time project setup
setup:
	@[ -f .env ] || cp .env.example .env && echo "Created .env — add your API keys"
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
	.venv/bin/pre-commit install
	@echo "Setup complete. Activate with: source .venv/bin/activate"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Development server with auto-reload
dev:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Linting
lint:
	python -m ruff check .
	python -m mypy app/

# Format code
format:
	python -m ruff format .
	python -m ruff check . --fix

# Run lint + tests (mirrors CI)
check: lint test

# Production server
run:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Docker operations
docker-build:
	docker build -t student-notes-rag:latest .

docker-run:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

# Database operations
db-init:
	python scripts/init_db.py

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.db" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/