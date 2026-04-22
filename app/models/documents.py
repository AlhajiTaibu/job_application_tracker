import uuid

from sqlalchemy import Column, String, Integer, DateTime, Boolean, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.database import SessionLocal
from app.models.job_application import JobApplication
from app.services.storage_service import storage_service

metadata = Base.metadata


class Documents(Base):
    __tablename__ = "document_upload"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    job_application_id = Column(UUID, ForeignKey(JobApplication.id), nullable=False, index=True)
    filename = Column(String)
    file_key = Column(UUID, nullable=False, index=True)
    file_type = Column(String(20))
    purpose = Column(String(20))
    version_name = Column(String(255))
    is_latest = Column(Boolean)
    upload_date = Column(DateTime)
    size = Column(Integer)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"File:{self.filename} purpose:{self.purpose}"

    def get_url(self):
        return storage_service.get_signed_url("resumes", f"{self.file_key}.{self.file_type}", 720)

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()