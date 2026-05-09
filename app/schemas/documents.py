import uuid
from typing import Literal, Optional

from fastapi import Form
from pydantic import BaseModel


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
