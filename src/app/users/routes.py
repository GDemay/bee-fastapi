"""API routes for user registration and activation."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.database import DatabasePool, get_db_pool
from app.email import EmailService, get_email_service
from app.users import service
from app.users.schemas import (
    ResendCodeResponse,
    UserActivatedResponse,
    UserActivateRequest,
    UserCreatedResponse,
    UserRegisterRequest,
)
from app.users.security import authenticate_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post(
    "/register",
    response_model=UserCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. An activation code will be sent to the provided email.",
)
async def register(
    request: UserRegisterRequest,
    db: Annotated[DatabasePool, Depends(get_db_pool)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> UserCreatedResponse:
    user = await service.register_user(
        db=db,
        email_service=email_service,
        email=request.email,
        password=request.password,
    )

    return UserCreatedResponse(
        id=user["id"],
        email=user["email"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


@router.post(
    "/activate",
    response_model=UserActivatedResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate user account",
    description="Activate a user account using the 4-digit code sent via email. Requires Basic Auth.",
)
async def activate(
    request: UserActivateRequest,
    user: Annotated[dict, Depends(authenticate_user)],
    db: Annotated[DatabasePool, Depends(get_db_pool)],
) -> UserActivatedResponse:
    activated_user = await service.activate_user(
        db=db,
        user=user,
        code=request.code,
    )

    return UserActivatedResponse(
        id=activated_user["id"],
        email=activated_user["email"],
        is_active=activated_user["is_active"],
    )


@router.post(
    "/resend-code",
    response_model=ResendCodeResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend activation code",
    description="Request a new activation code. Requires Basic Auth.",
)
async def resend_code(
    user: Annotated[dict, Depends(authenticate_user)],
    db: Annotated[DatabasePool, Depends(get_db_pool)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> ResendCodeResponse:
    await service.resend_activation_code(
        db=db,
        email_service=email_service,
        user=user,
    )

    return ResendCodeResponse()
