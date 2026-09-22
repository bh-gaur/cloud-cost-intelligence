.PHONY: help install dev test lint format migrate seed docker-up docker-down clean

PYTHON ?= python3
VENV ?= ../venv
PY_BIN ?= $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,$(PYTHON))
PIP_BIN ?= $(if $(wildcard $(VENV)/bin/pip),$(VENV)/bin/pip,pip3)

help:
	@echo "AWS Cost Intelligence - Developer CLI"
	@echo "======================================"
	@echo "make install      - Install backend and frontend dependencies"
	@echo "make dev          - Run backend and frontend concurrently"
	@echo "make test         - Run backend and frontend tests"
	@echo "make lint         - Run linters (Ruff/Flake8, ESLint)"
	@echo "make format       - Format code (Black/Ruff, Prettier)"
	@echo "make migrate      - Apply database schema migrations"
	@echo "make seed         - Seed demo FinOps cost and account data"
	@echo "make docker-up    - Start full stack in Docker Compose"
	@echo "make docker-down  - Stop Docker Compose services"
	@echo "make clean        - Remove temporary files, caches, and test artifacts"

install:
	@echo "Installing backend dependencies..."
	cd backend && $(PIP_BIN) install -e .
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev-backend:
	cd backend && $(PY_BIN) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting development services..."
	@echo "Run 'make dev-backend' in one shell and 'make dev-frontend' in another."

test-backend:
	cd backend && PYTHONPATH=. $(PY_BIN) -m pytest -v tests/

test-frontend:
	cd frontend && npm run test -- --run

test: test-backend test-frontend

lint-backend:
	cd backend && $(PY_BIN) -m ruff check app tests || true

lint-frontend:
	cd frontend && npm run lint || true

lint: lint-backend lint-frontend

format-backend:
	cd backend && $(PY_BIN) -m ruff format app tests || true

format-frontend:
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,css,json}" || true

format: format-backend format-frontend

migrate:
	cd backend && PYTHONPATH=. $(PY_BIN) -m alembic upgrade head

seed:
	cd backend && PYTHONPATH=. $(PY_BIN) scripts/seed_demo_data.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf backend/reports/csv/*.csv backend/reports/json/*.json backend/reports/html/*.html

