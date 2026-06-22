from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.logging_config import logger
from app.crud import crud_notification
from app.models.user import User
from app.schemas.job_application import ApiResponse
from app.schemas.notification import NotificationRegister, NotificationResponseList

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


@router.get("/notifications", response_model=ApiResponse[NotificationResponseList])
async def notifications(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)]):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_notification.retrieve_user_notifications(user_id=user.id, db=db)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/mark-as-read/{notification_id}")
async def mark_as_read(
        notification_id: str,
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)]):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_notification.mark_as_read(notification_id=notification_id, db=db)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/mark-all-as-read")
async def mark_all_as_read(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)]):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_notification.mark_all_as_read(user_id=user.id, db=db)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(
        notification_id: str,
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)]):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_notification.delete_notification(notification_id=notification_id, db=db)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))