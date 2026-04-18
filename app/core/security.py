import logging
from datetime import datetime, timedelta

from fastapi import HTTPException
from hashward import CryptContext
from jose import jwt, JWTError
from starlette import status

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated=["pbkdf2_sha256"])


def _make_hash(password: str) -> str:
    return pwd_ctx.hash(password)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_ctx.verify(plain_password, hashed_password)


def _hash_otp(otp: str) -> str:
    return pwd_ctx.hash(otp)


def _verify_otp_hash(plain_otp: str, hashed_otp: str) -> bool:
    return pwd_ctx.verify(plain_otp, hashed_otp)


def _make_access_token(user_email: str) -> str:
    exp = datetime.now() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_email), "exp": exp}, settings.secret_key, algorithm=settings.algorithm)


def _make_reset_token(user_email: str) -> str:
    exp = datetime.now() + timedelta(minutes=settings.reset_password_token_expire_minutes)
    return jwt.encode({"sub": str(user_email), "exp": exp}, settings.secret_key, algorithm=settings.algorithm)


def _make_refresh_token(user_email: str) -> str:
    exp = datetime.now() + timedelta(minutes=settings.refresh_token_expire_minutes)
    return jwt.encode({"sub": str(user_email), "exp": exp}, settings.secret_key, algorithm=settings.algorithm)


def _verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_email = payload["sub"]
        expiry = datetime.fromtimestamp(payload["exp"])
    except (JWTError, KeyError, ValueError) as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if expiry < datetime.now():
        raise HTTPException(status_code=400, detail="Expired token")
    return user_email
