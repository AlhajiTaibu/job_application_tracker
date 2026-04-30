from pydantic import BaseModel


class NotificationRegister(BaseModel):
    token: str
    platform: str