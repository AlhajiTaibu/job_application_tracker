from fastapi import HTTPException
from pydantic import validate_email
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.core.security import _make_hash
from app.models.user import User, BlacklistedToken
from app.schemas.user import UserCreate, ResetPassword, RefreshToken


def get_user_by_email(db: Session, email: str):
    try:
        return db.query(User).filter(User.email == email).first()
    except NoResultFound as error:
        raise HTTPException(status_code=404, detail=f"{str(error).split(':')[-1]}")


def create_user(db: Session, user: UserCreate):
    try:
        email_info, email = validate_email(user.email)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Invalid email: {error}")
    try:
        hashed_password = _make_hash(user.password)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Invalid password: {error}")
    db_user = db.query(User).filter_by(email=email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(email=email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def reset_password(db: Session, request_data: ResetPassword, email: str):
    try:
        password = request_data.password
        db_user = db.query(User).filter_by(email=email).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="Error")
        hashed_password = _make_hash(password)
        db_user.hashed_password = hashed_password
        db.commit()
        db.refresh(db_user)
        return {"success": True, "message": "Password reset successful"}
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail="Error")


def confirm_email(db: Session, email: str):
    db_user = db.query(User).filter_by(email=email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.is_verified = True
    db.commit()
    db.refresh(db_user)
    return db_user


def check_blacklisted_token(db: Session, token: RefreshToken):
    try:
        refresh_token = token.refresh_token
        is_blacklisted = db.query(BlacklistedToken).filter(
            BlacklistedToken.token == refresh_token
        ).first()

        if is_blacklisted:
            raise HTTPException(status_code=401, detail="Token has been revoked")
    except Exception as error:
        logger.error(error)


def create_blacklisted_token(db: Session, token: RefreshToken):
    refresh_token = token.refresh_token
    blacklisted_token = BlacklistedToken(refresh_token)
    db.add(blacklisted_token)
    db.commit()
    db.refresh(blacklisted_token)
    return {"success": True, "message": "Logout successful"}
