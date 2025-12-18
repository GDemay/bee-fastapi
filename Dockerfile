# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

FROM base AS development

COPY pyproject.toml README.md alembic.ini ./
COPY alembic/ ./alembic/

RUN uv sync --all-extras --no-install-project

COPY src/ ./src/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production

COPY pyproject.toml README.md alembic.ini ./
COPY alembic/ ./alembic/

RUN uv sync --no-dev --no-install-project

COPY src/ ./src/
COPY start.sh ./

RUN chmod +x start.sh && \
    adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["sh", "start.sh"]

FROM base AS test

COPY pyproject.toml README.md alembic.ini ./
COPY alembic/ ./alembic/

RUN uv sync --all-extras --no-install-project

COPY src/ ./src/
COPY tests/ ./tests/

CMD ["uv", "run", "pytest", "-v", "--cov=app", "--cov-report=term-missing"]
