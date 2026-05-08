from fastapi import APIRouter
from app.api.v1.endpoints import auth, job_application, contacts, interview, job_task, documents, notification, profile, \
    reporting

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    profile.router,
    prefix="/profile",
    tags=["Profile"]
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

api_router.include_router(
    documents.router,
    prefix="/document",
    tags=["Document"]
)

api_router.include_router(
    notification.router,
    prefix="/notification",
    tags=["Notification"]
)

api_router.include_router(
    reporting.router,
    prefix="/reports",
    tags=["Reports"]
)
