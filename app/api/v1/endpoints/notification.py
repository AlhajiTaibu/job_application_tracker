from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.logging_config import logger
from app.crud import crud_notification
from app.models.user import User
from app.schemas.notification import NotificationRegister

router = APIRouter()


@router.post("/register-device")
async def register_device(
        data: NotificationRegister,
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)]):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_notification.register_device(data=data, db=db, user_id=user.id)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
