from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from typing_extensions import Annotated

from app.api.deps import get_current_user, get_db
from app.core.logging_config import logger
from app.crud import crud_job_application
from app.models.user import User
from app.schemas.job_application import JobApplicationResponse, JobApplicationListResponse, JobApplicationCreate, \
    JobApplicationUpdate, ApiResponse, JobFilterParams

router = APIRouter()


@router.post("/create")
async def job_application(
        user: Annotated[User, Depends(get_current_user)],
        request_data: JobApplicationCreate):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_application.create_job_application(data=request_data, user=user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update/{job_id}")
async def job_application(
        user: Annotated[User, Depends(get_current_user)],
        request_data: JobApplicationUpdate,
        job_id: str,
        db: Session = Depends(get_db)):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_application.update_job_application(data=request_data, db=db, job_id=job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete/{job_id}")
async def job_application(
        user: Annotated[User, Depends(get_current_user)],
        job_id: str,
        db: Session = Depends(get_db)):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_application.delete_job_application(job_id=job_id, user=user, db=db)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/get/{job_id}", response_model=ApiResponse[JobApplicationResponse])
async def job_application(
        user: Annotated[User, Depends(get_current_user)],
        job_id: str,
        db: Session = Depends(get_db)):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_application.get_job_application_by_id(job_id=job_id, user=user, db=db)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/list", response_model=ApiResponse[JobApplicationListResponse])
async def job_application_list(
        user: Annotated[User, Depends(get_current_user)],
        cursor: Optional[str] = None,
        limit: int = 20,
        filters: JobFilterParams = Depends(),
        db: Session = Depends(get_db)
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_application.get_job_applications(user=user, db=db, filters=filters, limit=limit, cursor=cursor)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=str(error))
