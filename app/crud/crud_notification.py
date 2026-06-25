from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.notification import NotificationToken, Notifications
from app.schemas.job_application import ApiResponse
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

def save_notification(user_id: str, data):
    try:
        new_notification = Notifications(
            user_id =user_id,
            title=data['title'],
            message=data['message']
        )
        new_notification.save_to_db()
    except Exception as e:
        logger.error(e)
        raise Exception("Error saving notification")

def retrieve_user_notifications(user_id: str, db: Session):
    try:
        notifications = db.query(Notifications).filter(Notifications.user_id == user_id).order_by(Notifications.created_at.desc()).all()
        return ApiResponse(success=True, payload={"data": notifications})
    except Exception as e:
        logger.error(e)
        raise Exception("Error retrieving notifications")

def mark_as_read(notification_id: str, db: Session):
    try:
        notification = db.query(Notifications).filter(Notifications.id == notification_id).first()
        if not notification:
            raise Exception("Notification not found")
        notification.is_read = True
        db.commit()
        return {"success": True, "message": "Notification marked as read"}
    except Exception as e:
        logger.error(e)
        raise Exception("Error marking notification as read")

def mark_all_as_read(user_id: str, db: Session):
    try:
        db.query(Notifications).filter(Notifications.user_id == user_id).update({Notifications.is_read: True})
        db.commit()
        return {"success": True, "message": "All notifications marked as read"}
    except Exception as e:
        logger.error(e)
        raise Exception("Error marking notifications as read")

def delete_notification(notification_id: str, db: Session):
    try:
        notification = db.query(Notifications).filter(Notifications.id == notification_id).first()
        if not notification:
            raise Exception("Notification not found")
        db.delete(notification)
        db.commit()
        return {"success": True, "message": "Notification deleted"}
    except Exception as e:
        logger.error(e)
        raise Exception("Error deleting notification")


