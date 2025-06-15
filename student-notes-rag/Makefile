.PHONY: help install dev test lint format run docker-build docker-run clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code"
	@echo "  make run          - Run production server"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make clean        - Clean up generated files"

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
	python -m black .
	python -m ruff check . --fix

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