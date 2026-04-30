import uuid

from sqlalchemy import Column, UUID, ForeignKey, func, String, DateTime

from app.database import Base, SessionLocal
from app.models.user import User

metadata = Base.metadata

class NotificationToken(Base):
    __tablename__ = "notification_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    user_id = Column(UUID, ForeignKey(User.id), nullable=False, index=True)
    token = Column(String(255), nullable=False)
    device_type = Column(String(15), nullable=False)  # mobile, web
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"Notification Token: {self.token}"

    def save_to_db(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
        finally:
            db.close()
