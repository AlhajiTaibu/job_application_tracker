from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.job_application import JobTask, JobApplication
from app.schemas.job_application import ApiResponse
from app.schemas.job_task import JobTaskCreate, JobTaskUpdate
from datetime import datetime


def create_job_task(data: JobTaskCreate, db:Session):
    try:
        db_job = db.query(JobApplication).filter(JobApplication.id == data.job_application_id).first()
        if not db_job:
            raise HTTPException(status_code=404, detail="Job application not found")
        job_task_instance = JobTask(
            name=data.name,
            job_application_id=data.job_application_id,
            status=data.status,
            due_date=datetime.strptime(data.due_date, "%d/%m/%Y")
        )
        job_task_instance.save_to_db()
        return {
            "success": True,
            "message": "Task created successfully",
            "data": {
                "id" : job_task_instance.id,
                "name": job_task_instance.name
            }
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error creating task")


def update_job_task(data: JobTaskUpdate, job_task_id: str, db: Session):
    try:
        db_task = db.query(JobTask).filter(JobTask.id == job_task_id).first()
        if db_task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        db_task.name = data.name if data.name else db_task.name
        db_task.status = data.status if data.status else db_task.status
        db_task.due_date = datetime.strptime(data.due_date, "%d/%m/%Y") if data.due_date else db_task.due_date
        db.commit()
        db.refresh(db_task)
        return {
            "success": True,
            "message": "Task updated successfully",
            "data": {
            "id": db_task.id,
            "name": db_task.name
        }
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error updating task")


def get_task_by_id(task_id: str, db: Session):
    try:
        db_task = db.query(JobTask).filter(JobTask.id == task_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")
        return ApiResponse(success=True, payload=db_task)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error getting task")


def get_tasks(job_id: str, db: Session, limit: int):
    try:
        db_task = db.query(JobTask).filter(JobTask.job_application_id == job_id).limit(limit).all()
        results = db_task if db_task else []
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error getting task")


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
        raise HTTPException(status_code=404, detail="Error deleting task")