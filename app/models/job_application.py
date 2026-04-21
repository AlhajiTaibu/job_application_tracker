import uuid

from sqlalchemy import Column, String, DateTime, func, Boolean, ForeignKey, Date, Time, Integer
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
    contacts_id = Column(UUID, ForeignKey("contacts.id", ondelete="SET NULL"), default="")
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

class Contacts(Base):
    __tablename__ = "contacts"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    user_id = Column(UUID, ForeignKey(User.id), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(15), nullable=False)
    linkedIn_url = Column(String)
    notes = Column(String)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"Contacts: {self.name} email: {self.email} -> {self.role}"

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()


class Interview(Base):
    __tablename__ = "interview"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    job_application_id = Column(UUID, ForeignKey("job_application.id", ondelete="CASCADE"), nullable=False, index=True)
    format = Column(String(15))
    outcome = Column(String(30))
    date = Column(Date)
    time = Column(Time)
    notes = Column(String)
    round = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"Interview: {self.job_application_id} date: {self.date} time: {self.time}"

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()


class JobTask(Base):
    __tablename__ = "job_task"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    job_application_id = Column(UUID, ForeignKey("job_application.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255))
    status = Column(String(10), default="pending")
    due_date = Column(DateTime)
    is_overdue = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"JobTask: {self.job_application_id} name: {self.name} time: {self.time}"

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()