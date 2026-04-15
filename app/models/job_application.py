from sqlalchemy import Column, Integer, String, DateTime, func, Boolean

from app.database import Base
from app.database import SessionLocal

metadata = Base.metadata


class JobApplication(Base):
    __tablename__ = "job_application"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    job_url = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    state = Column(String(255), nullable=False)
    date_applied = Column(DateTime, nullable=False)
    source = Column(String(255), nullable=False)
    notes = Column(String(255), nullable=False)
    is_archived = Column(Boolean, nullable=False, default=False)
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
