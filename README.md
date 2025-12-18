# User Registration API

Production-ready FastAPI application for user registration with email verification using Resend.
Project is available online: https://bee-fastapi-development.up.railway.app/ 

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
- Resend API key (get one at https://resend.com)

## Local Development

### 1. Setup environment

```bash
cp .env.example .env
# Edit .env and add your RESEND_API_KEY
```

### 2. Start services

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

## Production (Railway)

### 1. Create Railway project

```bash
railway login
railway init
```

### 2. Add PostgreSQL

```bash
railway add --plugin postgresql
```

### 3. Set environment variables

```bash
railway variables set APP_ENV=production
railway variables set RESEND_API_KEY=re_your_key
railway variables set RESEND_FROM_EMAIL=noreply@yourdomain.com
```

### 4. Deploy

```bash
railway up
```

Railway will:
- Build the Docker image
- Run migrations automatically (via start command)
- Start the API

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
just migrate         # Run migrations
just migration NAME  # Create new migration
just migrate-down    # Rollback one migration
just shell           # Open shell in API container
```
# bee-fastapi
