"""Pytest fixtures and configuration."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.database import DatabasePool
from app.email.providers import MockProvider
from app.email.service import EmailService, set_email_service
from app.main import create_app
from app.users.security import hash_password


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        app_env="test",
        app_debug=True,
        database_url="postgresql://postgres:postgres@localhost:5432/user_registration_test",
        activation_code_expiry_seconds=60,
    )


@pytest.fixture
def mock_email_provider() -> MockProvider:
    return MockProvider()


@pytest.fixture
def mock_email_service(mock_email_provider: MockProvider) -> EmailService:
    service = EmailService(mock_email_provider)
    set_email_service(service)
    return service


@pytest.fixture
def mock_db_pool() -> MagicMock:
    pool = MagicMock(spec=DatabasePool)
    pool.acquire = MagicMock()
    pool.transaction = MagicMock()
    return pool


@pytest.fixture
def sample_user_data() -> dict:
    return {
        "id": uuid4(),
        "email": "test@example.com",
        "password_hash": hash_password("TestPassword123"),
        "is_active": False,
        "activation_code": "1234",
        "activation_code_expires_at": datetime.now(UTC) + timedelta(minutes=1),
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


@pytest.fixture
def active_user_data(sample_user_data: dict) -> dict:
    return {
        **sample_user_data,
        "is_active": True,
        "activation_code": None,
        "activation_code_expires_at": None,
    }


@pytest.fixture
def expired_code_user_data(sample_user_data: dict) -> dict:
    return {
        **sample_user_data,
        "activation_code_expires_at": datetime.now(UTC) - timedelta(minutes=5),
    }


@pytest.fixture
def app(mock_email_service: EmailService):
    return create_app()


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client(app) -> Generator[TestClient]:
    with TestClient(app) as client:
        yield client
