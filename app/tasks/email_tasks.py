from app.core.celery import celery_app
from app.core.logging_config import logger
from app.services.otp_service import OTPService


@celery_app.task(name="send_otp")
def send_verification_email(email: str):
        otp_service = OTPService()
        response = otp_service.send_otp(email)
        logger.info(f"response: {response}")
        return response

@celery_app.task(name="forgot_password")
def send_forgot_password_email(email: str, template:str, subject: str):
        otp_service = OTPService()
        response = otp_service.send_otp(email, template, subject)
        logger.info(f"response: {response}")
        return response