from fastapi import APIRouter
from app.api.v1.endpoints import auth, job_application

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    job_application.router,
    prefix="/job_application",
    tags=["Job Application"]
)