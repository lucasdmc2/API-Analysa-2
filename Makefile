.PHONY: setup run test lint type sec clean docker-build docker-up docker-down migrate seed

# Development setup
setup:
	@echo "Setting up development environment..."
	python -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r requirements.txt
	cp .env.example .env
	@echo "Setup complete! Edit .env file with your configuration."

# Run application locally
run:
	@echo "Starting API server..."
	. .venv/bin/activate && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	@echo "Running tests..."
	. .venv/bin/activate && pytest --maxfail=1 --disable-warnings -q --cov=src --cov-report=xml:reports/coverage.xml

# Run linters
lint:
	@echo "Running linters..."
	. .venv/bin/activate && ruff check src tests
	. .venv/bin/activate && ruff format --check src tests

# Fix linting issues
lint-fix:
	@echo "Fixing linting issues..."
	. .venv/bin/activate && ruff check --fix src tests
	. .venv/bin/activate && ruff format src tests

# Run type checks
type:
	@echo "Running type checks..."
	. .venv/bin/activate && mypy src

# Run security checks
sec:
	@echo "Running security checks..."
	. .venv/bin/activate && bandit -r src
	. .venv/bin/activate && pip-audit

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf reports/coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "Viewing Docker logs..."
	docker-compose logs -f api

# Database commands
migrate:
	@echo "Running database migrations..."
	docker-compose exec postgres psql -U clinical_user -d clinical_db -f /docker-entrypoint-initdb.d/001_init_core_tables.sql
	docker-compose exec postgres psql -U clinical_user -d clinical_db -f /docker-entrypoint-initdb.d/002_rls_policies.sql

seed:
	@echo "Seeding database with reference data..."
	docker-compose exec postgres psql -U clinical_user -d clinical_db -f /docker-entrypoint-initdb.d/../seed/001_basic_data.sql

# Full local setup
dev-setup: setup docker-up migrate seed
	@echo "Development environment ready!"
	@echo "API available at: http://localhost:8000"
	@echo "API docs at: http://localhost:8000/docs"
	@echo "MinIO console at: http://localhost:9001 (admin/minioadmin123)"

# Health check
health:
	@echo "Checking service health..."
	curl -f http://localhost:8000/health || echo "API not healthy"

# Quick development workflow
dev: lint-fix type test
	@echo "Development checks passed!"
