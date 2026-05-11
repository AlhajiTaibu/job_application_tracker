import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import Form
from pydantic import BaseModel
from fastapi.params import Query


class DocumentsUpload(BaseModel):
    purpose: Literal["cv", "cover letter", "portfolio", "offer letter", "references", "other"]
    is_base: Optional[bool] = False
    name: Optional[str] = None
    is_draft: Optional[bool] = False

    @classmethod
    def as_form(cls, request_data: str = Form(...)):
        return cls.model_validate_json(request_data)

class DocumentsLinkJobApplication(BaseModel):
    job_application_id: uuid.UUID


class DocumentFilterParams:
    def __init__(
            self,
            company_name: Optional[str] = None,
            purpose: Optional[str] = None,
            q: Optional[str] = Query(None, min_length=3, description="Search term"),
            sort_by: str = Query("created_at", pattern="^(created_at)$"),
            order: str = Query("asc", pattern="^(asc|desc)$")
    ):
        self.company_name = company_name
        self.purpose = purpose
        self.sort_by = sort_by
        self.order = order
        self.q = q

class DocumentsResponse(BaseModel):
    id: uuid.UUID
    name: str
    file_type: str
    purpose: str
    is_base: bool
    is_draft: bool
    created_at: datetime

class DocumentsListResponse(BaseModel):
    data: list[DocumentsResponse]


class DocumentsShortResponse(BaseModel):
    id: uuid.UUID
    name: str
    purpose: str


class DocumentUpdate(BaseModel):
    is_submitted: Optional[bool] = False
    name: Optional[str] = None
    is_draft: Optional[bool] = False
