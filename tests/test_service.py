"""Tests for user service business logic."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.email.providers import MockProvider
from app.email.service import EmailService
from app.exceptions import (
    ActivationCodeExpiredError,
    InvalidActivationCodeError,
    UserAlreadyActiveError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.users import service


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_register_user_success(self):
        mock_db = MagicMock()
        mock_provider = MockProvider()
        email_service = EmailService(mock_provider)

        user_id = uuid4()
        now = datetime.now(UTC)

        with patch("app.users.service.repository") as mock_repo:
            mock_repo.email_exists = AsyncMock(return_value=False)
            mock_repo.create_user = AsyncMock(
                return_value={
                    "id": user_id,
                    "email": "test@example.com",
                    "is_active": False,
                    "activation_code": "1234",
                    "activation_code_expires_at": now + timedelta(minutes=1),
                    "created_at": now,
                    "updated_at": now,
                }
            )

            result = await service.register_user(
                db=mock_db,
                email_service=email_service,
                email="test@example.com",
                password="TestPassword123",
            )

            assert result["email"] == "test@example.com"
            assert result["is_active"] is False
            mock_repo.email_exists.assert_called_once()
            mock_repo.create_user.assert_called_once()

            assert len(mock_provider.sent_emails) == 1
            assert mock_provider.sent_emails[0]["to"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self):
        mock_db = MagicMock()
        mock_provider = MockProvider()
        email_service = EmailService(mock_provider)

        with patch("app.users.service.repository") as mock_repo:
            mock_repo.email_exists = AsyncMock(return_value=True)

            with pytest.raises(UserAlreadyExistsError) as exc_info:
                await service.register_user(
                    db=mock_db,
                    email_service=email_service,
                    email="existing@example.com",
                    password="TestPassword123",
                )

            assert "existing@example.com" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_register_user_normalizes_email(self):
        mock_db = MagicMock()
        mock_provider = MockProvider()
        email_service = EmailService(mock_provider)

        user_id = uuid4()
        now = datetime.now(UTC)

        with patch("app.users.service.repository") as mock_repo:
            mock_repo.email_exists = AsyncMock(return_value=False)
            mock_repo.create_user = AsyncMock(
                return_value={
                    "id": user_id,
                    "email": "test@example.com",
                    "is_active": False,
                    "activation_code": "1234",
                    "activation_code_expires_at": now + timedelta(minutes=1),
                    "created_at": now,
                    "updated_at": now,
                }
            )

            await service.register_user(
                db=mock_db,
                email_service=email_service,
                email="TEST@EXAMPLE.COM",
                password="TestPassword123",
            )

            call_args = mock_repo.create_user.call_args
            assert call_args.kwargs["email"] == "TEST@EXAMPLE.COM"


class TestActivateUser:
    @pytest.mark.asyncio
    async def test_activate_user_success(self):
        mock_db = MagicMock()
        user_id = uuid4()
        now = datetime.now(UTC)

        user = {
            "id": user_id,
            "email": "test@example.com",
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": now + timedelta(minutes=1),
        }

        with patch("app.users.service.repository") as mock_repo:
            mock_repo.activate_user = AsyncMock(
                return_value={
                    "id": user_id,
                    "email": "test@example.com",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
            )

            result = await service.activate_user(
                db=mock_db,
                user=user,
                code="1234",
            )

            assert result["is_active"] is True
            mock_repo.activate_user.assert_called_once_with(mock_db, user_id)

    @pytest.mark.asyncio
    async def test_activate_user_already_active(self):
        mock_db = MagicMock()
        user = {
            "id": uuid4(),
            "email": "test@example.com",
            "is_active": True,
            "activation_code": None,
            "activation_code_expires_at": None,
        }

        with pytest.raises(UserAlreadyActiveError):
            await service.activate_user(
                db=mock_db,
                user=user,
                code="1234",
            )

    @pytest.mark.asyncio
    async def test_activate_user_invalid_code(self):
        mock_db = MagicMock()
        user = {
            "id": uuid4(),
            "email": "test@example.com",
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": datetime.now(UTC) + timedelta(minutes=1),
        }

        with pytest.raises(InvalidActivationCodeError):
            await service.activate_user(
                db=mock_db,
                user=user,
                code="9999",
            )

    @pytest.mark.asyncio
    async def test_activate_user_expired_code(self):
        mock_db = MagicMock()
        user = {
            "id": uuid4(),
            "email": "test@example.com",
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": datetime.now(UTC) - timedelta(minutes=5),
        }

        with pytest.raises(ActivationCodeExpiredError):
            await service.activate_user(
                db=mock_db,
                user=user,
                code="1234",
            )

    @pytest.mark.asyncio
    async def test_activate_user_no_code_stored(self):
        mock_db = MagicMock()
        user = {
            "id": uuid4(),
            "email": "test@example.com",
            "is_active": False,
            "activation_code": None,
            "activation_code_expires_at": None,
        }

        with pytest.raises(InvalidActivationCodeError):
            await service.activate_user(
                db=mock_db,
                user=user,
                code="1234",
            )

    @pytest.mark.asyncio
    async def test_activate_user_no_expiry_stored(self):
        mock_db = MagicMock()
        user = {
            "id": uuid4(),
            "email": "test@example.com",
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": None,
        }

        with pytest.raises(InvalidActivationCodeError):
            await service.activate_user(
                db=mock_db,
                user=user,
                code="1234",
            )

    @pytest.mark.asyncio
    async def test_activate_user_naive_datetime_handling(self):
        mock_db = MagicMock()
        user_id = uuid4()
        naive_time = datetime.now() + timedelta(minutes=1)

        user = {
            "id": user_id,
            "email": "test@example.com",
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": naive_time,
        }

        with patch("app.users.service.repository") as mock_repo:
            mock_repo.activate_user = AsyncMock(
                return_value={
                    "id": user_id,
                    "email": "test@example.com",
                    "is_active": True,
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )

            result = await service.activate_user(
                db=mock_db,
                user=user,
                code="1234",
            )

            assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_activate_user_not_found_after_activation(self):
        mock_db = MagicMock()
        user = {
            "id": uuid4(),
            "email": "test@example.com",
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": datetime.now(UTC) + timedelta(minutes=1),
        }

        with patch("app.users.service.repository") as mock_repo:
            mock_repo.activate_user = AsyncMock(return_value=None)

            with pytest.raises(UserNotFoundError):
                await service.activate_user(
                    db=mock_db,
                    user=user,
                    code="1234",
                )


class TestResendActivationCode:
    @pytest.mark.asyncio
    async def test_resend_code_success(self):
        mock_db = MagicMock()
        mock_provider = MockProvider()
        email_service = EmailService(mock_provider)
        user_id = uuid4()
        now = datetime.now(UTC)

        user = {
            "id": user_id,
            "email": "test@example.com",
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": now - timedelta(minutes=5),
        }

        with patch("app.users.service.repository") as mock_repo:
            mock_repo.update_activation_code = AsyncMock(
                return_value={
                    "id": user_id,
                    "email": "test@example.com",
                    "is_active": False,
                    "activation_code": "5678",
                    "activation_code_expires_at": now + timedelta(minutes=1),
                    "created_at": now,
                    "updated_at": now,
                }
            )

            result = await service.resend_activation_code(
                db=mock_db,
                email_service=email_service,
                user=user,
            )

            assert result["activation_code"] == "5678"
            mock_repo.update_activation_code.assert_called_once()

            assert len(mock_provider.sent_emails) == 1

    @pytest.mark.asyncio
    async def test_resend_code_already_active(self):
        mock_db = MagicMock()
        mock_provider = MockProvider()
        email_service = EmailService(mock_provider)

        user = {
            "id": uuid4(),
            "email": "test@example.com",
            "is_active": True,
            "activation_code": None,
            "activation_code_expires_at": None,
        }

        with pytest.raises(UserAlreadyActiveError):
            await service.resend_activation_code(
                db=mock_db,
                email_service=email_service,
                user=user,
            )

    @pytest.mark.asyncio
    async def test_resend_code_user_not_found(self):
        mock_db = MagicMock()
        mock_provider = MockProvider()
        email_service = EmailService(mock_provider)

        user = {
            "id": uuid4(),
            "email": "test@example.com",
            "is_active": False,
            "activation_code": "1234",
            "activation_code_expires_at": datetime.now(UTC) - timedelta(minutes=5),
        }

        with patch("app.users.service.repository") as mock_repo:
            mock_repo.update_activation_code = AsyncMock(return_value=None)

            with pytest.raises(UserNotFoundError):
                await service.resend_activation_code(
                    db=mock_db,
                    email_service=email_service,
                    user=user,
                )
