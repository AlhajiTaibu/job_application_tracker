import uuid
from enum import Enum

from sqlalchemy import Column, String, DateTime, func, Boolean, ForeignKey, Date, Time, Integer, Table, Index
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.database import SessionLocal
from app.models.user import User
from app.models.association import documents_association_table, association_table

metadata = Base.metadata


class JobApplication(Base):
    __tablename__ = "job_application"

    __table_args__ = (
        Index(
            "ix_job_application_company_name_trgm",
            "company_name",
            postgresql_using="gin",
            postgresql_ops={"company_name": "gin_trgm_ops"},
        ),
        Index(
            "ix_job_application_job_title_trgm",
            "job_title",
            postgresql_using="gin",
            postgresql_ops={"job_title": "gin_trgm_ops"},
        ),
    )
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    user_id = Column(UUID, ForeignKey(User.id), nullable=False, index=True)
    contacts = relationship("Contacts", secondary=association_table, back_populates="job_applications")
    documents = relationship("Documents", secondary=documents_association_table, back_populates="job_applications")
    company_name = Column(String(255), nullable=False, index=True)
    job_url = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False, index=True)
    description = Column(String)
    status = Column(String(255), nullable=False, index=True)
    date_applied = Column(DateTime)
    source = Column(String(255), nullable=False)
    notes = Column(String(255), nullable=True)
    is_archived = Column(Boolean, nullable=False, default=False, index=True)
    updated_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)

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
    transition_type = Column(String(20), default="system")
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

class JobApplicationStatusTransitionType(str, Enum):
    SYSTEM = "system"
    MANUAL = "manual"
    AUTO_SUGGESTED = "auto_suggested"


class Contacts(Base):
    __tablename__ = "contacts"

    __table_args__ = (
        Index(
            "ix_contacts_company_trgm",
            "company",
            postgresql_using="gin",
            postgresql_ops={"company": "gin_trgm_ops"},
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    user_id = Column(UUID, ForeignKey(User.id), nullable=False, index=True)
    job_applications = relationship("JobApplication", secondary=association_table, back_populates="contacts")
    name = Column(String(255), nullable=False, index=True)
    company = Column(String(50), index=True)
    relationship_type = Column(String(50))
    notes = relationship("NoteLog", back_populates="contact")
    email = Column(String(255))
    role = Column(String(15))
    linkedIn_url = Column(String)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now(), index=True)

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


class NoteLog(Base):
    __tablename__ = "note_log"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    contacts_id = Column(UUID, ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)
    contact = relationship("Contacts", back_populates="notes")
    notes = Column(String)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"Notes Log: {self.contacts_id} notes: {self.notes}"

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

    __table_args__ = (
        Index(
            "ix_interview_interviewer_name_trgm",
            "interviewer_name",
            postgresql_using="gin",
            postgresql_ops={"interviewer_name": "gin_trgm_ops"},
        ),
    )
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    job_application_id = Column(UUID, ForeignKey("job_application.id", ondelete="CASCADE"), nullable=False, index=True)
    format = Column(String(15), index=True)
    outcome = Column(String(30), index=True)
    date = Column(Date, index=True)
    time = Column(Time)
    notes = Column(String)
    round = Column(Integer)
    estimated_duration = Column(String(50))
    actual_duration = Column(String(50))
    timezone = Column(String(15))
    interviewer_name = Column(String(50), index=True)
    feedback = Column(String)
    link = Column(String)
    created_at = Column(DateTime, default=func.now(), index=True)

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
    job_application_id = Column(UUID, ForeignKey("job_application.id"))
    user_id = Column(UUID, ForeignKey(User.id))
    name = Column(String(255), nullable=False)
    description = Column(String)
    task_type = Column(String(50))
    created_by = Column(String(20))
    status = Column(String(10), default="pending", index=True)
    due_date = Column(DateTime, index=True)
    is_overdue = Column(Boolean, default=False, index=True)
    updated_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"JobTask: {self.id} name: {self.name}"

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()


class TaskType(str, Enum):
    FOLLOW_UP = "follow_up"
    CONFIRM = "confirm"
    REMINDER = "reminder"
    THANK_YOU = "thank_you"
    REVIEW = "review"
    OTHER = "other"


class TaskCreator(str, Enum):
    MANUAL = "manual"
    SYSTEM = "system"
    AUTO_SUGGESTED = "auto_suggested"


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SNOOZED = "snoozed"


class SnoozeJobTask(Base):
    __tablename__ = "snoozed_job_task"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    task_id = Column(UUID, ForeignKey("job_task.id"))
    snoozed_count = Column(Integer, default=0)
    next_due_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()
