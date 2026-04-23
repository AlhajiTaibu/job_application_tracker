import uuid
from typing import Optional, Literal, List

from pydantic import BaseModel


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