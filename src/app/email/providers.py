"""Email provider implementations."""

import logging
from abc import ABC, abstractmethod

import httpx

from app.exceptions import EmailServiceError

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


class ResendProvider(EmailProvider):
    API_URL = "https://api.resend.com/emails"

    def __init__(self, api_key: str, from_email: str) -> None:
        self.api_key = api_key
        self.from_email = from_email
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        if not self.api_key:
            raise EmailServiceError("Resend API key is not configured")

        try:
            client = await self._get_client()

            payload = {
                "from": self.from_email,
                "to": [to],
                "subject": subject,
                "text": body,
            }

            response = await client.post(self.API_URL, json=payload)

            if response.status_code == 200:
                data = response.json()
                logger.info("Email sent via Resend. ID: %s", data.get("id"))
                return True

            error_data = response.json() if response.content else {}
            error_message = error_data.get("message", f"HTTP {response.status_code}")
            logger.error("Resend API error: %s", error_message)
            raise EmailServiceError(f"Failed to send email: {error_message}")

        except httpx.RequestError as e:
            logger.error("Resend connection error: %s", e)
            raise EmailServiceError(f"Email service connection error: {e!s}") from e

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


class MockProvider(EmailProvider):
    """Mock provider for testing only."""

    def __init__(self) -> None:
        self.sent_emails: list[dict] = []

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        email_data = {"to": to, "subject": subject, "body": body}
        self.sent_emails.append(email_data)
        logger.info("[MOCK] Email stored: %s", email_data)
        return True

    def clear(self) -> None:
        self.sent_emails.clear()

    def get_last_email(self) -> dict | None:
        return self.sent_emails[-1] if self.sent_emails else None

    async def close(self) -> None:
        pass
