"""Email service for sending activation codes."""

import logging

from app.config import Settings, get_settings
from app.email.providers import EmailProvider, MockProvider, ResendProvider

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, provider: EmailProvider) -> None:
        self._provider = provider

    @property
    def provider(self) -> EmailProvider:
        return self._provider

    async def send_activation_code(self, email: str, code: str) -> bool:
        subject = "Your Account Activation Code"
        body = (
            f"Welcome to our service!\n\n"
            f"Your activation code is: {code}\n\n"
            f"This code will expire in 1 minute.\n\n"
            f"If you did not request this code, please ignore this email."
        )

        logger.info("Sending activation code to %s", email)
        return await self._provider.send_email(email, subject, body)

    async def close(self) -> None:
        await self._provider.close()


def create_email_service(settings: Settings | None = None) -> EmailService:
    settings = settings or get_settings()

    if settings.is_production:
        provider = ResendProvider(
            api_key=settings.resend_api_key,
            from_email=settings.resend_from_email,
        )
        logger.info("Using Resend email provider")
    else:
        provider = MockProvider()
        logger.info("Using Mock email provider (console output)")

    return EmailService(provider)


_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = create_email_service()
    return _email_service


def set_email_service(service: EmailService) -> None:
    global _email_service
    _email_service = service


async def close_email_service() -> None:
    global _email_service
    if _email_service is not None:
        await _email_service.close()
        _email_service = None
