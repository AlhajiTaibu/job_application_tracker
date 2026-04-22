from markupsafe import Markup
from sqladmin import ModelView, Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import settings
from app.models.documents import Documents
from app.models.job_application import JobApplication, Contacts, Interview
from app.models.user import User
from sqladmin.filters import BooleanFilter, StaticValuesFilter, AllUniqueStringValuesFilter


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")

        # Use your existing logic or a simple hardcoded admin for now
        if username == "admin" and password == "your-secure-password":
            request.session.update({"token": "authenticated"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session


authentication_backend = AdminAuth(secret_key=settings.secret_key)


class UserAdmin(ModelView, model=User):
    can_delete = False
    column_list = ["id", "email", "is_verified", "created_at"]
    column_filters = [
        BooleanFilter(column=User.is_verified),
    ]
    column_searchable_list = ["email"]
    column_details_exclude_list = ["hashed_password"]
    icon = "fa-solid fa-person"


class JobApplicationAdmin(ModelView, model=JobApplication):
    can_delete = False
    column_list = ["id", "company_name", "job_title", "status", "source"]
    column_searchable_list = ["company_name", "job_title"]
    column_filters = [
        StaticValuesFilter(
            column=JobApplication.status,
            values=[("saved", "Saved"), ("applied", "Applied"), ("screening", "Screening"),
                    ("interviewing", "Interviewing"), ("offer", "Offer"), ("accepted", "Accepted"),
                    ("rejected", "Rejected"), ("withdrawn", "Withdrawn")]
        ),
        AllUniqueStringValuesFilter(column=JobApplication.source)
    ]
    icon = "fa-solid fa-briefcase"


class ContactsAdmin(ModelView, model=Contacts):
    can_delete = False
    name_plural = "Contacts"
    column_list = ["id", "name", "email", ]
    column_searchable_list = ["name", "email"]
    column_filters = [
        StaticValuesFilter(
            column=Contacts.role,
            values=[("recruiter", "Recruiter"), ("employee", "Employee"), ("hiring manager", "Hiring Manager"),
                    ("referral", "Referral")]
        )
    ]
    icon = "fa-solid fa-phone"


class InterviewAdmin(ModelView, model=Interview):
    can_delete = False
    column_list = ["id", "format", "round", "date", "time", "outcome"]
    column_filters = [
        StaticValuesFilter(
            column=Interview.format,
            values=[("phone", "Phone"), ("video", "Video"), ("onsite", "Onsite"), ("technical", "Technical"),
                    ("panel", "Panel")]
        )
    ]
    icon = "fa-solid fa-message"


class DocumentAdmin(ModelView, model=Documents):
    can_delete = False
    name_plural = "Documents"
    icon = "fa-solid fa-file-pdf"
    column_list = ["id", "filename", "file_type", "purpose", "preview_link"]
    column_details_exclude_list = ["file_key"]
    column_filters = [
        StaticValuesFilter(
            column=Documents.purpose,
            values=[("cv", "CV"), ("cover letter", "Cover Letter"), ("portfolio", "Portfolio")]
        )
    ]
    column_formatters = {
        "preview_link": lambda m, a: Markup(
            f'<a href="{m.get_url()}" target="_blank">'
            f'  <i class="fa-solid fa-eye"></i> View PDF'
            f'</a>'
        )
    }


class AdminRegistration:
    def __init__(self, admin: Admin):
        admin.add_view(UserAdmin)
        admin.add_view(JobApplicationAdmin)
        admin.add_view(ContactsAdmin)
        admin.add_view(InterviewAdmin)
        admin.add_view(DocumentAdmin)
