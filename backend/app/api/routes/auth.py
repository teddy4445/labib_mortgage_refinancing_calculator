from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from backend.app import models
from backend.app.api.response_utils import build_response_meta
from backend.app.core.config import get_settings
from backend.app.dependencies import (
    get_analytics_manager,
    get_captcha_manager,
    get_db_manager,
    get_email_manager,
    get_rate_limit_manager,
    get_validation_manager,
)
from backend.app.managers.analytics_manager import AnalyticsManager
from backend.app.managers.database_manager import DataBaseManager
from backend.app.managers.email_manager import EmailManager
from backend.app.managers.security_manager import CaptchaManager, RateLimitManager, ValidationManager
from backend.app.schemas import (
    EmailAvailabilityResponse,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterResponse,
    ResetPasswordResponse,
    UserCreate,
)


router = APIRouter()


class RegisterRequest(UserCreate):
    captcha_token: str | None = None


class ForgotPasswordRequest(PasswordResetRequest):
    captcha_token: str | None = None


def _hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def _build_rate_key(request: Request, rate_limit_manager: RateLimitManager, label: str) -> str:
    return rate_limit_manager.build_key([label, request.client.host if request.client else "unknown"])


@router.post("/register", response_model=RegisterResponse)
async def register(
    payload: RegisterRequest,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    validation_manager: Annotated[ValidationManager, Depends(get_validation_manager)],
    captcha_manager: Annotated[CaptchaManager, Depends(get_captcha_manager)],
    email_manager: Annotated[EmailManager, Depends(get_email_manager)],
    analytics_manager: Annotated[AnalyticsManager, Depends(get_analytics_manager)],
    rate_limit_manager: Annotated[RateLimitManager, Depends(get_rate_limit_manager)],
) -> RegisterResponse:
    rate_limit_manager.check(key=_build_rate_key(request, rate_limit_manager, "register"))
    validation_manager.validate_registration(payload)
    if not await captcha_manager.verify(payload.captcha_token, request.client.host if request.client else None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captcha verification failed.")
    if await db_manager.find_user_by_email(str(payload.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
    if await db_manager.find_user_by_username(payload.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered.")

    user = await db_manager.create_user(payload, password_hash=_hash_password(payload.password))
    verification_token = hashlib.sha256(f"{user.email}:{datetime.utcnow().isoformat()}".encode("utf-8")).hexdigest()
    await db_manager.add(
        models.EmailVerificationToken(
            user_id=user.id,
            token=verification_token,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
    )

    settings = get_settings()
    verification_link = f"{settings.frontend_url}/pages/status/email-verification.html?token={verification_token}"
    try:
        email_manager.send_auth_email(to_email=user.email, verification_link=verification_link, user_name=user.username)
    except Exception as exc:
        await analytics_manager.track_email_failure(template_name="auth_code.html", error=str(exc))

    await analytics_manager.track_conversion(page="register", session_id=None, source="backend_api")
    return RegisterResponse(
        status="pending_verification",
        user_id=user.id,
        meta=build_response_meta(request),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    rate_limit_manager: Annotated[RateLimitManager, Depends(get_rate_limit_manager)],
) -> LoginResponse:
    rate_limit_manager.check(key=_build_rate_key(request, rate_limit_manager, "login"))
    user = await db_manager.find_user_by_email(str(payload.email))
    if user is None or user.password_hash != _hash_password(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    if user.status == models.UserStatus.LOCKED:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="User account is locked.")
    return LoginResponse(
        status="ok",
        role=user.role.value,
        user_id=user.id,
        username=user.username,
        email=user.email,
        account_status=user.status.value,
        email_verified=user.email_verified,
        meta=build_response_meta(request),
    )


@router.get("/email-available", response_model=EmailAvailabilityResponse)
async def email_available(
    email: str,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
) -> EmailAvailabilityResponse:
    existing = await db_manager.find_user_by_email(email)
    available = existing is None
    return EmailAvailabilityResponse(
        available=available,
        code="EMAIL_AVAILABLE" if available else "EMAIL_TAKEN",
        meta=build_response_meta(request),
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
    captcha_manager: Annotated[CaptchaManager, Depends(get_captcha_manager)],
    email_manager: Annotated[EmailManager, Depends(get_email_manager)],
    analytics_manager: Annotated[AnalyticsManager, Depends(get_analytics_manager)],
    rate_limit_manager: Annotated[RateLimitManager, Depends(get_rate_limit_manager)],
) -> ForgotPasswordResponse:
    rate_limit_manager.check(key=_build_rate_key(request, rate_limit_manager, "forgot-password"))
    if not await captcha_manager.verify(payload.captcha_token, request.client.host if request.client else None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captcha verification failed.")
    user = await db_manager.find_user_by_email(str(payload.email))
    if user is None:
        return ForgotPasswordResponse(status="ignored", email=payload.email, meta=build_response_meta(request))

    token = hashlib.sha256(f"reset:{user.email}:{datetime.utcnow().isoformat()}".encode("utf-8")).hexdigest()
    await db_manager.add(
        models.PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
    )
    reset_link = f"{get_settings().frontend_url}/pages/reset-password.html?token={token}"
    try:
        email_manager.send_password_reset(to_email=user.email, reset_link=reset_link, user_name=user.username)
    except Exception as exc:
        await analytics_manager.track_email_failure(template_name="password_reset.html", error=str(exc))
    return ForgotPasswordResponse(status="sent", email=payload.email, meta=build_response_meta(request))


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    payload: PasswordResetConfirm,
    request: Request,
    db_manager: Annotated[DataBaseManager, Depends(get_db_manager)],
) -> ResetPasswordResponse:
    token = await db_manager.find_password_reset_token(payload.token)
    if token is None or token.consumed_at is not None or token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token expired.")

    user = await db_manager.get_by_id(models.User, token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    await db_manager.update_user_password(user.id, _hash_password(payload.password))
    await db_manager.consume_password_reset_token(token)
    return ResetPasswordResponse(status="ok", meta=build_response_meta(request))
