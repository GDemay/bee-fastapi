"""User repository for database operations."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.database import DatabasePool


async def create_user(
    db: DatabasePool,
    email: str,
    password_hash: str,
    activation_code: str,
    activation_code_expires_at: datetime,
) -> dict[str, Any]:
    query = """
        INSERT INTO users (email, password_hash, activation_code, activation_code_expires_at)
        VALUES ($1, $2, $3, $4)
        RETURNING id, email, is_active, activation_code, activation_code_expires_at, created_at, updated_at
    """
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            query,
            email.lower(),
            password_hash,
            activation_code,
            activation_code_expires_at,
        )
        return dict(row) if row else {}


async def find_user_by_email(db: DatabasePool, email: str) -> dict[str, Any] | None:
    query = """
        SELECT id, email, password_hash, is_active, activation_code,
               activation_code_expires_at, created_at, updated_at
        FROM users
        WHERE LOWER(email) = LOWER($1)
    """
    async with db.acquire() as conn:
        row = await conn.fetchrow(query, email)
        return dict(row) if row else None


async def find_user_by_id(db: DatabasePool, user_id: UUID) -> dict[str, Any] | None:
    query = """
        SELECT id, email, password_hash, is_active, activation_code,
               activation_code_expires_at, created_at, updated_at
        FROM users
        WHERE id = $1
    """
    async with db.acquire() as conn:
        row = await conn.fetchrow(query, user_id)
        return dict(row) if row else None


async def activate_user(db: DatabasePool, user_id: UUID) -> dict[str, Any] | None:
    query = """
        UPDATE users
        SET is_active = TRUE, activation_code = NULL, activation_code_expires_at = NULL
        WHERE id = $1 AND is_active = FALSE
        RETURNING id, email, is_active, created_at, updated_at
    """
    async with db.acquire() as conn:
        row = await conn.fetchrow(query, user_id)
        return dict(row) if row else None


async def update_activation_code(
    db: DatabasePool,
    user_id: UUID,
    activation_code: str,
    activation_code_expires_at: datetime,
) -> dict[str, Any] | None:
    query = """
        UPDATE users
        SET activation_code = $2, activation_code_expires_at = $3
        WHERE id = $1 AND is_active = FALSE
        RETURNING id, email, is_active, activation_code, activation_code_expires_at, created_at, updated_at
    """
    async with db.acquire() as conn:
        row = await conn.fetchrow(query, user_id, activation_code, activation_code_expires_at)
        return dict(row) if row else None


async def email_exists(db: DatabasePool, email: str) -> bool:
    query = "SELECT EXISTS(SELECT 1 FROM users WHERE LOWER(email) = LOWER($1))"
    async with db.acquire() as conn:
        result = await conn.fetchval(query, email)
        return bool(result)


async def delete_user(db: DatabasePool, user_id: UUID) -> bool:
    query = "DELETE FROM users WHERE id = $1 RETURNING id"
    async with db.acquire() as conn:
        result = await conn.fetchval(query, user_id)
        return result is not None
