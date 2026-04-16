import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import _make_access_token, _verify_password, _make_refresh_token, \
    _verify_token
from app.crud import crud_user
from app.schemas.user import UserCreate, ConfirmEmail, ResendOTP, RefreshToken, ResetPassword
from app.services.otp_service import OTPService
from app.tasks.email_tasks import send_verification_email, send_forgot_password_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    user = crud_user.create_user(db, user)
    try:
        task = send_verification_email.delay(user.email)
        logger.info(f"Task {task.id}, email: {user.email}, email verification sent")
        return {
            'success': True,
            'message': 'OTP sent to email',
            'expires_in': "3 minutes",
        }
    except Exception as error:
        logger.error(f"error: {error}")
        raise HTTPException(status_code=400, detail="Error sending OTP email")


@router.post("/login")
async def login(data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, data.username)
    if not user or not _verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="User's email is not verified")
    return {"access_token": _make_access_token(user.email), "token_type": "bearer",
            "refresh_token": _make_refresh_token(user.email)}


@router.post("/confirm-email")
async def confirm_email(token_data: ConfirmEmail, db: Session = Depends(get_db)):
    try:
        email, token = token_data.email, token_data.token
        otp_service = OTPService()
        is_otp_verified = otp_service.verify_otp(email, token)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=f"{str(error).split(':')[-1]}")
    if not is_otp_verified:
        raise HTTPException(status_code=400, detail="Invalid token")
    return crud_user.confirm_email(db, email)


@router.post("/resend-otp")
async def resend_otp(data: ResendOTP, db: Session = Depends(get_db)):
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
async def refresh_access_token(token: RefreshToken, db: Session = Depends(get_db)):
    crud_user.check_blacklisted_token(db, token)
    try:
        email = _verify_token(token.refresh_token)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=f"{str(e)}")
    db_user = crud_user.get_user_by_email(db, email)
    return {"access_token": _make_access_token(db_user.email), "token_type": "bearer",
            "message": "Token refreshed successfully"}


@router.post("/logout")
async def logout(token: RefreshToken, db: Session = Depends(get_db)):
    return crud_user.create_blacklisted_token(db, token)


@router.post("/forgot-password")
async def forgot_password(data: ResendOTP, db: Session = Depends(get_db)):
    try:
        db_user = crud_user.get_user_by_email(db, data.email)
        task = send_forgot_password_email.delay(db_user.email, template="auth/forgot_password.html",
                                                subject="Forgotten password")
        logger.info(f"Task {task.id}, email: {db_user.email}, forgot password sent")
        return {"success": True, "message": "Forgot password OTP sent to email"}
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=f"{error}")


@router.post("/reset-password")
async def reset_password(request_data: ResetPassword, db: Session = Depends(get_db)):
    return crud_user.reset_password(db, request_data)
