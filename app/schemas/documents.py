import uuid
from typing import Literal

from fastapi import Form
from pydantic import BaseModel


class DocumentsUpload(BaseModel):
    job_application_id: uuid.UUID
    purpose: Literal["cv", "cover letter", "portfolio"]

    @classmethod
    def as_form(cls, request_data: str = Form(...)):
        return cls.model_validate_json(request_data)
