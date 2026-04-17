import uuid
from datetime import timedelta, datetime

from fastapi import HTTPException
from sqlalchemy import Column, String, Integer, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.database import SessionLocal

metadata = Base.metadata


class User(Base):
    __tablename__ = "users"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"User: {self.email}"


class EmailVerificationOTP(Base):
    __tablename__ = "email_verification_otp"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    email = Column(String, nullable=False)
    otp = Column(String, unique=True, index=True, nullable=False)
    attempts = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"Email verification otp: {self.otp}"

    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP code."""
        import secrets
        import string
        return ''.join(secrets.choice(string.digits) for _ in range(6))

    def is_otp_expired(self) -> bool:
        """Check if OTP is expired (3 minutes)."""
        expiry_time = self.created_at + timedelta(minutes=3)
        return datetime.now() > expiry_time

    def increment_attempts(self):
        self.attempts += 1
        self.save_to_db()

    def mark_otp_expired(self):
        self.is_expired = True
        self.save_to_db()

    def verify(self):
        if self.is_expired or self.is_verified:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        self.is_verified = True
        self.verified_at = func.now()
        self.save_to_db()

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()

    def delete_from_db(self):
        db = SessionLocal()
        try:
            db.delete(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    token = Column(String, primary_key=True, index=True)
    blacklisted_on = Column(DateTime, server_default=func.now())
