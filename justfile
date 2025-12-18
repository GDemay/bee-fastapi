# User Registration API - Task Runner
# Install just: https://github.com/casey/just

set dotenv-load := true

default:
    @just --list

# Start all services in development mode
up:
    docker compose up -d
    @echo ""
    @echo "✅ Services started!"
    @echo ""
    @echo "📍 API:        http://localhost:${API_PORT:-8000}"
    @echo "📖 Swagger:    http://localhost:${API_PORT:-8000}/docs"
    @echo "📧 Mailhog:    http://localhost:8025"
    @echo ""

# Stop all services
down:
    docker compose down

# View logs from all services
logs:
    docker compose logs -f

# View logs from API service only
logs-api:
    docker compose logs -f api

# Build Docker images
build:
    docker compose build

# Run database migrations
migrate:
    docker compose exec api uv run alembic upgrade head

# Create a new migration
migration name:
    docker compose exec api uv run alembic revision --autogenerate -m "{{name}}"

# Rollback last migration
migrate-down:
    docker compose exec api uv run alembic downgrade -1

# Show migration history
migrate-history:
    docker compose exec api uv run alembic history

# Run tests in Docker
test:
    docker compose --profile test up --build --abort-on-container-exit test
    docker compose --profile test down

# Run tests with coverage report
test-cov:
    docker compose --profile test run --rm test uv run pytest -v --cov=app --cov-report=html --cov-report=term-missing
    docker compose --profile test down

# Run linter (check mode)
lint:
    docker compose exec api uv run ruff check src/ tests/
    docker compose exec api uv run ruff format --check src/ tests/

# Run linter and fix issues
lint-fix:
    docker compose exec api uv run ruff check --fix src/ tests/
    docker compose exec api uv run ruff format src/ tests/

# Format code
format:
    docker compose exec api uv run ruff format src/ tests/

# Clean up containers, volumes, and cache
clean:
    docker compose down -v --remove-orphans
    docker compose --profile test down -v --remove-orphans
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    @echo "✅ Cleaned up"

# Install development dependencies locally
install:
    uv sync --all-extras

# Run API locally (requires local postgres)
dev:
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Health check
health:
    curl -s http://localhost:${API_PORT:-8000}/health | python -m json.tool
