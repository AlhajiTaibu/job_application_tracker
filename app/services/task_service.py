from datetime import datetime
from typing import Dict, Any

from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.job_application import JobTask, TaskType, TaskCreator


class TaskService:
    def __init__(self):
        try:
            self.db = SessionLocal()
        finally:
            self.db.close()

    def create_task(self, name: str, description: str, task_type: TaskType, created_by: TaskCreator, due_date: str = None,
                    meta_data: Dict[str, Any] = None):
        try:
            task = JobTask(
                name=name,
                description=description,
                task_type=task_type,
                created_by=created_by
            )
            if due_date:
                task.due_date = datetime.strptime(due_date, "%d/%m/%Y")
            if meta_data:
                if "user_id" in meta_data:
                    task.user_id = meta_data["user_id"]
                if "job_application_id" in meta_data:
                    task.job_application_id = meta_data["job_application_id"]
            task.save_to_db()
            return {
                "success": True,
                "id": task.id,
                "message": "Task created successfully"
            }
        except Exception as error:
            logger.error(error)
            raise Exception("Error creating task")

    def update_task(self, task_id: str, data: Dict[str, Any]):
        try:
            task = self.db.query(JobTask).filter(JobTask.id == task_id).first()
            if not task:
                raise Exception("Task not found")
            task.name = data["name"] if "name" in data else task.name
            task.description = data["description"] if "description" in data else task.description
            task.due_date = datetime.strptime(data["due_date"], "%d/%m/%Y") if "due_date" in data else task.due_date
            task.task_type = data["task_type"] if "task_type" in data else task.task_type
            task.status = data["status"] if "status" in data else task.status
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


task_service = TaskService()
