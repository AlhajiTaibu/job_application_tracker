from datetime import datetime, timedelta

from app.core.celery import celery_app
from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.job_application import JobApplication
from app.models.user import User
from app.services.state_machine import job_application_state_machine
from app.services.email_service.email_service import send_email


@celery_app.task()
def mark_job_application_stale():
    """
    Mark job applications that have not been updated in the last 30 days as stale
    and send notifications to the user.
    :return:
    """
    db = SessionLocal()
    try:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        job_apps = (db.query(JobApplication).
                    filter(JobApplication.updated_at < thirty_days_ago,
                           JobApplication.status.contains("applied", "interviewing", "assessment", "screening"))
                    .all())
        for job_app in job_apps:
            job_application_state_machine.transition_state(job_app, "stale", {"reason": "No activity in the last 30 days"})
            user_id = job_app.user_id
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                send_email(
                    recipient=user.email,
                    subject="Job Application Stale Notification",
                    html="notification/application_stale.html",
                    context = {
                        "email": user.email,
                        "company": job_app.company_name,
                        "title": job_app.job_title
                    }
                )
    except Exception as error:
        logger.error(error)
    finally:
        db.close()