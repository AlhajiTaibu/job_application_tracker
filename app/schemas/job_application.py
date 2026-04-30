import uuid
from datetime import date, datetime, time
from typing import List, Generic, TypeVar, Optional, Literal

from fastapi.params import Query
from pydantic import BaseModel

from app.schemas.interview import InterviewDetailShort

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    payload: Optional[T] = None
    error: Optional[str] = None


class JobApplicationCreate(BaseModel):
    company_name: str
    job_url: str
    job_title: str
    description: str
    source: str
    notes: str


class JobApplicationUpdate(BaseModel):
    company_name: Optional[str] = None
    job_url: Optional[str] = None
    job_title: Optional[str] = None
    description: Optional[str] = None
    date_applied: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    contacts_id: Optional[str] = None


class JobApplicationStatusTransition(BaseModel):
    to_status: Literal["saved", "applied", "assessment", "screening", "interviewing", "offer", "accepted", "stale", "rejected", "withdrawn"]
    reason: str


class JobApplicationStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    available_status: List[str]
    previous_status: str
    message: str


class JobApplicationResponse(BaseModel):
    id: uuid.UUID
    contacts_id: Optional[uuid.UUID]
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_role: Optional[str] = None
    company_name: str
    job_url: str
    job_title: str
    description: Optional[str]
    status: str
    source: str
    notes: str
    interviews: Optional[list[InterviewDetailShort]]
    updated_at: datetime


class JobApplicationShortResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    job_title: str
    status: str
    description: Optional[str]
    contacts_id: Optional[uuid.UUID]
    source: str
    updated_at: datetime


class JobApplicationListResponse(BaseModel):
    data: List[JobApplicationShortResponse] = []
    next_cursor: Optional[str]


class JobFilterParams:
    def __init__(
            self,
            company_name: Optional[str] = None,
            status: Optional[str] = None,
            source: Optional[str] = None,
            start_date: Optional[date] = Query(None, description="Filter from this date (YYYY-MM-DD)"),
            end_date: Optional[date] = Query(None, description="Filter until this date (YYYY-MM-DD)"),
            q: Optional[str] = Query(None, min_length=3, description="Search term"),
            sort_by: str = Query("created_at", pattern="^(created_at|company_name|date_applied|updated_at)$"),
            order: str = Query("desc", pattern="^(asc|desc)$")
    ):
        self.company_name = company_name
        self.status = status
        self.source = source
        self.start_date = start_date
        self.end_date = end_date
        self.sort_by = sort_by
        self.order = order
        self.q = q

