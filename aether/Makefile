# Aether AI Companion Makefile

.PHONY: help install dev-install test lint format clean run docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code"
	@echo "  clean        - Clean up temporary files"
	@echo "  run          - Run the application"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"

# Installation
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/ -v --cov=aether --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

# Code quality
lint:
	flake8 aether/
	mypy aether/
	black --check aether/
	isort --check-only aether/

format:
	black aether/
	isort aether/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Development
run:
	python -m aether.main

run-dev:
	uvicorn aether.core.api.main:app --reload --host 0.0.0.0 --port 8000

# Database
db-init:
	alembic upgrade head

db-migrate:
	alembic revision --autogenerate -m "$(message)"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

# Docker
docker-build:
	docker build -t aether-ai-companion .

docker-run:
	docker run -p 8000:8000 -v $(PWD)/.env:/app/.env aether-ai-companion

# Development tools
setup-dev:
	python -m venv venv
	source venv/bin/activate && make dev-install
	cp .env.example .env
	@echo "Development environment set up!"
	@echo "Activate with: source venv/bin/activate"
	@echo "Configure .env file with your settings"