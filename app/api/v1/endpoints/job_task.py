from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.logging_config import logger
from app.crud import crud_job_task
from app.models.user import User
from app.schemas.job_application import ApiResponse
from app.schemas.job_task import JobTaskCreate, JobTaskUpdate, JobTaskDetail, JobTaskList

router = APIRouter()


@router.post("/create")
async def task(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        request_data: JobTaskCreate
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_task.create_job_task(data=request_data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update/{task_id}")
async def task(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        task_id: str,
        request_data: JobTaskUpdate
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_task.update_job_task(data=request_data, db=db, job_task_id=task_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get/{task_id}", response_model=ApiResponse[JobTaskDetail])
async def task(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        task_id: str
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_task.get_task_by_id(task_id=task_id, db=db)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/list/{job_id}", response_model=ApiResponse[JobTaskList])
async def task(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        job_id: str,
        limit: int = 20,
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_task.get_tasks(job_id=job_id, db=db, limit=limit)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=str(error))


@router.delete("/delete/{task_id}")
async def task(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        task_id: str
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_job_task.delete_task(task_id=task_id, db=db)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
