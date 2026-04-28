import uuid
from typing import Optional, Literal

from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    notification_type: Optional[Literal["email", "push"]] = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    title: Optional[str]
    notification_type: Literal["email", "push"]
    avatar_url: Optional[str]
