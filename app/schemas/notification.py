from datetime import datetime
import uuid
from typing import Optional

from pydantic import BaseModel



class NotificationRegister(BaseModel):
    token: str
    platform: str

class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

class NotificationResponseList(BaseModel):
    data: list[NotificationResponse]
