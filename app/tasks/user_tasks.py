from app.core.celery import celery_app
from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.user import EmailVerificationOTP
from app.services.otp_service import OTPService


@celery_app.task(bind=True,  max_retries=3)
def send_verification_email(self, email: str):
    try:
        otp_service = OTPService()
        response = otp_service.send_otp(email)
        logger.info(f"response: {response}")
        return response
    except Exception as error:
        logger.error(error)
        raise self.retry(exc=error, countdown=2 ** self.request.retries)


@celery_app.task(bind=True,  max_retries=3, name="forgot_password")
def send_forgot_password_email(self, email: str, template: str, subject: str):
    try:
        otp_service = OTPService()
        response = otp_service.send_otp(email, template, subject)
        logger.info(f"response: {response}")
        return response
    except Exception as error:
        logger.error(error)
        raise self.retry(exc=error, countdown=2 ** self.request.retries)


@celery_app.task()
def delete_expired_otp():
    db = SessionLocal()
    try:
        otps = db.query(EmailVerificationOTP).where(EmailVerificationOTP.is_verified == False).all()
        db.close()
        for otp in otps:
            if otp.is_otp_expired():
                result = db.delete(otp)
                affected_rows = result.rowcount
                if affected_rows == 0:
                    logger.warning(f"No rows were deleted for OTP ID: {otp.id}")
                else:
                    logger.info(f"Deleted {affected_rows} row(s) for OTP ID: {otp.id}")
                db.commit()
    except Exception as error:
        logger.error(error)
    finally:
        db.close()