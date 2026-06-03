from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy import or_, and_, desc, select, asc
from sqlalchemy.testing import db

from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.job_application import JobTask, TaskType, TaskCreator, TaskStatus, JobApplication, SnoozeJobTask
from app.schemas.job_task import JobTaskUpdate, JobTaskFilterParams
from dateutil import parser


class TaskService:
    def __init__(self):
        try:
            self.db = SessionLocal()
        finally:
            self.db.close()

    def create_task(self, name: str, description: str, task_type: TaskType, created_by: TaskCreator,
                    due_date: datetime = None, meta_data: Dict[str, Any] = None):
        try:
            task = JobTask(
                name=name,
                description=description,
                task_type=task_type,
                created_by=created_by
            )
            if due_date:
                task.due_date = parser.parse(due_date) if isinstance(due_date, str) else task.due_date
            if meta_data:
                if "user_id" in meta_data:
                    task.user_id = meta_data["user_id"]
                if "job_application_id" in meta_data and meta_data["job_application_id"]:
                    job = self.db.query(JobApplication).where(
                        JobApplication.id == meta_data["job_application_id"]).first()
                    if not job:
                        raise Exception("Job Application not found")
                    task.job_application_id = meta_data["job_application_id"]
                    task.user_id = job.user_id
            self.db.close()
            task.save_to_db()
            return {
                "success": True,
                "id": task.id,
                "message": "Task created successfully"
            }
        except Exception as error:
            logger.error(error)
            raise Exception("Error creating task")

    def update_task(self, task_id: str, data: JobTaskUpdate):
        try:
            task = self.db.query(JobTask).filter(JobTask.id == task_id).first()
            self.db.close()
            if not task:
                raise Exception("Task not found")
            task.name = data.name if data.name else task.name
            task.due_date = parser.parse(data.due_date) if data.due_date else task.due_date
            task.task_type = data.task_type if data.task_type else task.task_type
            task.status = data.status if data.status else task.status
            task.updated_at = datetime.now()
            task.save_to_db()
            return {
                "success": True,
                "message": "Task updated successfully",
                "data": {
                    "id": task.id,
                    "name": task.name
                }
            }

        except Exception as error:
            logger.error(error)
            raise Exception("Error updating task")

    def get_task(self, task_id: str):
        try:
            db_task = self.db.query(JobTask).filter(JobTask.id == task_id).first()
            if not db_task:
                raise Exception("Task not found")
            return db_task
        except Exception as error:
            logger.error(error)
            raise Exception("Error retrieving task")

    def get_tasks(self, job_id: str, limit: int):
        try:
            db_task = self.db.query(JobTask).filter(JobTask.job_application_id == job_id).order_by(desc(JobTask.created_at)).limit(limit).all()
            results = db_task if db_task else []
            return results
        except Exception as error:
            logger.error(error)
            raise Exception("Error retrieving tasks")

    def get_daily_tasks(self, user_id: str, filters: JobTaskFilterParams):
        try:
            today = datetime.now().date()
            stmt = select(JobTask).filter(
                JobTask.user_id == user_id,
                JobTask.is_overdue == False,
                JobTask.due_date == today,
                or_(JobTask.status == TaskStatus.PENDING,JobTask.status == TaskStatus.SNOOZED)
            )
            if filters.status:
                stmt = stmt.where(JobTask.status == filters.status)
            if filters.task_type:
                stmt = stmt.where(JobTask.task_type == filters.task_type)

            if filters.order == "desc":
                stmt = stmt.order_by(desc(JobTask.created_at))
            else:
                stmt = stmt.order_by(asc(JobTask.created_at))

            db_tasks = self.db.execute(stmt).scalars().all()
            return db_tasks
        except Exception as error:
            logger.error(error)
            raise Exception("Error retrieving daily tasks")

    def get_upcoming_tasks(self, user_id: str, days: int, filters: JobTaskFilterParams):
        try:
            if days <= 0:
                raise Exception("Days must be greater than 0")
            today = datetime.now().date()
            future_date = today + timedelta(days=days)
            stmt = select(JobTask).filter(
                JobTask.user_id == user_id,
                JobTask.is_overdue == False,
                JobTask.due_date >= today,
                JobTask.due_date <= future_date,
                or_(JobTask.status == TaskStatus.PENDING, JobTask.status == TaskStatus.SNOOZED)
            )

            if filters.status:
                stmt = stmt.where(JobTask.status == filters.status)
            if filters.task_type:
                stmt = stmt.where(JobTask.task_type == filters.task_type)

            if filters.order == "desc":
                stmt = stmt.order_by( desc(JobTask.created_at))
            else:
                stmt = stmt.order_by(asc(JobTask.created_at))

            db_tasks = self.db.execute(stmt).scalars().all()
            return db_tasks
        except Exception as error:
            logger.error(error)
            raise Exception("Error retrieving upcoming tasks")

    def get_overdue_tasks(self, user_id: str, filters: JobTaskFilterParams):
        try:
            today = datetime.now().date()
            stmt = select(JobTask).filter(
                or_(and_(JobTask.is_overdue == True,
                         JobTask.user_id == user_id,
                         JobTask.status != TaskStatus.COMPLETED),
                    and_(JobTask.due_date < today,
                         JobTask.user_id == user_id,
                         JobTask.status != TaskStatus.COMPLETED))
            )

            if filters.status:
                stmt = stmt.where(JobTask.status == filters.status)
            if filters.task_type:
                stmt = stmt.where(JobTask.task_type == filters.task_type)

            if filters.order == "desc":
                stmt = stmt.order_by(desc(JobTask.created_at))
            else:
                stmt = stmt.order_by(asc(JobTask.created_at))

            db_tasks = self.db.execute(stmt).scalars().all()
            return db_tasks
        except Exception as error:
            logger.error(error)
            raise Exception("Error retrieving overdue tasks")

    def snooze_task(self, task_id: str, period: int, snoozed_by: TaskCreator):
        try:
            task = self.db.query(JobTask).filter(JobTask.id == task_id).first()
            self.db.close()
            if not task:
                raise Exception("Task not found")
            task.status = TaskStatus.SNOOZED
            task.due_date = task.due_date + timedelta(days=period)
            task.updated_at = datetime.now()
            task.save_to_db()
            snooze_job_task = self.db.query(SnoozeJobTask).filter(SnoozeJobTask.task_id == task_id).first()
            self.db.close()
            if not snooze_job_task:
                new_snooze_job_task = SnoozeJobTask(task_id=task_id, next_due_date=task.due_date)
                new_snooze_job_task.save_to_db()
            else:
                snooze_job_task.snoozed_count += 1
                snooze_job_task.next_due_date = task.due_date
                snooze_job_task.save_to_db()
            return {
                "success": True,
                "message": f"Task snoozed for {period} days"
            }
        except Exception as error:
            logger.error(error)
            raise Exception("Error snoozing task")

    def complete_task(self, task_id):
        try:
            task = self.db.query(JobTask).filter(JobTask.id == task_id).first()
            self.db.close()
            if not task:
                raise Exception("Task not found")
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.now()
            task.save_to_db()
            return {
                "success": True,
                "message": "Task completed successfully"
            }
        except Exception as error:
            logger.error(error)
            raise Exception("Error completing task")

    def cancel_task(self, task_id):
        try:
            task = self.db.query(JobTask).filter(JobTask.id == task_id).first()
            self.db.close()
            if not task:
                raise Exception("Task not found")
            task.status = TaskStatus.CANCELLED
            task.updated_at = datetime.now()
            task.save_to_db()
            return {
                "success": True,
                "message": "Task cancelled successfully"
            }
        except Exception as error:
            logger.error(error)
            raise Exception("Error cancelling task")


task_service = TaskService()
