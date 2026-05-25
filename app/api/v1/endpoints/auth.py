import base64
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sso.sso.google import GoogleSSO
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_reset_password_token_user
from app.core.config import settings
from app.core.logging_config import logger
from app.core.security import _make_access_token, _verify_password, _make_refresh_token, \
    _verify_token, _make_reset_token
from app.crud import crud_user
from app.models.user import User
from app.schemas.user import UserCreate, ConfirmEmail, ResendOTP, RefreshToken, ResetPassword, ResetPasswordOTP
from app.services.otp_service import OTPService
from app.tasks.user_tasks import send_verification_email, send_forgot_password_email

google_sso = GoogleSSO(
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    redirect_uri=settings.oauth2_redirect_uri,
    allow_insecure_http=False if settings.is_prod else True
)

router = APIRouter()


@router.post("/register")
async def register(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        user = crud_user.create_user(db, user)
        task = send_verification_email.delay(user.email)
        logger.info(f"Task {task.id}, email: {user.email}, email verification sent")
        return {
            'success': True,
            'message': 'OTP sent to email',
            'expires_in': "3 minutes",
        }
    except Exception as error:
        logger.error(f"error: {error}")
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/login")
async def login(data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[Session, Depends(get_db)]):
    try:
        user = crud_user.get_user_by_email(db, data.username)
        if not user or not _verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        if not user.is_verified:
            raise HTTPException(status_code=400, detail="User's email is not verified")
        return {
            "access_token": _make_access_token(user.email),
            "token_type": "bearer",
            "refresh_token": _make_refresh_token(user.email),
            "user_id": user.id
        }
    except Exception as error:
        logger.error(f"error: {error}")
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/confirm-email")
async def confirm_email(token_data: ConfirmEmail, db: Annotated[Session, Depends(get_db)]):
    try:
        email, token = token_data.email, token_data.token
        otp_service = OTPService()
        is_otp_verified = otp_service.verify_otp(email, token)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=f"{str(error).split(':')[-1]}")
    if not is_otp_verified:
        raise HTTPException(status_code=400, detail="Invalid token")

    db_user = crud_user.confirm_email(db, email)
    return {
        "access_token": _make_access_token(db_user.email),
        "token_type": "bearer",
        "refresh_token": _make_refresh_token(db_user.email),
        "user_id": db_user.id
    }


@router.post("/resend-otp")
async def resend_otp(data: ResendOTP, db: Annotated[Session, Depends(get_db)]):
    try:
        db_user = crud_user.get_user_by_email(db, data.email)
        task = send_verification_email.delay(db_user.email)
        logger.info(f"Task {task.id}, email: {db_user.email} otp resend sent")
        return {
            'success': True,
            'message': 'OTP sent to email',
            'expires_in': "3 minutes",
        }
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=f"{error}")


@router.post("/refresh-token")
async def refresh_access_token(token: RefreshToken, db: Annotated[Session, Depends(get_db)]):
    try:
        crud_user.check_blacklisted_token(db, token)
        email = _verify_token(token.refresh_token)
        db_user = crud_user.get_user_by_email(db, email)
        return {
            "access_token": _make_access_token(db_user.email),
            "token_type": "bearer",
            "message": "Token refreshed successfully"
        }
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=f"{error}")


@router.post("/logout")
async def logout(token: RefreshToken, db: Annotated[Session, Depends(get_db)]):
    return crud_user.create_blacklisted_token(db, token)


@router.post("/forgot-password")
async def forgot_password(data: ResendOTP, db: Annotated[Session, Depends(get_db)]):
    try:
        db_user = crud_user.get_user_by_email(db, data.email)
        task = send_forgot_password_email.delay(db_user.email, template="auth/forgot_password.html",
                                                subject="Forgotten password")
        logger.info(f"Task {task.id}, email: {db_user.email}, forgot password sent")
        return {"success": True, "message": "Forgot password OTP sent to email"}
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=f"{error}")


@router.post("/verify-reset-password-token")
async def verify_reset_password_token(data: ResetPasswordOTP):
    try:
        otp_service = OTPService()
        otp_service.verify_otp(data.email, data.token)
        reset_token = _make_reset_token(data.email)
        return {"success": True, "reset_token": reset_token}
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=f"{str(error)}")


@router.post("/reset-password")
async def reset_password(request_data: ResetPassword, user: Annotated[User, Depends(get_reset_password_token_user)],
                         db: Annotated[Session, Depends(get_db)]):
    return crud_user.reset_password(db, request_data, user.email)


@router.get("/google/login")
async def google_login():
    """Redirects the user to the Google OAuth2 login page."""
    try:
        async with google_sso:
            return await google_sso.get_login_redirect(redirect_uri=settings.oauth2_redirect_uri)
    except Exception as error:
        logger.error(str(error))
        raise HTTPException(status_code=400, detail=f"An error occurred: {str(error)}")


@router.get("/google/callback/")
async def google_callback(request: Request):
    """Handles the callback from Google, processes the token, and returns user data."""
    try:
        async with google_sso:
            user = await google_sso.verify_and_process(request)

        if not user:
            raise HTTPException(status_code=400, detail="Authentication failed")
        if not user.email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        db_user = crud_user.create_user_or_login_via_google_sso(user=user)
        data = {
            "access_token": _make_access_token(db_user.email),
            "token_type": "bearer",
            "refresh_token": _make_refresh_token(db_user.email),
            "user_id": str(db_user.id)
        }
        if not settings.frontend_url:
            return data
        json_str = json.dumps(data)
        encoded = base64.b64encode(json_str.encode("utf-8")).decode()
        return RedirectResponse(url=f"{settings.frontend_url}?token={encoded}")
    except Exception as e:
        logger.error(str(e))
        if not settings.frontend_url:
            raise HTTPException(status_code=400, detail=f"An error occurred: {str(e)}")
        return RedirectResponse(url=f"{settings.frontend_url}/login?error={str(e)}")
