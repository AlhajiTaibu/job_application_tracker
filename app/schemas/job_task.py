import uuid
from datetime import datetime
from typing import Literal, Optional, List

from pydantic import BaseModel

from app.models.job_application import TaskType


class JobTaskCreate(BaseModel):
    job_application_id: Optional[uuid.UUID]
    name: str
    task_type: TaskType
    due_date: str


class JobTaskUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[Literal["pending", "completed", "snoozed", "cancelled"]] = None
    due_date: Optional[str] = None


class JobTaskDetail(BaseModel):
    id: uuid.UUID
    job_application_id: Optional[uuid.UUID]
    name: str
    status: Literal["pending", "completed", "snoozed", "cancelled"]
    due_date: datetime
    is_overdue: bool


class JobTaskList(BaseModel):
    data: List[JobTaskDetail] = []


class JobTaskSnooze(BaseModel):
    period: int