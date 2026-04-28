from typing import Annotated

from fastapi import HTTPException, UploadFile, File
from fastapi.params import Depends
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.logging_config import logger
from app.crud import crud_profile
from app.models.user import User
from app.schemas.job_application import ApiResponse
from app.schemas.profile import ProfileUpdate, ProfileResponse

router = APIRouter()


@router.post("/update")
async def profile(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        request_data: ProfileUpdate
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_profile.update_profile(data=request_data, user_id=user.id, db=db)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail="Error updating profile")


@router.get("", response_model=ApiResponse[ProfileResponse])
async def profile(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)]
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_profile.get_profile(user_id=user.id, db=db)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail="Error retrieving profile")


@router.post("/upload-avatar")
async def profile(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        file: UploadFile = File(...)
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return await crud_profile.upload_profile_avatar(user_id=user.id, db=db, file=file)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=str(error))