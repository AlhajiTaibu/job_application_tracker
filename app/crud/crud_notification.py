from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.notification import NotificationToken
from app.schemas.notification import NotificationRegister


def register_device(user_id: str, data: NotificationRegister, db: Session):
    try:
        existing_token = db.query(NotificationToken).filter(NotificationToken.token == data.token).first()
        if existing_token:
            # Update the existing token's user_id if needed
            existing_token.user_id = user_id
            db.commit()
            return {"success":True, "status": "Token updated"}
        new_token = NotificationToken(user_id=user_id, token=data.token, device_type=data.platform)
        db.add(new_token)
        db.commit()
        return {"success": True, "status": "Token saved"}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail="Error registering device")
