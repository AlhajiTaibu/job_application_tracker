from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.job_application import JobTask, TaskCreator
from app.schemas.job_application import ApiResponse
from app.schemas.job_task import JobTaskCreate, JobTaskUpdate, JobTaskSnooze

from app.services.task_service import task_service


def create_job_task(data: JobTaskCreate, user_id: str):
    try:
        return task_service.create_task(data.name, data.name, data.task_type, TaskCreator.MANUAL, data.due_date,
                                        {"job_application_id": data.job_application_id, "user_id": user_id})
    except Exception as e:
        logger.error(e)
        raise Exception("Error creating task")


def update_job_task(data: JobTaskUpdate, task_id: str):
    try:
        result = task_service.update_task(task_id, data)
        return result
    except Exception as e:
        logger.error(e)
        raise Exception("Error updating task")


def get_task_by_id(task_id: str):
    try:
        task = task_service.get_task(task_id)
        return ApiResponse(success=True, payload=task)
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting task")


def get_tasks(job_id: str, limit: int):
    try:
        results = task_service.get_tasks(job_id, limit)
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting tasks")


def get_daily_tasks(user_id: str):
    try:
        results = task_service.get_daily_tasks(user_id=user_id)
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting daily tasks")


def get_overdue_tasks(user_id: str):
    try:
        results = task_service.get_overdue_tasks(user_id=user_id)
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting overdue tasks")


def get_upcoming_tasks(user_id: str):
    try:
        results = task_service.get_upcoming_tasks(user_id=user_id, days=3)
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting upcoming tasks")


def delete_task(task_id: str, db: Session):
    try:
        db_task = db.query(JobTask).filter(JobTask.id == task_id).first()
        if db_task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        db.delete(db_task)
        db.commit()
        return {
            "success": True,
            "message": "Task deleted successfully"
        }
    except Exception as e:
        logger.error(e)
        raise Exception("Error deleting task")


def snooze_job_task(data: JobTaskSnooze, task_id: str):
    try:
        return task_service.snooze_task(task_id, data.period, TaskCreator.MANUAL)
    except Exception as e:
        logger.error(e)
        raise Exception("Error Snoozing task")


def complete_job_task(task_id: str):
    try:
        return task_service.complete_task(task_id)
    except Exception as e:
        logger.error(e)
        raise Exception("Error Completing task")


def cancel_job_task(task_id: str):
    try:
        return task_service.cancel_task(task_id)
    except Exception as e:
        logger.error(e)
        raise Exception("Error Cancelling task")
