from sqlalchemy import update

from app.core.celery import celery_app
from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.job_application import JobTask
from datetime import datetime


@celery_app.task(name="flag_overdue_tasks")
def flag_overdue_tasks():
    db = SessionLocal()
    try:
        now = datetime.now()
        with db.begin():
            stmt = (
                update(JobTask)
                .where(JobTask.due_date < now)
                .values(is_overdue=True)
            )
            result = db.execute(stmt)
            db.commit()
            logger.info(f"Updated {result.rowcount} rows")
    except Exception as error:
        logger.error(error)
    finally:
        db.close()

