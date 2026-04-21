from fastapi import APIRouter
from app.api.v1.endpoints import auth, job_application, contacts, interview, job_task

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

api_router.include_router(
    contacts.router,
    prefix="/contacts",
    tags=["Contacts"]
)

api_router.include_router(
    interview.router,
    prefix="/interview",
    tags=["Interview"]
)

api_router.include_router(
    job_task.router,
    prefix="/task",
    tags=["Task"]
)
