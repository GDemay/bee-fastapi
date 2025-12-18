# User Registration API

Production-ready FastAPI application for user registration with email verification using Resend.

Project is available online: [https://bee-fastapi-development.up.railway.app/](https://bee-fastapi-development.up.railway.app/).
This service sends you an email (likely to your spam folder) via Resend.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Server                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Routes    │→ │   Service   │→ │    Repository       │  │
│  │  (HTTP)     │  │  (Business) │  │    (Raw SQL)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                │                    │              │
│         ▼                ▼                    ▼              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Pydantic   │  │   Email     │  │      asyncpg        │  │
│  │  Schemas    │  │   Service   │  │   (PostgreSQL)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│       PostgreSQL        │     │         Resend          │
│       (Database)        │     │      (Email API)        │
└─────────────────────────┘     └─────────────────────────┘
```

## Requirements

- Docker & Docker Compose
- [just](https://github.com/casey/just) (task runner)

## Local Development

### 1. Setup environment

```bash
cp .env.example .env
# Edit `.env` and add your `RESEND_API_KEY` if you want to send emails. IF NOT, it will log them to the console. This parameter is optional
```

### 2. Start services

```bash
docker compose up -d
```
or
```bash
just up
```

This will:
- Start PostgreSQL
- Run Alembic migrations
- Start the API on http://localhost:8000

### 3. View API docs

Open http://localhost:8000/docs

### 4. Run tests

```bash
just test
```

### 5. Stop services

```bash
just down
```
or

```bash
docker compose down
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/register` | Register new user |
| POST | `/users/activate` | Activate account with code |
| POST | `/users/resend-code` | Resend activation code |
| GET | `/health` | Health check |

### Register User

```bash
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123"}'
```

### Activate Account

```bash
curl -X POST http://localhost:8000/users/activate \
  -u "user@example.com:SecurePass123" \
  -H "Content-Type: application/json" \
  -d '{"code": "1234"}'
```

### Resend Code

```bash
curl -X POST http://localhost:8000/users/resend-code \
  -u "user@example.com:SecurePass123"
```

## Migration System

Uses Alembic for database migrations.

```bash
# Run migrations
just migrate

# Create new migration
just migration "add_new_column"

# Rollback one migration
just migrate-down
```

## Available Commands

```bash
just up              # Start all services
just down            # Stop all services
just test            # Run tests
just lint            # Check code style
just lint-fix        # Fix code style
just format          # Format code
```


# bee-fastapi
