import logging

from fastapi import HTTPException
from sqlalchemy import select
from app.database import SessionLocal

from app.models.user import User, EmailVerificationOTP
from app.services.email_service.email_service import send_email

logger = logging.getLogger(__name__)


class OTPService:
    def __init__(self):
        self.expiry = '3'
        try:
            self.db = SessionLocal()
        finally:
            self.db.close()

    def send_otp(self, email: str, template: str = "auth/verification_email.html", subject: str = "OTP Verification"):
        otp = EmailVerificationOTP.generate_otp()
        data = EmailVerificationOTP(email=email, otp=otp)
        data.save_to_db()
        email_sent = send_email(template, email, subject, {'otp': otp, 'email': email, 'expiry': self.expiry })
        if email_sent:
            return {
                'success': True,
                'message': 'OTP sent to email',
                'expires_in': '3 minutes',
            }
        else:
            return {}

    def verify_otp(self, email: str, token: str):
        try:
            result = self.db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=400, detail="Invalid OTP")
            res = self.db.execute(select(EmailVerificationOTP)
                                  .filter(EmailVerificationOTP.email == email,
                                          EmailVerificationOTP.is_verified == False,
                                          EmailVerificationOTP.is_expired == False
                                          )
                                  .order_by(EmailVerificationOTP.created_at))
            email_verification_otp = res.scalar()
            if not email_verification_otp:
                raise HTTPException(status_code=400, detail="Invalid OTP")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

        try:
            if email_verification_otp.is_otp_expired():
                email_verification_otp.mark_otp_expired()
                raise HTTPException(status_code=400, detail="OTP Expired")

            if email_verification_otp.attempts > 3:
                email_verification_otp.mark_otp_expired()
                raise HTTPException(status_code=400, detail="Too many attempts")

            if email_verification_otp.otp == token:
                email_verification_otp.verify()
                return True
            else:
                email_verification_otp.increment_attempts()
                remaining_attempts = 3 - email_verification_otp.attempts
                raise HTTPException(status_code=400,
                                    detail=f"Invalid OTP, you have {remaining_attempts} more attempts remaining")
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{e}")
