import uuid
from datetime import datetime
from typing import Literal, Optional, List

from pydantic import BaseModel


class JobTaskCreate(BaseModel):
    job_application_id: uuid.UUID
    name: str
    status: Literal["pending", "done", "snoozed"]
    due_date: str


class JobTaskUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[Literal["pending", "done", "snoozed"]] = None
    due_date: Optional[str] = None


class JobTaskDetail(BaseModel):
    id: uuid.UUID
    job_application_id: uuid.UUID
    name: str
    status: Literal["pending", "done", "snoozed"]
    due_date: datetime
    is_overdue: bool


class JobTaskList(BaseModel):
    data: List[JobTaskDetail] = []