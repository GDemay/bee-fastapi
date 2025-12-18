"""Integration tests for API endpoints."""

import base64
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database import get_db_pool
from app.email import get_email_service
from app.email.providers import MockProvider
from app.email.service import EmailService
from app.main import create_app
from app.users.security import hash_password


def get_basic_auth_header(email: str, password: str) -> dict:
    credentials = base64.b64encode(f"{email}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}


@pytest.fixture
def mock_db():
    mock = MagicMock()
    mock.acquire = MagicMock()
    return mock


@pytest.fixture
def mock_email_provider():
    return MockProvider()


@pytest.fixture
def client(mock_db, mock_email_provider):
    app = create_app()

    app.dependency_overrides[get_db_pool] = lambda: mock_db

    email_service = EmailService(mock_email_provider)
    app.dependency_overrides[get_email_service] = lambda: email_service

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


class TestRegisterEndpoint:
    def test_register_success(self, client, mock_email_provider):
        user_id = uuid4()
        now = datetime.now(UTC)

        with patch("app.users.repository.email_exists", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = False

            with patch("app.users.repository.create_user", new_callable=AsyncMock) as mock_create:
                mock_create.return_value = {
                    "id": user_id,
                    "email": "test@example.com",
                    "is_active": False,
                    "activation_code": "1234",
                    "activation_code_expires_at": now + timedelta(minutes=1),
                    "created_at": now,
                    "updated_at": now,
                }

                response = client.post(
                    "/api/v1/users/register",
                    json={
                        "email": "test@example.com",
                        "password": "TestPassword123",
                    },
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["email"] == "test@example.com"
                assert data["is_active"] is False
                assert "message" in data
                assert str(user_id) == data["id"]

                assert len(mock_email_provider.sent_emails) == 1

    def test_register_email_exists(self, client):
        with patch("app.users.repository.email_exists", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = True

            response = client.post(
                "/api/v1/users/register",
                json={
                    "email": "existing@example.com",
                    "password": "TestPassword123",
                },
            )

            assert response.status_code == status.HTTP_409_CONFLICT
            data = response.json()
            assert data["error_code"] == "EMAIL_ALREADY_EXISTS"

    def test_register_invalid_email(self, client):
        response = client.post(
            "/api/v1/users/register",
            json={
                "email": "invalid-email",
                "password": "TestPassword123",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_weak_password_too_short(self, client):
        response = client.post(
            "/api/v1/users/register",
            json={
                "email": "test@example.com",
                "password": "weak",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_weak_password_no_uppercase(self, client):
        response = client.post(
            "/api/v1/users/register",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_weak_password_no_lowercase(self, client):
        response = client.post(
            "/api/v1/users/register",
            json={
                "email": "test@example.com",
                "password": "TESTPASSWORD123",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_weak_password_no_digit(self, client):
        response = client.post(
            "/api/v1/users/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_missing_email(self, client):
        response = client.post(
            "/api/v1/users/register",
            json={
                "password": "TestPassword123",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_missing_password(self, client):
        response = client.post(
            "/api/v1/users/register",
            json={
                "email": "test@example.com",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_empty_body(self, client):
        response = client.post(
            "/api/v1/users/register",
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestActivateEndpoint:
    def test_activate_success(self, client):
        user_id = uuid4()
        now = datetime.now(UTC)
        password = "TestPassword123"
        password_hash = hash_password(password)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": password_hash,
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": now + timedelta(minutes=1),
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = user_data

            with patch(
                "app.users.repository.activate_user", new_callable=AsyncMock
            ) as mock_activate:
                mock_activate.return_value = {
                    "id": user_id,
                    "email": "test@example.com",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }

                response = client.post(
                    "/api/v1/users/activate",
                    json={"code": "1234"},
                    headers=get_basic_auth_header("test@example.com", password),
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["is_active"] is True

    def test_activate_no_auth(self, client):
        response = client.post(
            "/api/v1/users/activate",
            json={"code": "1234"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_activate_invalid_credentials_wrong_email(self, client):
        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None

            response = client.post(
                "/api/v1/users/activate",
                json={"code": "1234"},
                headers=get_basic_auth_header("wrong@example.com", "WrongPassword123"),
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_activate_invalid_credentials_wrong_password(self, client):
        user_id = uuid4()
        now = datetime.now(UTC)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": hash_password("CorrectPassword123"),
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": now + timedelta(minutes=1),
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = user_data

            response = client.post(
                "/api/v1/users/activate",
                json={"code": "1234"},
                headers=get_basic_auth_header("test@example.com", "WrongPassword123"),
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_activate_expired_code(self, client):
        user_id = uuid4()
        now = datetime.now(UTC)
        password = "TestPassword123"
        password_hash = hash_password(password)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": password_hash,
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": now - timedelta(minutes=5),
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = user_data

            response = client.post(
                "/api/v1/users/activate",
                json={"code": "1234"},
                headers=get_basic_auth_header("test@example.com", password),
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["error_code"] == "CODE_EXPIRED"

    def test_activate_invalid_code(self, client):
        user_id = uuid4()
        now = datetime.now(UTC)
        password = "TestPassword123"
        password_hash = hash_password(password)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": password_hash,
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": now + timedelta(minutes=1),
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = user_data

            response = client.post(
                "/api/v1/users/activate",
                json={"code": "9999"},
                headers=get_basic_auth_header("test@example.com", password),
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["error_code"] == "INVALID_CODE"

    def test_activate_already_active(self, client):
        user_id = uuid4()
        now = datetime.now(UTC)
        password = "TestPassword123"
        password_hash = hash_password(password)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": password_hash,
            "is_active": True,
            "activation_code": None,
            "activation_code_expires_at": None,
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = user_data

            response = client.post(
                "/api/v1/users/activate",
                json={"code": "1234"},
                headers=get_basic_auth_header("test@example.com", password),
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["error_code"] == "USER_ALREADY_ACTIVE"

    def test_activate_invalid_code_format_too_short(self, client):
        user_id = uuid4()
        now = datetime.now(UTC)
        password = "TestPassword123"
        password_hash = hash_password(password)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": password_hash,
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": now + timedelta(minutes=1),
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = user_data

            response = client.post(
                "/api/v1/users/activate",
                json={"code": "123"},
                headers=get_basic_auth_header("test@example.com", password),
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_activate_invalid_code_format_non_numeric(self, client):
        user_id = uuid4()
        now = datetime.now(UTC)
        password = "TestPassword123"
        password_hash = hash_password(password)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": password_hash,
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": now + timedelta(minutes=1),
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = user_data

            response = client.post(
                "/api/v1/users/activate",
                json={"code": "abcd"},
                headers=get_basic_auth_header("test@example.com", password),
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestResendCodeEndpoint:
    def test_resend_code_success(self, client, mock_email_provider):
        user_id = uuid4()
        now = datetime.now(UTC)
        password = "TestPassword123"
        password_hash = hash_password(password)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": password_hash,
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": now - timedelta(minutes=5),
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = user_data

            with patch(
                "app.users.repository.update_activation_code", new_callable=AsyncMock
            ) as mock_update:
                mock_update.return_value = {
                    **user_data,
                    "activation_code": "5678",
                    "activation_code_expires_at": now + timedelta(minutes=1),
                }

                response = client.post(
                    "/api/v1/users/resend-code",
                    headers=get_basic_auth_header("test@example.com", password),
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "message" in data

                assert len(mock_email_provider.sent_emails) == 1

    def test_resend_code_already_active(self, client):
        user_id = uuid4()
        now = datetime.now(UTC)
        password = "TestPassword123"
        password_hash = hash_password(password)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": password_hash,
            "is_active": True,
            "activation_code": None,
            "activation_code_expires_at": None,
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = user_data

            response = client.post(
                "/api/v1/users/resend-code",
                headers=get_basic_auth_header("test@example.com", password),
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["error_code"] == "USER_ALREADY_ACTIVE"

    def test_resend_code_no_auth(self, client):
        response = client.post("/api/v1/users/resend-code")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_resend_code_invalid_credentials(self, client):
        with patch("app.users.repository.find_user_by_email", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None

            response = client.post(
                "/api/v1/users/resend-code",
                headers=get_basic_auth_header("wrong@example.com", "WrongPassword123"),
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
