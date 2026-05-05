from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.logging_config import logger
from app.crud import crud_reporting
from app.models.user import User

router = APIRouter()

@router.get("/application-funnel")
async def application_funnel(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    try:
        if not user:
            raise HTTPException(status_code=403, detail="Forbidden")
        return await crud_reporting.application_funnel(db=db, user_id=user.id)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/time-in-stage-analytics")
async def time_in_stage_analytics(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    try:
        if not user:
            raise HTTPException(status_code=403, detail="Forbidden")
        return await crud_reporting.time_in_stage_analytics(db=db, user_id=user.id)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/source-analytics")
async def source_analytics(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    try:
        if not user:
            raise HTTPException(status_code=403, detail="Forbidden")
        return await crud_reporting.source_analytics(db=db, user_id=user.id)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/role-analytics")
async def role_analytics(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    try:
        if not user:
            raise HTTPException(status_code=403, detail="Forbidden")
        return await crud_reporting.role_analytics(db=db, user_id=user.id)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=str(error))

