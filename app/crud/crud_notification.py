from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.notification import NotificationToken
from app.schemas.notification import NotificationRegister


def register_device(user_id: str, data: NotificationRegister, db: Session):
    try:
        existing_token = db.query(NotificationToken).filter(NotificationToken.token == data.token).first()
        if existing_token:
            existing_token.user_id = user_id
            db.commit()
            return {"success":True, "status": "Token updated"}
        new_token = NotificationToken(user_id=user_id, token=data.token, device_type=data.platform)
        db.add(new_token)
        db.commit()
        return {"success": True, "status": "Token saved"}
    except Exception as e:
        logger.error(e)
        raise Exception("Error registering device")


def retrieve_user_tokens(user_id: str, db: Session):
    try:
        tokens = db.query(NotificationToken).filter(NotificationToken.user_id == user_id).all()
        return [token.token for token in tokens]
    except Exception as e:
        logger.error(e)
        raise Exception("Error retrieving tokens")
