from sqlalchemy import update, or_, select

from app.core.celery import celery_app
from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.job_application import JobTask, TaskStatus, TaskType, TaskCreator, JobApplication
from datetime import datetime

from app.models.user import User, Profile, NotificationType
from app.services.email_service.email_service import send_email
from app.services.firebase_service import push_notification_service
from app.services.task_service import task_service


@celery_app.task()
def flag_overdue_tasks():
    db = SessionLocal()
    try:
        now = datetime.now()
        with db.begin():
            stmt = (
                update(JobTask)
                .where(JobTask.due_date < now)
                .where(or_(JobTask.status != TaskStatus.COMPLETED, JobTask.status != TaskStatus.CANCELLED))
                .values(is_overdue=True)
            )
            result = db.execute(stmt)
            db.commit()
            logger.info(f"Updated {result.rowcount} rows")
    except Exception as error:
        logger.error(error)
    finally:
        db.close()


@celery_app.task()
def send_task_reminders():
    db = SessionLocal()
    try:
        today = datetime.now().date()
        overdue_tasks = db.query(JobTask).filter(
            JobTask.due_date == today,
            or_(JobTask.status != TaskStatus.CANCELLED, JobTask.status != TaskStatus.COMPLETED)
        ).all()

        for task in overdue_tasks:
            user_id = task.user_id
            stmt = select(User.id, User.email, Profile.notification_type).join(Profile, User.id == Profile.user_id).where(User.id==user_id)
            user = db.execute(stmt).first()
            message = resolve_notification_message(task.task_type)
            subject = "Job Application Notification"
            task_type = str(task.task_type).capitalize()
            if user.notification_type == NotificationType.EMAIL:
                send_email(
                    recipient=user.email,
                    subject=subject,
                    html="notification/general_notification.html",
                    context={
                        "email": user.email,
                        "task_type": task_type,
                        "message": message
                    }
                )
            if user.notification_type == NotificationType.PUSH:
                push_notification_service.send_push_notification(user_id, title=subject, body=f"URGENT:{task_type} - {message}")
            logger.info(f"Sending reminder for task: {task.name}")
    except Exception as error:
        logger.error(error)
    finally:
        db.close()


def resolve_notification_message(task_type: TaskType):
    if task_type == TaskType.FOLLOW_UP:
        message = "Follow up with recruiter if no response"
    elif task_type == TaskType.CONFIRM:
        message = "Confirm your attendance for the interview"
    elif task_type == TaskType.THANK_YOU:
        message = "Send a thank you message"
    elif task_type == TaskType.REMINDER:
        message = "You have a reminder task due today"
    elif task_type == TaskType.REVIEW:
        message = "You have a review task due today"
    else:
        message = "You have a task due today"
    return message



@celery_app.task()
def snooze_tasks():
    """
    Snooze active follow-up tasks for the next 7 days
    :return:
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        follow_up_tasks = db.query(JobTask).filter(
            JobTask.due_date < now,
            JobTask.task_type == TaskType.FOLLOW_UP,
            JobTask.status == TaskStatus.PENDING
        ).all()

        for task in follow_up_tasks:
            task_service.snooze_task(task.id, 7, TaskCreator.SYSTEM)
    except Exception as error:
        logger.error(error)
    finally:
        db.close()
