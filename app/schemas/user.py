from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str


class ConfirmEmail(BaseModel):
    token: str
    email: str


class ResendOTP(BaseModel):
    email: str


class RefreshToken(BaseModel):
    refresh_token: str


class ResetPassword(BaseModel):
    email: str
    password: str
