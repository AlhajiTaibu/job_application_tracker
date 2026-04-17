import uuid
from datetime import date
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
        Literal["saved", "applied", "screening", "interview", "offer", "accepted", "rejected", "withdrawn"]] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    job_url: str
    job_title: str
    status: str
    source: str
    notes: str


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
