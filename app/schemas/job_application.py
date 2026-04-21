import uuid
from datetime import date, datetime, time
from typing import List, Generic, TypeVar, Optional, Literal

from fastapi.params import Query
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    payload: Optional[T] = None
    error: Optional[str] = None


class JobApplicationCreate(BaseModel):
    company_name: str
    job_url: str
    job_title: str
    source: str
    notes: str


class JobApplicationUpdate(BaseModel):
    company_name: Optional[str] = None
    job_url: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[
        Literal["saved", "applied", "screening", "interviewing", "offer", "accepted", "rejected", "withdrawn"]] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    contacts_id: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: uuid.UUID
    contacts_id: Optional[uuid.UUID]
    company_name: str
    job_url: str
    job_title: str
    status: str
    source: str
    notes: str
    updated_at: datetime


class JobApplicationListResponse(BaseModel):
    data: List[JobApplicationResponse] = []
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


class ContactsCreate(BaseModel):
    name: str
    email: Optional[str] = None
    role: Literal["recruiter","employee","hiring manager","referral"]
    linkedIn_url: Optional[str] = None
    notes: Optional[str] = None


class ContactsUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Literal["recruiter","employee","hiring manager","referral"]] = None
    linkedIn_url: Optional[str] = None
    notes: Optional[str] = None


class ContactsDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    linkedIn_url: str
    notes: str


class ContactsListResponse(BaseModel):
    data: List[ContactsDetailResponse] = []


class ContactsLinkJobApplication(BaseModel):
    job_application_id: uuid.UUID


class InterviewCreate(BaseModel):
    job_application_id: uuid.UUID
    format: Literal["phone", "video", "onsite", "technical", "panel"]
    date: str
    time: str
    round: int


class InterviewUpdate(BaseModel):
    format: Optional[Literal["phone", "video", "onsite", "technical", "panel"]]
    date: Optional[str]
    time: Optional[str]
    round: Optional[int]
    what_went_well: Optional[str]
    what_was_discussed: Optional[str]


class InterviewDetail(BaseModel):
    id: uuid.UUID
    format: Optional[Literal["phone", "video", "onsite", "technical", "panel"]]
    date: Optional[date]
    time: Optional[time]
    round: Optional[int]
    notes: Optional[str]


class InterviewList(BaseModel):
    data: List[InterviewDetail] = []


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
