import uuid

from sqlalchemy import Column, String, Integer, DateTime, Boolean, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.database import SessionLocal
from app.models.association import documents_association_table
from app.models.user import User
from app.services.storage_service import storage_service

metadata = Base.metadata


class Documents(Base):
    __tablename__ = "documents"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    job_applications = relationship("JobApplication", secondary=documents_association_table, back_populates="documents")
    user_id = Column(UUID, ForeignKey(User.id), nullable=False, index=True)
    name = Column(String(255))
    filename = Column(String)
    file_key = Column(UUID, nullable=True, index=True)
    file_type = Column(String(20))
    purpose = Column(String(20))
    version_name = Column(String(255))
    is_submitted = Column(Boolean)
    upload_date = Column(DateTime)
    size = Column(Integer)
    is_archived = Column(Boolean, default=False)
    is_base = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)
    status = Column(String(20), default="pending")
    error = Column(String)
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