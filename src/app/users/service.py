"""User service containing business logic."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from app.config import Settings, get_settings
from app.database import DatabasePool
from app.email import EmailService
from app.exceptions import (
    ActivationCodeExpiredError,
    InvalidActivationCodeError,
    UserAlreadyActiveError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.users import repository
from app.users.security import generate_activation_code, hash_password

logger = logging.getLogger(__name__)


async def register_user(
    db: DatabasePool,
    email_service: EmailService,
    email: str,
    password: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()

    if await repository.email_exists(db, email):
        raise UserAlreadyExistsError(email)

    activation_code = generate_activation_code()
    expiry_seconds = settings.activation_code_expiry_seconds
    activation_expires_at = datetime.now(UTC) + timedelta(seconds=expiry_seconds)

    password_hash = hash_password(password)

    user = await repository.create_user(
        db=db,
        email=email,
        password_hash=password_hash,
        activation_code=activation_code,
        activation_code_expires_at=activation_expires_at,
    )

    logger.info("User created: %s (%s)", user["id"], email)

    await email_service.send_activation_code(email, activation_code)

    return user


async def activate_user(
    db: DatabasePool,
    user: dict[str, Any],
    code: str,
) -> dict[str, Any]:
    if user["is_active"]:
        raise UserAlreadyActiveError()

    stored_code = user.get("activation_code")
    if stored_code is None or stored_code != code:
        raise InvalidActivationCodeError()

    expires_at = user.get("activation_code_expires_at")
    if expires_at is None:
        raise InvalidActivationCodeError()

    now = datetime.now(UTC)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if now > expires_at:
        raise ActivationCodeExpiredError()

    activated_user = await repository.activate_user(db, user["id"])

    if activated_user is None:
        raise UserNotFoundError(str(user["id"]))

    logger.info("User activated: %s (%s)", user["id"], user["email"])

    return activated_user


async def resend_activation_code(
    db: DatabasePool,
    email_service: EmailService,
    user: dict[str, Any],
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()

    if user["is_active"]:
        raise UserAlreadyActiveError()

    activation_code = generate_activation_code()
    expiry_seconds = settings.activation_code_expiry_seconds
    activation_expires_at = datetime.now(UTC) + timedelta(seconds=expiry_seconds)

    updated_user = await repository.update_activation_code(
        db=db,
        user_id=user["id"],
        activation_code=activation_code,
        activation_code_expires_at=activation_expires_at,
    )

    if updated_user is None:
        raise UserNotFoundError(str(user["id"]))

    logger.info("Activation code resent for user: %s (%s)", user["id"], user["email"])

    await email_service.send_activation_code(user["email"], activation_code)

    return updated_user
