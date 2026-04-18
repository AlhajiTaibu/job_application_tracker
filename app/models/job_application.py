import uuid

from sqlalchemy import Column, String, DateTime, func, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql.base import UUID

from app.database import Base
from app.database import SessionLocal
from app.models.user import User

metadata = Base.metadata


class JobApplication(Base):
    __tablename__ = "job_application"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    user_id = Column(UUID, ForeignKey(User.id), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    job_url = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False)
    date_applied = Column(DateTime, nullable=False)
    source = Column(String(255), nullable=False)
    notes = Column(String(255), nullable=True)
    is_archived = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"Job: {self.company_name} - {self.job_title}"

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()


class JobApplicationStatusHistory(Base):
    __tablename__ = "job_application_status_history"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    job_application_id = Column(UUID, ForeignKey("job_application.id"), nullable=False, index=True)
    from_status = Column(String(255), nullable=False)
    to_status = Column(String(255), nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"Job Application: {self.job_application_id} status: {self.from_status} -> {self.to_status}"

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()
