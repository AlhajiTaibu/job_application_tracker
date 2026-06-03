import uuid
from datetime import datetime
from typing import Literal, Optional, List
from fastapi.params import Query

from pydantic import BaseModel


class JobTaskCreate(BaseModel):
    job_application_id: Optional[uuid.UUID]
    name: str
    task_type: Literal["follow_up", "confirm", "reminder", "thank_you", "review", "other"]
    due_date: str


class JobTaskUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[Literal["pending", "completed", "snoozed", "cancelled"]] = None
    task_type: Optional[Literal["follow_up", "confirm", "reminder", "thank_you", "review", "other"]] = None
    due_date: Optional[str] = None


class JobTaskDetail(BaseModel):
    id: uuid.UUID
    job_application_id: Optional[uuid.UUID]
    name: str
    status: Literal["pending", "completed", "snoozed", "cancelled"]
    task_type: Literal["follow_up", "confirm", "reminder", "thank_you", "review", "other"]
    due_date: Optional[datetime]
    is_overdue: bool
    created_at: datetime
    updated_at: Optional[datetime]


class JobTaskList(BaseModel):
    data: List[JobTaskDetail] = []


class JobTaskSnooze(BaseModel):
    period: int

class JobTaskFilterParams:
    def __init__(
            self,
            status: Optional[str] = None,
            task_type: Optional[str] = None,
            q: Optional[str] = Query(None, min_length=3, description="Search term"),
            sort_by: str = Query("created_at", pattern="^(created_at|status|task_type|updated_at)$"),
            order: str = Query("desc", pattern="^(asc|desc)$")
    ):
        self.task_type = task_type
        self.status = status
        self.sort_by = sort_by
        self.order = order
        self.q = q