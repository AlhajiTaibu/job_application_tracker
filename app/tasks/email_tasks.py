from app.core.celery import celery_app
from app.services.otp_service import OTPService


@celery_app.task(name="send_otp")
def send_verification_email(email: str):
        otp_service = OTPService()
        response = otp_service.send_otp(email)
        return response

@celery_app.task(name="forgot_password")
def send_forgot_password_email(email: str, template:str, subject: str):
        otp_service = OTPService()
        response = otp_service.send_otp(email, template, subject)
        return response