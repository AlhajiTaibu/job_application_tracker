from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.job_application import JobTask, TaskCreator
from app.schemas.job_application import ApiResponse
from app.schemas.job_task import JobTaskCreate, JobTaskUpdate, JobTaskSnooze, JobTaskFilterParams
from app.core.redis import redis_manager

from app.services.task_service import task_service


def create_job_task(data: JobTaskCreate, user_id: str):
    try:
        return task_service.create_task(data.name, data.name, data.task_type, TaskCreator.MANUAL, data.due_date,
                                        {"job_application_id": data.job_application_id, "user_id": user_id})
    except Exception as e:
        logger.error(e)
        raise Exception("Error creating task")


async def update_job_task(data: JobTaskUpdate, task_id: str, user_id:str):
    try:
        result = task_service.update_task(task_id, data)

        keys = [
            f"user_task:{user_id}",
        ]

        for key in keys:
            await redis_manager.delete_value_sync(key)
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


def get_daily_tasks(user_id: str, filters: JobTaskFilterParams):
    try:
        results = task_service.get_daily_tasks(user_id=user_id, filters=filters)
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting daily tasks")


def get_overdue_tasks(user_id: str, filters: JobTaskFilterParams):
    try:
        results = task_service.get_overdue_tasks(user_id=user_id, filters=filters)
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting overdue tasks")


def get_upcoming_tasks(user_id: str, filters: JobTaskFilterParams):
    try:
        results = task_service.get_upcoming_tasks(user_id=user_id, days=3, filters=filters)
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting upcoming tasks")


async def delete_task(task_id: str, db: Session):
    try:
        db_task = db.query(JobTask).filter(JobTask.id == task_id).first()
        if db_task is None:
            raise Exception("Task not found")
        db.delete(db_task)
        db.commit()

        keys = [
            f"user_task:{db_task.user_id}",
        ]

        for key in keys:
             await redis_manager.delete_value(key)
        return {
            "success": True,
            "message": "Task deleted successfully"
        }
    except Exception as e:
        logger.error(e)
        raise Exception("Error deleting task")


async  def snooze_job_task(data: JobTaskSnooze, task_id: str, user_id: str):
    try:
        result = task_service.snooze_task(task_id, data.period, TaskCreator.MANUAL)
        keys = [
            f"user_task:{user_id}",
        ]

        for key in keys:
           await redis_manager.delete_value(key)
        return result
    except Exception as e:
        logger.error(e)
        raise Exception("Error Snoozing task")


async def complete_job_task(task_id: str, user_id:str):
    try:
        result = task_service.complete_task(task_id)

        keys = [
            f"user_task:{user_id}",
        ]

        for key in keys:
             await redis_manager.delete_value(key)
        return result
    except Exception as e:
        logger.error(e)
        raise Exception("Error Completing task")


def cancel_job_task(task_id: str):
    try:
        return task_service.cancel_task(task_id)
    except Exception as e:
        logger.error(e)
        raise Exception("Error Cancelling task")
