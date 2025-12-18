"""Tests for email service and providers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.email.providers import MockProvider, ResendProvider
from app.email.service import EmailService, create_email_service
from app.exceptions import EmailServiceError


class TestMockProvider:
    @pytest.mark.asyncio
    async def test_send_email_stores_in_memory(self):
        provider = MockProvider()

        result = await provider.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        assert result is True
        assert len(provider.sent_emails) == 1
        assert provider.sent_emails[0]["to"] == "test@example.com"
        assert provider.sent_emails[0]["subject"] == "Test Subject"
        assert provider.sent_emails[0]["body"] == "Test Body"

    @pytest.mark.asyncio
    async def test_send_multiple_emails(self):
        provider = MockProvider()

        await provider.send_email("first@example.com", "First", "Body 1")
        await provider.send_email("second@example.com", "Second", "Body 2")
        await provider.send_email("third@example.com", "Third", "Body 3")

        assert len(provider.sent_emails) == 3

    @pytest.mark.asyncio
    async def test_get_last_email(self):
        provider = MockProvider()

        await provider.send_email("first@example.com", "First", "Body 1")
        await provider.send_email("second@example.com", "Second", "Body 2")

        last = provider.get_last_email()
        assert last is not None
        assert last["to"] == "second@example.com"

    @pytest.mark.asyncio
    async def test_get_last_email_empty(self):
        provider = MockProvider()

        assert provider.get_last_email() is None

    def test_clear_emails(self):
        provider = MockProvider()
        provider.sent_emails.append({"to": "test@example.com"})

        provider.clear()

        assert len(provider.sent_emails) == 0

    @pytest.mark.asyncio
    async def test_close_is_noop(self):
        provider = MockProvider()
        await provider.close()


class TestEmailService:
    @pytest.mark.asyncio
    async def test_send_activation_code(self):
        mock_provider = MockProvider()
        svc = EmailService(mock_provider)

        result = await svc.send_activation_code("test@example.com", "1234")

        assert result is True
        assert len(mock_provider.sent_emails) == 1

        email = mock_provider.sent_emails[0]
        assert email["to"] == "test@example.com"
        assert "1234" in email["body"]
        assert "activation" in email["subject"].lower()

    @pytest.mark.asyncio
    async def test_send_activation_code_includes_expiry_info(self):
        mock_provider = MockProvider()
        svc = EmailService(mock_provider)

        await svc.send_activation_code("test@example.com", "5678")

        email = mock_provider.sent_emails[0]
        assert "1 minute" in email["body"]

    @pytest.mark.asyncio
    async def test_provider_property(self):
        mock_provider = MockProvider()
        svc = EmailService(mock_provider)

        assert svc.provider is mock_provider


class TestResendProvider:
    @pytest.mark.asyncio
    async def test_send_email_no_api_key(self):
        provider = ResendProvider(
            api_key="",
            from_email="noreply@example.com",
        )

        with pytest.raises(EmailServiceError) as exc_info:
            await provider.send_email(
                to="test@example.com",
                subject="Test",
                body="Test body",
            )

        assert "not configured" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        provider = ResendProvider(
            api_key="re_valid_api_key",
            from_email="noreply@example.com",
        )

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "email_123"}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await provider.send_email(
                to="test@example.com",
                subject="Test",
                body="Test body",
            )

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_api_error(self):
        provider = ResendProvider(
            api_key="re_valid_api_key",
            from_email="noreply@example.com",
        )

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.content = b'{"message": "Invalid email"}'
            mock_response.json.return_value = {"message": "Invalid email"}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(EmailServiceError) as exc_info:
                await provider.send_email(
                    to="invalid",
                    subject="Test",
                    body="Test body",
                )

            assert "Invalid email" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_close_client(self):
        provider = ResendProvider(api_key="key", from_email="test@example.com")
        provider._client = AsyncMock()

        await provider.close()

        assert provider._client is None


class TestCreateEmailService:
    def test_create_mock_provider_for_test_env(self):
        settings = Settings(
            app_env="test",
            database_url="postgresql://localhost/test",
        )

        svc = create_email_service(settings)

        assert isinstance(svc.provider, MockProvider)

    def test_create_mock_provider_for_local_env(self):
        settings = Settings(
            app_env="local",
            resend_api_key="re_test_key",
            resend_from_email="noreply@example.com",
            database_url="postgresql://localhost/test",
        )

        svc = create_email_service(settings)

        assert isinstance(svc.provider, MockProvider)

    def test_create_resend_provider_for_production_env(self):
        settings = Settings(
            app_env="production",
            resend_api_key="re_test_key",
            resend_from_email="noreply@example.com",
            database_url="postgresql://localhost/test",
        )

        svc = create_email_service(settings)

        assert isinstance(svc.provider, ResendProvider)
