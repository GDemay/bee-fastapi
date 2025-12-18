"""Application exceptions."""

from typing import Any


class AppException(Exception):
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class UserAlreadyExistsError(AppException):
    def __init__(self, email: str) -> None:
        super().__init__(
            message=f"User with email '{email}' already exists",
            error_code="EMAIL_ALREADY_EXISTS",
            status_code=409,
            details={"email": email},
        )


class UserNotFoundError(AppException):
    def __init__(self, identifier: str) -> None:
        super().__init__(
            message=f"User not found: {identifier}",
            error_code="USER_NOT_FOUND",
            status_code=404,
            details={"identifier": identifier},
        )


class InvalidCredentialsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Invalid email or password",
            error_code="INVALID_CREDENTIALS",
            status_code=401,
        )


class InvalidActivationCodeError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Invalid activation code",
            error_code="INVALID_CODE",
            status_code=400,
        )


class ActivationCodeExpiredError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Activation code has expired. Please request a new one.",
            error_code="CODE_EXPIRED",
            status_code=400,
        )


class UserAlreadyActiveError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="User account is already active",
            error_code="USER_ALREADY_ACTIVE",
            status_code=400,
        )


class EmailServiceError(AppException):
    def __init__(self, message: str = "Failed to send email") -> None:
        super().__init__(
            message=message,
            error_code="EMAIL_SERVICE_ERROR",
            status_code=503,
        )
