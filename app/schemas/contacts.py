import uuid
from datetime import datetime
from typing import Optional, Literal, List
from fastapi.params import Query
from pydantic import BaseModel


class ContactsCreate(BaseModel):
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    relationship_type: Literal["recruiter", "employee", "hiring manager", "referral"]
    role: Optional[str] = None
    linkedIn_url: Optional[str] = None
    notes: Optional[str] = None


class ContactsUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    relationship_type: Optional[Literal["recruiter", "employee", "hiring manager", "referral"]] = None
    role: Optional[str] = None
    linkedIn_url: Optional[str] = None
    notes: Optional[str] = None


class JobApplicationResponseTruncated(BaseModel):
    id: uuid.UUID
    company_name: str
    job_title: str
    status: str


class ContactsDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: Optional[str]
    company: Optional[str]
    relationship_type: Optional[str]
    role: Optional[str]
    linkedIn_url: Optional[str]
    notes: Optional[List[NoteLog]]
    job_applications: Optional[List[JobApplicationResponseTruncated]]


class ContactsListResponse(BaseModel):
    data: List[ContactsDetailResponse] = []


class ContactsLinkJobApplication(BaseModel):
    job_application_id: uuid.UUID


class ContactsFilterParams:
    def __init__(
            self,
            q: Optional[str] = Query(None, min_length=3, description="Search term"),
            # sort_by: str = Query("created_at"),
            order: str = Query("desc", pattern="^(asc|desc)$")
    ):
        # self.sort_by = sort_by
        self.order = order
        self.q = q


class NoteLog(BaseModel):
    id: uuid.UUID
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
