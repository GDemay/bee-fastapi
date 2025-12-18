"""Database connection management using asyncpg."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Connection, Pool

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class DatabasePool:
    def __init__(self) -> None:
        self._pool: Pool | None = None

    async def connect(self, settings: Settings | None = None) -> None:
        if self._pool is not None:
            return

        settings = settings or get_settings()
        database_url = settings.raw_asyncpg_url

        logger.info("Connecting to database...")
        self._pool = await asyncpg.create_pool(
            dsn=database_url,
            min_size=settings.database_pool_min_size,
            max_size=settings.database_pool_max_size,
        )
        logger.info("Database connection pool established")

    async def disconnect(self) -> None:
        if self._pool is None:
            return

        logger.info("Closing database connection pool...")
        await self._pool.close()
        self._pool = None
        logger.info("Database connection pool closed")

    @property
    def pool(self) -> Pool:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        return self._pool

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Connection]:
        async with self.pool.acquire() as connection:
            yield connection

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Connection]:
        async with self.pool.acquire() as connection, connection.transaction():
            yield connection


_db_pool = DatabasePool()


def get_db_pool() -> DatabasePool:
    return _db_pool
